import base64
import os
import requests
import wrapper
import json
from es import ES
from flask import Flask
from flask import redirect, request, render_template, make_response
from werkzeug import SharedDataMiddleware
from logistic import Logistic
from render import render_neuroelectro

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 20
FEDERATE_INDEX = "federate"
ELSEVIER_INDEX = "deusre"
ARXIV_INDEX = "arxiv"
FEDERATE_SIZE = 10
DB_LIST = ["NIF", "Dryad", "Harvard", "Pubmed"]
WRAPPER_LIST = [getattr(wrapper, "".join([w, "Wrapper"]))() for w in DB_LIST]

WEIGHT = [0.22010851, 0.11594479, -0.00707995, -0.09021589, -0.04557491,  0.29571261]
BEST_WEIGHT = [
    [0, 0, 0, 0, 9, 3],
    [0, 2, 5, 5, 0, 0]
]

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})

es = None
logistic = Logistic(WEIGHT)

@app.route("/deusre/api/<path:path>")
def route(path):
    #: pass all request to elasticsearch server
    target = "http://compute-1-33:9200/" + path
    data = request.get_data()
    res = make_response(requests.get(target, data=data, params=request.args).content)
    return res

@app.route("/deusre/neuroelectro/")
def classify_search():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('neuro.html', hits=[], query="", qtype="")
    query = params['q']
    vector = es.get_feature_vector(query, 'neuroelectro')
    query_type = logistic.classify(vector)
    qtype = "Neuron" if query_type == 0 else "Property"
    weight = BEST_WEIGHT[query_type]
    res = es.search_neuroelectro(query, weight, 'neuroelectro')
    hits = [hit['_source'] for hit in res['hits']['hits']]
    hits = [render_neuroelectro(hit) for hit in hits]
    for i in range(len(hits)):
        hits[i]['id'] = i
    template = render_template('neuro.html', hits=hits, query=query, qtype=qtype)
    resp = make_response(template)
    return resp

@app.route("/deusre/federate/item/<path:path>")
def item(path):
    userid = request.cookies.get('userid')
    """ Fetch federated item with id. """
    pos, index, id = path.split(':')
    if index == 'federate':
        doc = es.search(index=FEDERATE_INDEX, docid=id)
        url = doc['_source']['url']
        logger.info("User {0} clicked result {1} with url {2}".format(userid, pos, url))
        return redirect(url)
    else:
        doc = es.search(index=ELSEVIER_INDEX, docid=id)
        logger.info("User {0} clicked result {1} with local id {2}".format(userid, pos, id))
        xml = json.dumps(doc['_source'], indent=4, separators=(",<br>",":"))
        type = "text/html"
    template = render_template('item.xml', content=xml)
    response = make_response(template)
    response.headers["Content-Type"] = type
    response.headers["Accept-Charset"] = "utf-8"
    return response

@app.route("/deusre/federate/")
def federate():
    #: federated search of different data repositories
    # set cookies
    if 'userid' not in request.cookies:
        userid = base64.b64encode(os.urandom(16))
        logger.info("New user. Set userid to " + userid)
    else:
        userid = request.cookies.get('userid')
        logger.info("User {0} logged in.".format(userid))
    # empty page
    if 'query' not in request.args:
        return render_template('federate.html', hits=[])
    # start to fetch result from repos
    query = request.args['query']
    logger.info("User: {0}, Query: {1}".format(userid, query))
    doc_id = 0
    es.delete_all(index=FEDERATE_INDEX)
    for i in range(len(WRAPPER_LIST)):
        db = WRAPPER_LIST[i]
        dbname = DB_LIST[i]
        logger.info("Fetching results from {0}.".format(dbname))
        doclist = db.raw_search(query, size=FEDERATE_SIZE)
        logger.info("{0} results returned".format(len(doclist)))
        for doc in doclist:
            es.index_tmp_doc(index=FEDERATE_INDEX, doc_id=doc_id, dbname=dbname, doc=doc)
            doc_id += 1
    es.refresh(index=FEDERATE_INDEX)
    res = es.search(index=FEDERATE_INDEX, body={'query':{'match':{'text':query}}, 'size':1000}, docid=None)
    elsevier_res = search_local(dict(q=query), ELSEVIER_INDEX)
    elsevier_hits = elsevier_res.hits_for_federate()
    hits = res['hits']['hits']
    for hit in hits:
        hit['_id'] = 'federate:'+hit['_id']
    hits = merge(hits, elsevier_hits)
    hits = [dict(name=hit['_source']['title'],id=hit['_id']) for hit in hits]
    # build result
    template = render_template('federate.html', hits=enumerate(hits))
    resp = make_response(template)
    resp.set_cookie('userid', userid)
    return resp

@app.route("/deusre/arxiv/")
def arxiv():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('arxiv.html', hits=[], query="", params={})
    res = search_local(params, ARXIV_INDEX)
    logger.info("Reranking...")
    res = res.rerank(params)
    logger.info("Rendering...")
    return render_template('arxiv.html', hits=res, len=len(res), params=params)

@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('search.html', hits=[], query="", params={})
    res = search_local(params, ELSEVIER_INDEX)
    logger.info("Reranking...")
    res = res.rerank(params)
    logger.info("Rendering...")
    return render_template('search.html', hits=res, len=len(res), params=params)

def merge(hits1, hits2):
    i = 0
    j = 0
    hits = []
    while (i < len(hits1) and j < len(hits2)):
        score1 = hits1[i]['_score']
        score2 = hits2[j]['_score']
        if (score1 > score2):
            hits.append(hits1[i])
            i += 1
        else:
            hits.append(hits2[j])
            j += 1
    if i < len(hits1):
        hits += hits1[i:]
    if j < len(hits2):
        hits += hits2[j:]
    return hits

def search_local(params, index):
    res = []
    size = DEFAULT_SIZE
    if 'size' in params:
        size = params['size']
    page = 0
    query = params['q']
    if len(query) == 0:
        text_response = es.match_all(page, size, index=index)
    else:
        logger.info("Search elasticsearch with query: {0}".format(query))
        text_response = es.text_search(query, page, size, index=index)
    return text_response
    page += 1
    return res

def initindex():
    logger.info('Initializing federated index.')
    existed = es.existed(index=FEDERATE_INDEX)
    if not existed:
        logger.info('Index not existed, creating new index.')
        es.create(index=FEDERATE_INDEX)
    else:
        logger.info('Index has already existed.')

if __name__ == "__main__":
    with open('config.txt') as fin:
        server = fin.readline().strip()
    es = ES(server)
    initindex()
    app.run(host="0.0.0.0", port=8080, debug=True)
