import json
import popol
import random
from elasticsearch import Elasticsearch

class Assessment(object):
    """A class represents assessments stored in an elasticsearch server"""

    MAX_SIZE = 1000
    ASSESS_QUERY = {"query":{"match_all":{}}, "size":MAX_SIZE}

    def __init__(self, config):
        self.es = Elasticsearch([{"host": config["es_server"]}], timeout=100)
        self.index = config['judgeIndex']
        self.docType = config['docType']
        self.dataSrc = config['dataSrc']
        self.invalidList = None

        self.fetchAssessments()

    def fetchAssessments(self):
        self.judgeList = []
        res = self.es.search(index=self.index, doc_type=self.docType, body=Assessment.ASSESS_QUERY)
        print len(res)
        hits = res['hits']['hits']

        for qid in xrange(len(hits)):
            src = hits[qid]['_source']

            dataSrc = src['data']
            if dataSrc != self.dataSrc:
                continue

            judgeContent = src['judge']
            if judgeContent.startswith('{'):
                judge = json.loads(judgeContent)
                src['judge'] = judge
                self.judgeList.append(src)

    def update(self):
        self.fetchAssessments();
        self.invalidList = None

    def nextToValidate(self, userid):
        if self.invalidList is None:
            self.getInvalidList()
        candidates = []
        for j in self.invalidList:
            print j
            if 'user' in j and j['user'] != userid:
                candidates.append(j)
        candidates = [j for j in self.invalidList if 'user' in j and j['user'] != userid]
        if len(candidates) == 0:
            return None
        else:
            return candidates[random.randint(0, len(candidates)-1)]

    def getInvalidList(self):
        print "Getting invalid list..."
        self.invalidList = []
        n = len(self.judgeList)
        for i in xrange(n):
            uniq = True
            for j in xrange(n):
                if i != j and popol.dictEqual(self.judgeList[i]['judge']["query"], self.judgeList[j]['judge']["query"]):
                    uniq = False
                    break
            if uniq:
                self.invalidList.append(self.judgeList[i])
        print len(self.invalidList)
