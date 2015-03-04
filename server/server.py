from flask import Flask
from flask import request, render_template, make_response
import requests
from werkzeug import SharedDataMiddleware
from es import ES
import wrapper

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 20
FEDERATE_INDEX = "federate"
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
    doc = es.search(index=FEDERATE_INDEX, docid=path)
    xml = doc['_source']['xml']
    template = render_template('item.xml', content = xml)
    response = make_response(template)
    response.headers["Content-Type"] = "application/xml"
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
    hits = res['hits']['hits']
    hits = [dict(name=hit['_source']['title'],id=hit['_id']) for hit in hits]
    return render_template('federate.html', hits=hits)

@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    res = []
    params = request.args
    if len(params) == 0:
        return render_template('search.html', hits=[], query="", params={})
    size = DEFAULT_SIZE
    if 'size' in params:
        size = params['size']
    page = 0
    query = params['q']
    if len(query) == 0:
        text_response = es.match_all(page, size)
    else:
        text_response = es.text_search(query, page, size)
    res += text_response.rerank(params)
    page += 1
    return render_template('search.html', hits=res, len=len(res), params=params)

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
