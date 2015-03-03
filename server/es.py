from elasticsearch import Elasticsearch

FIELDS = ["article-title", "caption", "citations", "data_*.row_header", "footnotes", "headers.header_*", "headings",
          "keywords"]
FEATURES = set(["accuracy", "magnitude", "mainValue", "precision", "pvalue"])


class ES():
    def __init__(self):
        self.es = Elasticsearch([{"host":"compute-1-33"}])

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
        return ESResponse(res)

    def match_all(self, page, size):
        query = {
            "query": {
                "match_all": {}
            },
            "from": page * size,
            "size": size
        }
        res = self.es.search(index="deusre", body=query)
        return ESResponse(res, match_all=True)

class ESResponse():
    def __init__(self, res, match_all=False):
        self.match_all = match_all
        self.hits = []
        for hit in res['hits']['hits']:
            jsn = hit['_source']
            if 'highlight' in hit:
                jsn['highlight'] = hit['highlight']
            self.hits.append(jsn)

    def size(self):
        return len(self.hits);

    def filter(self, params):
        hits = [self.convert(hit) for hit in self.hits]
        hits = self.filter_highlight(hits, params)
        return hits

    def filter_highlight(self, hits, params):
        filtered = []
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
                matched = False
                for col in columns:
                    for row in rows:
                        data = hit['data_rows']
                        if row < len(data) and col < len(data[row]):
                            cell_val = hit['data_rows'][row][col]
                            if self.satisfy(cell_val, params):
                                matched = True
                                cell_val['highlight'] = True
                            hit['data_rows'][row][col] = cell_val
                if matched:
                    filtered.append(hit)
        return filtered

    def satisfy(self, cell, params):
        if abs(float(cell['type']) + 1) < 0.000001:
            return False
        for criteria in params:
            if len(params[criteria]) > 0:
                info = criteria.split('_')
                f = info[0]
                if f in FEATURES:
                    bound = info[1]
                    if f in cell and cell[f] is not None:
                        if bound == 'min' and cell[f] < float(params[criteria]) \
                                or bound == 'max' and cell[f] > float(params[criteria]):
                            return False
        return True

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
