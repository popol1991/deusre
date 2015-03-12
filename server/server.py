from flask import Flask
from flask import request, render_template, make_response
import requests
from werkzeug import SharedDataMiddleware
from es import ES
import wrapper
import json

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 20
FEDERATE_INDEX = "federate"
ELSEVIER_INDEX = "deusre"
FEDERATE_SIZE = 10
DB_LIST = ["NIF", "Dryad", "Harvard", "Pubmed", "Brain"]
WRAPPER_LIST = [getattr(wrapper, "".join([w, "Wrapper"]))() for w in DB_LIST]

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})
es = ES()

@app.route("/deusre/api/<path:path>")
def route(path):
    #: pass all request to elasticsearch server
    target = "http://compute-1-33:9200/" + path
    data = request.get_data()
    res = make_response(requests.get(target, data=data, params=request.args).content)
    return res

@app.route("/deusre/federate/item/<path:path>")
def item(path):
    """ Fetch federated item with id. """
    index, id = path.split(':')
    if index == 'federate':
        doc = es.search(index=FEDERATE_INDEX, docid=id)
        xml = doc['_source']['xml']
        type = "application/xml"
    else:
        doc = es.search(index=ELSEVIER_INDEX, docid=id)
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
    if 'query' not in request.args:
        return render_template('federate.html', hits=[])
    query = request.args['query']
    doc_id = 0
    es.delete_all(index=FEDERATE_INDEX)
    alldoclist = []
    for i in range(len(WRAPPER_LIST)):
        db = WRAPPER_LIST[i]
        dbname = DB_LIST[i]
        logger.info("Fetching results from {0}.".format(dbname))
        doclist = db.raw_search(query, size=FEDERATE_SIZE)
        alldoclist += [doc['source'] for doc in doclist]
        logger.info("{0} results returned".format(len(doclist)))
        for doc in doclist:
            es.index_tmp_doc(index=FEDERATE_INDEX, doc_id=doc_id, dbname=dbname, doc=doc)
            doc_id += 1
    es.refresh(index=FEDERATE_INDEX)
    res = es.search(index=FEDERATE_INDEX, body={'query':{'match':{'text':query}}, 'size':1000}, docid=None)
    elsevier_res = search_elsevier(dict(q=query))
    elsevier_hits = elsevier_res.hits_for_federate()
    hits = res['hits']['hits']
    for hit in hits:
        hit['_id'] = 'federate:'+hit['_id']
    hits = merge(hits, elsevier_hits)
    hits = [dict(name=hit['_source']['title'],id=hit['_id']) for hit in hits]
    return render_template('federate.html', hits=hits)

@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('search.html', hits=[], query="", params={})
    res = search_elsevier(params)
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

def search_elsevier(params):
    res = []
    size = DEFAULT_SIZE
    if 'size' in params:
        size = params['size']
    page = 0
    query = params['q']
    if len(query) == 0:
        text_response = es.match_all(page, size)
    else:
        logger.info("Search elasticsearch with query: {0}".format(query))
        text_response = es.text_search(query, page, size)
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
    initindex()
    app.run(host="0.0.0.0", port=8080, debug=True)
