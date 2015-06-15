"""This script generate TREC-format prel file from local judge index
"""

import json
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

    for qid in xrange(len(hits)):
        judge = json.loads(hits[qid]['_source']['judge'])
        prel = judge['prel']

        for docid, rel in prel.items():
            if rel != '0':
                print "{0} Q0 {1} {2}".format(qid, docid, int(rel) - 1)
