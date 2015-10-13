import sys
sys.path.append("../server/")
import json
import random
import time
import copy
import popol
from es import ES
from elasticsearch import Elasticsearch
from learnweight import evaluate

FOLD = 2

INDEX = "arxiv-cs-expand"
#QUERY_FILE = "query.json"

QUERY_FILE = "./randomQuerySeg-CS/query_5.json"

if '-o' in sys.argv:
    OUTPUT = sys.argv[sys.argv.index('-o') + 1]
else:
    OUTPUT = 'result.tmp'

FIELDS = ['article-title', 'caption', "row_header_field", "footnotes", "col_header_field", "keywords"]
FIELD_NUM = len(FIELDS)
BEST_WEIGHT    = [[5, 1, 1, 1, 1, 1], # neuron
                 [1, 1, 2, 5, 5, 1],
                 [4, 3, 2, 0 ,1, 0]] # property

esService = ES('localhost')

def build_params(query):
    params = dict()
    for p in query:
        params[p['name']] = p['value']
    return params

def search(hits, LAMBDA, MU, weight):
    fout = open(OUTPUT, 'w')
    for idx in xrange(len(hits)):
        #judge = json.loads(hits[idx]['_source']['judge'])
        #qid = hits[idx]['qid']
        #query = judge['query']
        #params = build_params(query)

        qid = hits[idx]['qid']
        query = hits[idx]['query']
        topic = hits[idx]['topic']
        obj = hits[idx]['object']
        prop = hits[idx]['property']

        if '--script' in sys.argv:
            tokens = [t['token'] for t in es.indices.analyze(body=query, index=INDEX, field="caption")['tokens']]
            topicTokens = [] if len(topic) == 0 else [t['token'] for t in es.indices.analyze(body=topic, index=INDEX, field="caption")['tokens']]
            objTokens = [] if len(obj) == 0 else [t['token'] for t in es.indices.analyze(body=obj, index=INDEX, field="caption")['tokens']]
            body = {
                "query" : {
                    "bool": {
                        "should": [
                            {
                                "function_score": {
                                    "script_score" : {
                                        "params" : {
                                            "qid" : qid,
                                            "query": tokens,
                                            "topic": topicTokens,
                                            "object": objTokens,
                                            "property": [] if len(prop) == 0 else [t['token'] for t in es.indices.analyze(body=prop, index=INDEX, field="caption")['tokens']],
                                            "lambda": LAMBDA,
                                            "mu": MU,
                                            "topicWeight": [1,1,0,1,1,1,0],
                                            "objectWeight": [1,0,0,0,1,1,1],
                                            "propertyWeight": [0,0,1,0,0,0,0]
                                        },
                                        #"script": "multi_input_field"
                                        #"script": "term_centric_field"
                                        "script": "feature"
                                    }
                                }
                            }
                        ]
                    }
                },
                "size" : 100
            }
            #if len(objTokens) > 1:
                #phrase_body = {
                    #"multi_match": {
                        #"query": obj,
                        #"fields": ["article-title","caption","abstract","footnotes","citations"],
                        #"type": "phrase"
                    #}
                #}
                #body["query"]["bool"]["should"].append(phrase_body)
            rank = es.search(index=INDEX, doc_type="table", body=body)
        else:
            rank = esService.search_with_weight(query, BEST_WEIGHT[1], INDEX, size=50, type="cross_fields", highlight=False, fields=FIELDS)

        #doclist = ESResponse(rank).rerank({})
        doclist = rank['hits']['hits']

        for idx in xrange(len(doclist)):
            doc = doclist[idx]
            fout.write("{0} Q0 {1} {2} {3} test # {4}\n".format(qid, doc['_id'], idx+1, doc['_score'], query))
    fout.close()

if __name__ == "__main__":
    es = Elasticsearch(timeout=100)

    hits = json.load(open(QUERY_FILE))
    random.shuffle(hits)

    begin = time.time()

    mask = [1, 0, 0, 0, 1, 1]
    for i in range(1, FOLD + 1):
        print "Training on the {0} fold...".format(i)
        left = (i - 1) * len(hits) / FOLD
        right = i * len(hits) / FOLD
        train = hits[:left] + hits[right:]
        test = hits[left:right]
        maxMAP = -1
        bestLambda = -1
        bestMu = -1
        bestWeight = None
        for LAMBDA in [0.2]:
            for MU in [100]:
                bins = sum(mask)
                generator = popol.objectsInBins(bins, 10)
                for arrange in generator:
                    #weight = [int(x) for x in bin(base)[2:].zfill(FIELD_NUM)]
                    weight = [0] * len(mask)
                    i = 0
                    for j in xrange(len(weight)):
                        if mask[j] != 0:
                            weight[j] = arrange[i]
                            i += 1
                    # test on training set
                    search(hits, LAMBDA, MU, weight)
                    exit()
                    out = evaluate("./results/prel", detail=False)
                    MAP = float(out.split('\n')[5][-6:])
                    print "\r{0}\tweight: {1}, MAP: {2}".format(time.time()-begin, weight, MAP),
                    sys.stdout.flush()
                    if MAP > maxMAP:
                        maxMAP = MAP
                        bestLambda = LAMBDA
                        bestMu = MU
                        bestWeight = copy.copy(weight)
                    break
        print "\nBest MAP: {0}\nWeight: {1}".format(maxMAP, bestWeight)

        search(hits, bestLambda, bestMu, bestWeight)
        print evaluate("./results/prel", detail=False)
        print "======================================================================="
        end = time.time()
        print "Time taken: ", end - begin, "seconds."
        exit()

    end = time.time()
    print "Time taken: ", end - begin, "seconds."
