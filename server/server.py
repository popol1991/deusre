import sys
import base64
import os
import requests
import wrapper
import json
from subprocess import check_output
from es import ES
from es import ESResponse
from flask import Flask
from flask import redirect, request, render_template, make_response
from werkzeug import SharedDataMiddleware
from logistic import Logistic

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SIZE = 10
FEDERATE_INDEX = "federate"
ELSEVIER_INDEX = "deusre"
ARXIV_INDEX = "test"
NEURO_INDEX = "neuroelectro"
FEDERATE_SIZE = 10
DB_LIST = ["NIF", "Dryad", "Harvard", "Pubmed"]
WRAPPER_LIST = [getattr(wrapper, "".join([w, "Wrapper"]))() for w in DB_LIST]

ARXIV_FIELDS = ["article-title", "caption", "row_header_field", "footnotes", "col_header_field", "keywords"]

#: old best weight for different type of queries
#WEIGHT = [0.22010851, 0.11594479, -0.00707995, -0.09021589, -0.04557491,  0.29571261]
#BEST_WEIGHT = [
    #[0, 0, 0, 0, 9, 3],
    #[0, 2, 5, 5, 0, 0]
#]

WEIGHT = [0.22186689, 0.11555565, 0.01580477, -0.13478732, -0.087531, -0.02332883]
BEST_WEIGHT = [
    [5, 1, 1, 1, 1, 1], # neuron
    [1, 1, 2, 5, 5, 1]  # property
]

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})

es = None
logistic = Logistic(WEIGHT)
config = json.load(open(sys.argv[1]))
es = ES(config['es_server'])

@app.route('/')
def index():
    #: for test
    return "Hello World!"

@app.route("/deusre/api/<path:path>")
def route(path):
    #: pass all request to elasticsearch server
    target = "http://compute-1-10:9200/" + path
    data = request.get_data()
    res = make_response(requests.get(target, data=data, params=request.args).content)
    return res

@app.route("/deusre/neuroelectro/submit")
@app.route("/deusre/neuroelectro/")
def classify_search():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('neuro.html', hits=[], len=0, params={}, qtype="")
    query = params['q']
    vector = es.get_feature_vector(query, NEURO_INDEX)
    query_type = logistic.classify(vector)
    qtype = "Neuron" if query_type == 0 else "Property"
    weight = BEST_WEIGHT[query_type]
    res = es.search_with_weight(query, weight, NEURO_INDEX, size=DEFAULT_SIZE, type="cross_fields")
    res = ESResponse(res)
    #return render_template('search.html', hits=res, len=len(res), params=params)
    hits = res.rerank(params)
    for i in range(len(hits)):
        hits[i]['id'] = i
    template = render_template('neuro.html', hits=hits, len=len(hits), params=params, qtype=qtype)
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
    #res = search_local(params, ARXIV_INDEX)
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

@app.route("/deusre/search/submit")
@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    params = request.args
    if len(params) == 0:
        return render_template('search.html', hits=[], query="", params={}, dataset="elsevier")
    res = search_local(params, ELSEVIER_INDEX)
    logger.info("Reranking...")
    res = res.rerank(params)
    logger.info("Rendering...")
    return render_template('search.html', hits=res, len=len(res), params=params, dataset="elsevier")

@app.route("/deusre/search/mlt", methods=["GET"])
def mlt():
    params = request.args
    query = params['q']
    pathId = params['path'].split('.')
    path = ".".join(pathId[:-1])
    tid = pathId[-1]
    out = check_output(["java", "-cp", "/Users/Kyle/IdeaProjects/mlt/lib/table2query.jar:/Users/Kyle/IdeaProjects/mlt/lib/stanford-corenlp-full-2015-04-20/stanford-corenlp-3.5.2.jar:/Users/Kyle/IdeaProjects/mlt/lib/stanford-corenlp-full-2015-04-20/stanford-corenlp-3.5.2-models.jar:/Users/Kyle/IdeaProjects/mlt/lib/", "MoreLikeThis", query, path, tid])
    print out
    result = es.search_with_term_weight(out, ELSEVIER_INDEX, [1]*6, filter=[])
    result = result.rerank(params)
    return render_template('search.html', hits=result, len=len(result), params=params, dataset="elsevier")

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

initindex()

if __name__ == "__main__":
    #with open('config.txt') as fin:
        #server = fin.readline().strip()
    #es = ES(server)
    #initindex()
    app.run(host="0.0.0.0", port=8080, debug=True)
