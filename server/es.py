import time
import datetime
import re
from elasticsearch import Elasticsearch
from operator import itemgetter

FIELDS = ["article-title", "caption", "citations", "data_*.row_header", "footnotes", "headers.header_*", "headings",
          "keywords"]
CELL_FEATURE = ["magnitude", "mainValue", "precision", "pvalue"]
COLUMN_FEATURE = ["int_ratio", "real_ration", "mean", "stddev", "range", "accuracy", "magnitude"]

#NEURO_FIELDS = ["caption", "header_row_*.header_*", "data_row_*.svalue_*", "footnote_*", "keyword_0", "article-title"]
#FIELD_PTN = [re.compile(p) for p in [r"caption", r"header_row_\d+\.header_\d+", r"data_row_\d+\.svalue_\d+", r"footnote_\d+", r"keyword_0", r"article-title"]]

NEURO_FIELDS = ["article-title", "caption", "data.data_*.row_header", "footnotes", "headers.header_*", "keywords"]
FIELD_PTN = [re.compile(p) for p in [r"article-title", r"caption", r"data.data_\d+\.row_header", r"footnotes", r"headers\.header_\d+", r"keywords"]]

class ES():
    """ A wrapper class for elasticsearch """
    def __init__(self, server):
        self.es = Elasticsearch([{"host":server}])

    def existed(self, index):
        return self.es.indices.exists(index=index)

    def create(self, index):
        self.es.indices.create(index=index)

    def delete_all(self, index):
        self.es.delete_by_query(index=index, body={'query': {'match_all':{}}})

    def refresh(self, index):
        self.es.indices.refresh(index=index)

    def search(self, index, body=None, docid=None):
        if docid is None:
            return self.es.search(index=index, body=body)
        else:
            return self.es.get(index=index, doc_type='_all', id=docid)

    def index_tmp_doc(self, index, doc_id, dbname, doc):
        body = {
            'title': doc['title'],
            'source': dbname,
            'url' : doc['url'],
            'text': doc['source'].get_text(),
            'xml': doc['source'].prettify(),
            'timestamp': datetime.datetime.fromtimestamp(time.time())
        }
        self.es.index(index=index, doc_type='doc', id=doc_id, body=body)

    def text_search(self, q, page, size, index):
        query = self.mk_text_body(q, page, size, index)
        res = self.es.search(index=index, body=query)
        return ESResponse(res)

    def mk_text_body(self, q, page, size, index):
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
        return query

    def mk_filter(self, terms):
        filters = []
        for term in terms:
            filters.append(dict(term=dict(domains=term)))
            filters.append(dict(term=dict(subdomains=term)))
        filter_body = {
            "bool" : {
                "should" : filters
            }
        }
        return filter_body

    def match_all(self, page, size, index):
        query = {
            "query": {
                "match_all": {}
            },
            "from": page * size,
            "size": size
        }
        res = self.es.search(index=index, body=query)
        return ESResponse(res, match_all=True)

    def mkbody(self, query, field, highlight=False):
        # prepare body
        qry = {
            "multi_match": {
                "query": query,
                "fields": field,
                "type": "best_fields"
            }
        }
        body = {
            "_source": True,
            "query": qry,
            "size": 100
        }
        if highlight:
            fields = dict()
            for f in field:
                fields[f] = dict()
            body['highlight'] = dict(fields=fields)
        return body

    def get_feature_vector(self, query, index, doc_type='table', field=NEURO_FIELDS):
        body = self.mkbody(query, field, highlight=True)

        # search
        res = self.es.search(index=index, doc_type=doc_type, body=body)
        return self.get_vector(res)

    def get_vector(self, res):
        hits = res['hits']['hits']
        nummatched = [0] * len(NEURO_FIELDS)
        total = 0
        for hit in hits:
            if 'highlight' in hit:
                hilights = hit['highlight']
                for f in hilights:
                    total += len(hilights[f])
                    for i in range(len(NEURO_FIELDS)):
                        pattern = FIELD_PTN[i]
                        if pattern.search(f) is not None:
                            nummatched[i] += len(hilights[f])
                            break
        return [w for w in nummatched]

    def search_neuroelectro(self, query, weight, index, doc_type='table'):
        field = ["{0}^{1}".format(NEURO_FIELDS[i], weight[i]) for i in range(len(weight))]
        body = self.mkbody(query, field)
        res = self.es.search(index=index, doc_type=doc_type, body=body)
        return res

