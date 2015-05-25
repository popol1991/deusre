from random import shuffle
from es import ESResponse

MAX_POOL_SIZE = 50

def interleave(ranklist, filters):
    reranked = []
    for rank in ranklist:
        reranked.append(ESResponse(rank).rerank(filters))

    # How many overlap do the 4 ranks have
    #v = set()
    #for rank in reranked:
        #for table in rank:
            #v.add(table['_id'])
    #print len(v)

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

    shuffle(merged)
    for i in range(len(merged)):
        merged[i]['id'] = i

    return merged
