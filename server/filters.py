def get_filter_index(hits):
    retlist = []
    for hit in hits:
        celllist = []
        data = hit['data_rows']
        for row in data:
            for cell in row:
                print cell
                value = {}
                value['text'] = cell['text']
                value['type'] = cell['type']
                if value['type'] != -1:
                    value['value'] = cell['mainValue']
                    value['cellid'] = cell['cellid']
                    value['unit'] = cell['unit']
                celllist.append(value)
        retlist.append(dict(date=hit['date'], cell_list=celllist))
    return retlist