class ESResponse():
    def __init__(self, res, match_all=False):
        self.match_all = match_all
        self.hits = []
        self.scores = []
        self.ids = []
        for hit in res['hits']['hits']:
            jsn = hit['_source']
            if 'highlight' in hit:
                jsn['highlight'] = hit['highlight']
            self.hits.append(jsn)
            self.scores.append(hit['_score'])
            self.ids.append(hit['_id'])

    def size(self):
        return len(self.hits);

    def rerank(self, params):
        hits = [self.convert(hit) for hit in self.hits]
        filtered = self.filter_highlight(hits, params)
        reranked = [e[0] for e in sorted(filtered, key=itemgetter(1), reverse=True)]
        #: Add id for tables for selector
        for i in range(len(reranked)):
            reranked[i]['id'] = i
        return reranked

    def filter_highlight(self, hits, params):
        filtered = []
        tail = []
        for hit in hits:
            if self.match_all or 'highlight' in hit:
                columns = []
                rows = []
                if not self.match_all:
                    hl = hit['highlight']
                    columns = [int(key.split('_')[1]) for key in hl if key.startswith('headers')]
                    rows = [int(key.split('.')[1].split('_')[1]) for key in hl if key.startswith('data')]
                if len(columns) == 0:
                    width = len(hit['data_rows'][0])
                    columns = range(width)
                if len(rows) == 0:
                    height = len(hit['data_rows'])
                    rows = range(height)
                col_scores = []
                for col in columns:
                    #: iterate over filters as terms here
                    #: need to figure out how to combine scores from different columns
                    #: use the number of matched cells as term frequency and column length as doclen
                    tf = 0
                    doclen = 0
                    feature_scores = []
                    for feature in CELL_FEATURE:
                        if not self.has_feature(feature, params):
                            continue
                        for row in rows:
                            doclen += 1
                            data = hit['data_rows']
                            if data is None or data[row] is None: continue
                            if row < len(data) and col < len(data[row]):
                                cell_val = hit['data_rows'][row][col]
                                if not self.is_text(cell_val) and self.satisfy(cell_val, params, feature):
                                    tf += 1
                                    if 'highlight' not in cell_val:
                                        cell_val['highlight'] = 1
                                    else:
                                        cell_val['highlight'] += 1
                                hit['data_rows'][row][col] = cell_val
                        score = tf * 1.0 / doclen
                        feature_scores.append(score)
                    cellscore = self.combine_filter(feature_scores)

                    columnscore = 1
                    matched = 0
                    total = 0
                    for feature in COLUMN_FEATURE:
                        if not self.has_feature(feature, params):
                            continue
                        key = "col_{0}".format(col)
                        if 'column_stats' not in hit or key not in hit['column_stats']:
                            continue
                        total += 1
                        if self.satisfy(hit['column_stats'][key], params, feature):
                            matched += 1
                    if total == 0:
                        columnscore = 1
                    else:
                        columnscore = matched * 1.0 / total

                    col_scores.append(cellscore * columnscore)
                score = self.combine(col_scores)
                hit['score'] = score
                filtered.append((hit, score))
            else:
                tail.append((hit, 0))
        filtered += tail
        return filtered

    def is_text(self, cell):
        if (cell['type'] + 1 < 0.000001):
            return True
        return False

    def combine_filter(self, scores):
        prod = 1
        for s in scores:
            prod *= s
        return prod

    def combine(self, scores):
        return max(scores)

    def has_feature(self, feature, params):
        minimum = "_".join([feature, "min"])
        maximum = "_".join([feature, "max"])
        min_not_exist = (minimum not in params or len(params[minimum]) == 0)
        max_not_exist = (maximum not in params or len(params[maximum]) == 0)
        if (min_not_exist and max_not_exist):
            return False
        else:
            return True

    def satisfy(self, cell, params, feature):
        minimum = "_".join([feature, "min"])
        maximum = "_".join([feature, "max"])
        min_not_exist = (minimum not in params or len(params[minimum]) == 0)
        max_not_exist = (maximum not in params or len(params[maximum]) == 0)
        if (min_not_exist or cell[feature] > float(params[minimum])) \
                and (max_not_exist or cell[feature] < float(params[maximum])):
            return True
        return False

    def convert(self, hit):
        # header
        length = 0
        depth = 0
        for h in hit['headers']:
            idx = int(h.split('_')[1])
            length = idx if idx > length else length
            depth = len(hit['headers'][h])
        header_rows = []
        for i in range(depth):
            headers = [None] * (length + 1)
            header_rows.append(headers)
        for h in hit['headers']:
            idx = int(h.split('_')[1])
            for d in range(len(hit['headers'][h])):
                if d < len(header_rows) and idx < len(header_rows[d]):
                    header_rows[d][idx] = dict(value=hit['headers'][h][d])
        hit['header_rows'] = header_rows

        # data
        length = 0
        for r in hit['data']:
            idx = int(r.split('_')[1])
            length = idx if idx > length else length
        data_rows = [None] * (length + 1)
        for r in hit['data']:
            idx = int(r.split('_')[1])
            row = [dict(type=-1, text=hit['data'][r]['row_header'])]
            for val in hit['data'][r]['values']:
                row.append(val)
            data_rows[idx] = row
        hit['data_rows'] = data_rows
        return hit

    def hits_for_federate(self):
        fhits = []
        for i in range(len(self.hits)):
            hit = {
                '_score': self.scores[i],
                '_source': dict(title="Elsevier: "+self.hits[i]['caption']),
                '_id': "elsevier:"+self.ids[i]
            }
            fhits.append(hit)
        return fhits
