"""This script generate TREC-format search result for evaluation"""

import sys
sys.path.append("../server/")
import json
from es import ES
from elasticsearch import Elasticsearch

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
        q = query[0]['value']

        rank = es.search_with_weight(q, [1]*6, 'arxiv', size=50, type="best_fields", filter=["Computer Science"], highlight=False)
        doclist = rank['hits']['hits']

        for idx in xrange(len(doclist)):
            doc = doclist[idx]
            print "{0} Q0 {1} {2} {3} test".format(qid, doc['_id'], idx+1, doc['_score'])
