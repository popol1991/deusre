from random import shuffle
from es import ESResponse

MAX_POOL_SIZE = 50

def getpid(docid):
    pid = ".".join(docid.split('.')[:-1])
    return pid

def interleave(ranklist, filters):
    reranked = []
    for rank in ranklist:
        reranked.append(ESResponse(rank).rerank(filters))

    merged = []
    visited_id = set()
    while True:
        all_empty = True
        for rank in reranked:
            if len(merged) < MAX_POOL_SIZE and len(rank) > 0:
                all_empty = False
                table = rank.pop(0)
                table_id = table['_id']
                if not table_id in visited_id:
                    merged.append(table)
                    visited_id.add(table_id)
        if all_empty or len(merged) == MAX_POOL_SIZE:
            break

    piddict = {}
    for doc in merged:
        pid = getpid(doc['_id'])
        if not pid in piddict:
            piddict[pid] = []
        piddict[pid].append(doc)
    keylist = piddict.keys()
    shuffle(keylist)
    rank_to_render = []
    for key in keylist:
        for doc in piddict[key]:
            rank_to_render.append(doc)
    #shuffle(merged)

    for i in xrange(len(merged)):
        merged[i]['id'] = i

    #return merged
    return rank_to_render
