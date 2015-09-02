import sys
import json
from es import ES
from es import ESResponse
from flask import Flask
from flask import request, render_template
from werkzeug import SharedDataMiddleware

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 10
ARXIV_INDEX = "test"

ARXIV_FIELDS = ["article-title", "caption", "row_header_field", "footnotes", "col_header_field", "keywords", "abstract"]

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})

es = None
config = json.load(open(sys.argv[1]))
es = ES(config['es_server'])

#@app.route("/deusre/federate/item/<path:path>")
#def item(path):
    #userid = request.cookies.get('userid')
    #""" Fetch federated item with id. """
    #pos, index, id = path.split(':')
    #if index == 'federate':
        #doc = es.search(index=FEDERATE_INDEX, docid=id)
        #url = doc['_source']['url']
        #logger.info("User {0} clicked result {1} with url {2}".format(userid, pos, url))
        #return redirect(url)
    #else:
        #doc = es.search(index=ELSEVIER_INDEX, docid=id)
        #logger.info("User {0} clicked result {1} with local id {2}".format(userid, pos, id))
        #xml = json.dumps(doc['_source'], indent=4, separators=(",<br>",":"))
        #type = "text/html"
    #template = render_template('item.xml', content=xml)
    #response = make_response(template)
    #response.headers["Content-Type"] = type
    #response.headers["Accept-Charset"] = "utf-8"
    #return response

@app.route("/deusre/arxiv/subjects.json")
def subjects():
    with open("./static/data/subjects.json") as fin:
        subject = "".join(fin.readlines())
    return subject

@app.route("/deusre/arxiv/submit")
@app.route("/deusre/arxiv/", methods=['GET', 'POST'])
def arxiv():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('arxiv.html', len=0, hits=[], query="", params={}, dataset="elsevier", pages=0, visible=0, page=0)
    domainlist = [params[key] for key in params if key.startswith('subdomain')]
    if len(domainlist) == 0 or domainlist[0] == 'all':
        if 'domain' in params:
            domainlist = [params['domain']]
        else:
            domainlist.append('all')
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
    res = es.search(ARXIV_INDEX, body=body)
    numRes = res['hits']['total']
    res = ESResponse(res)
    logger.info("Reranking...")
    res = res.rerank(params)
    logger.info("Rendering...")
    for hit in res:
        if len(hit['subdomains']) != 0:
            hit['subject'] = ", ".join(hit['subdomains'])
        else:
            hit['subject'] = ", ".join(hit['domains'])
    pages = (numRes + DEFAULT_SIZE) / DEFAULT_SIZE
    return render_template('arxiv.html', hits=res, len=len(res), params=params, dataset="arxiv", pages=pages, visible=min(pages, 5), page=page+1, resNum=numRes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
