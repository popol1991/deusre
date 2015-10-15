import sys
import urllib
import time
import datetime
import json
import cookies
import xml.etree.ElementTree as ET
from es import ES
from es import ESResponse
from flask import Flask
from flask import request, render_template, redirect, make_response
from werkzeug import SharedDataMiddleware

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 10
ARXIV_INDEX = "arxiv-new"
KEY_USERID = 'cmu.table.arxiv.userid'

ARXIV_API = 'http://export.arxiv.org/api/query?search_query=all:{0}&start={1}&max_results={2}'
ARXIV_XML_PREFIX = '{http://www.w3.org/2005/Atom}'
ARXIV_XML_ID = "".join([ARXIV_XML_PREFIX, "id"])
ARXIV_XML_TITLE = "".join([ARXIV_XML_PREFIX, "title"])
ARXIV_XML_AUTHOR = "".join([ARXIV_XML_PREFIX, "author"])
ARXIV_XML_NAME = "".join([ARXIV_XML_PREFIX, "name"])
ARXIV_XML_SUMMARY = "".join([ARXIV_XML_PREFIX, "summary"])

ARXIV_FIELDS = ["article-title", "caption", "row_header_field", "footnotes", "col_header_field", "keywords", "abstract"]

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})

es = None
config = json.load(open("config.json"))
es = ES(config['es_server'])

def getTimestamp():
    ts = time.time()
    stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return stamp

@app.route("/deusre/arxiv/subjects.json")
def subjects():
    with open("./static/data/subjects.json") as fin:
        subject = "".join(fin.readlines())
    return subject

@app.route("/deusre/arxiv/doc/<path:path>")
def route(path):
    userid, docid = path.split(":")
    logger.info("[{0}]\tUser from {1} with id {2} clicked doc with id {3}".format(getTimestamp(), request.remote_addr, userid, docid))
    return redirect("http://arxiv.org/abs/{0}".format(docid))

@app.route("/deusre/arxiv/submit")
@app.route("/deusre/arxiv/", methods=['GET', 'POST'])
def arxiv():
    userid = cookies.setUserId()
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('arxiv.html', len=0, hits=[], query="", params={}, dataset="elsevier", pages=0, visible=0, page=0, userid=userid)
    logger.info("[{0}]\t_QUERY: user={1} ip={2} query={3}".format(getTimestamp(), userid, request.remote_addr, json.dumps(params)))
    # get domain
    if 'domain' in params:
        domainlist = [params['domain']]
    else:
        domainlist.append('all')
    # get page
    if 'page' in params:
        page = int(params['page']) - 1
    else:
        page = 0

    if domainlist[0] == 'all':
        body = es.mk_text_body(params['q'], page, DEFAULT_SIZE, ARXIV_INDEX, highlight=True, fields=ARXIV_FIELDS)
    else:
        filter_query = es.mk_filter(domainlist)
        query = es.mk_text_body(params['q'], page, DEFAULT_SIZE, ARXIV_INDEX, highlight=False, fields=ARXIV_FIELDS)
        filtered = dict(query=query['query'], filter=filter_query)
        body = {
            "query" : {
                "filtered" : filtered
            },
            "from": page * DEFAULT_SIZE,
            "size": DEFAULT_SIZE
        }
    print body
    res = es.search(ARXIV_INDEX, body=body)
    numRes = res['hits']['total']
    res = ESResponse(res)
    logger.info("[{0}]\tReranking...".format(getTimestamp()))
    res = res.rerank(params)
    logger.info("[{0}]\tRendering...".format(getTimestamp()))
    for hit in res:
        hit['subject'] = ", ".join(hit['domains'])
    pages = (numRes + DEFAULT_SIZE) / DEFAULT_SIZE

    resNum = len(res)
    fullTextList = []
    if resNum == 0:
        # get arXiv full text result here
        url = ARXIV_API.format(params['q'], 0, DEFAULT_SIZE)
        data = urllib.urlopen(url).read()
        root = ET.fromstring(data)
        for entry in root.iter(ARXIV_XML_PREFIX + "entry"):
            link = entry.find(ARXIV_XML_ID).text
            title = entry.find(ARXIV_XML_TITLE).text.strip()
            author = entry.find(ARXIV_XML_AUTHOR)
            names = ", ".join([name.text for name in author.findall(ARXIV_XML_NAME)])
            summary = entry.find(ARXIV_XML_SUMMARY).text.strip()
            fullTextList.append(dict(link=link, title=title, author=names, summary=summary))

    print fullTextList
    template = render_template('arxiv.html', hits=res, len=resNum, params=params, dataset="arxiv", pages=pages, visible=min(pages, 5), page=page+1, resNum=numRes, userid=userid, fulltextlist=fullTextList)
    resp = make_response(template)
    resp.set_cookie(KEY_USERID, userid)
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=True)
