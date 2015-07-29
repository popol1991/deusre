import sys
import re

PREC_K = [5, 10, 15, 20, 30, 100]

LENGTH = 27
LINE_TOTAL = 1
LINE_PREC = 18

def split(line):
    return re.split(r"\s+", line)

if __name__ == '__main__':
    trecLines = sys.stdin.readlines()[:-30]
    queryLen = len(trecLines) / LENGTH

    recAtK = [0] * 6
    for q in xrange(queryLen):
        total = int(split(trecLines[q * LENGTH + LINE_TOTAL])[2])
        for p in xrange(6):
            precLine = trecLines[q * LENGTH + LINE_PREC + p]
            prec = float(split(precLine)[2])
            numRel = prec * PREC_K[p]
            recall = numRel / total
            recAtK[p] += recall

    avgRecAtK = [x / queryLen for x in recAtK]
    print avgRecAtK
