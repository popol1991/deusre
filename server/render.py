def get_list(src, tag):
    retlist = []
    for key in src:
        if tag in key:
            idx = int(key.split('_')[-1])
            if len(retlist) <= idx:
                retlist += [None] * (idx - len(retlist) + 1)
            retlist[idx] = src[key]
    return retlist

def get_rows(src, tag):
    retlist = []
    for row in src:
        retlist.append(get_list(row, tag))
    return retlist

def render_neuroelectro(hit):
    hit["header_rows"] = get_rows(hit['header_rows'], 'header')
    hit["data_rows"] = get_rows(hit['data_rows'], 'svalue')
    return hit
