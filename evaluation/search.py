"""This script generate TREC-format search result for evaluation"""

import sys
sys.path.append("../server/")
import json
from es import ES, ESResponse
from elasticsearch import Elasticsearch

def build_params(query):
    params = dict()
    for p in query:
        params[p['name']] = p['value']
    return params

if __name__ == "__main__":
    es = Elasticsearch()

    body = {
        "query" : {
            "match_all": {}
        },
        "size" : 100
    }

    res = es.search(index="judge", doc_type="judge", body=body)
    hits = res['hits']['hits']

    es = ES('localhost')

    for qid in xrange(len(hits)):
        judge = json.loads(hits[qid]['_source']['judge'])
        # TODO: only text query now
        query = judge['query']
        params = build_params(query)
        print >> sys.stderr, params
        if len(params) == 1:
            highlight = False
        else:
            highlight = True
        q = query[0]['value']

        rank = es.search_with_weight(q, [1, 1, 2, 5, 5, 1], 'arxiv', size=50, type="best_fields", filter=["Computer Science"], highlight=highlight)
        doclist = ESResponse(rank).rerank(params)

        for idx in xrange(len(doclist)):
            doc = doclist[idx]
            print "{0} Q0 {1} {2} {3} test # {4} {5}".format(qid, doc['_id'], idx+1, doc['_score'], q, doc['score'])
