from elasticsearch import Elasticsearch

FIELDS = ["article-title", "caption", "citations", "data_*.row_header", "footnotes", "headers.header_*", "headings", "keywords"]

class ES():
    def __init__(self):
        self.es = Elasticsearch()

    def text_search(self, q, page, size):
        query = {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": FIELDS,
                    "type": "cross_fields"
                }
            },
            "from": page * size,
            "size": size,
            "highlight": {
                "fields": {
                    "headers.header_*": {},
                    "data.data_*.row_header": {}
                }
            }
        }
        res = self.es.search(index="deusre", body=query)
        return res

class ESResponse():
    pass
