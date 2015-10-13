import sys

if __name__ == "__main__":
    f1 = open(sys.argv[1])
    f2 = open(sys.argv[2])
    l1 = f1.readline()
    l2 = f2.readline()
    while True:
        docid1, qid1 = l1.split("\t")[:2]
        docid2, qid2 = l2.split("\t")[:2]
        if docid1 == docid2 and qid1 == qid2:
            # join
            print "\t".join([l1.strip(), "\t".join(l2.split("\t")[2:])]),
            l1 = f1.readline()
            l2 = f2.readline()
        elif docid1 < docid2 or docid1 == docid2 and qid1 < qid2:
            # advance 1
            l1 = f1.readline()
        elif docid1 > docid2 or docid1 == docid2 and qid1 > qid2:
            # advance 2
            l2 = f2.readline()

        if not l1 or not l2:
            break
    f1.close()
    f2.close()
