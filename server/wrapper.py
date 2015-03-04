import urllib
import urllib2
from bs4 import BeautifulSoup

SPLIT = "_##SPLIT##_"
DEFAULT_SIZE = 4

class Wrapper():
    def search(self, query, size=DEFAULT_SIZE):
        raise NotImplementedError("This must be implemented.")

    def get_count(self, query):
        return -1

class DryadWrapper(Wrapper):
    def __init__(self):
        self.url = "http://datadryad.org/solr/search/select/"

    def raw_search(self, query, size=DEFAULT_SIZE):
        params = {
            'q': query,
            'rows': size
        }
        urlparam = urllib.urlencode(params)
        response = urllib.urlopen(self.url, urlparam).read()
        soup = BeautifulSoup(response)
        doclist = soup.find_all('doc')
        retlist = []
        for doc in doclist:
            titleNode = doc.find("arr", {"name":"dc.title"})
            if titleNode is not None:
                retlist.append(dict(source=doc, title="Dryad: "+titleNode.find("str").get_text()))
        return retlist

    def search(self, query, size=DEFAULT_SIZE):
        return "\n".join(self.raw_search(query, size))

    def get_count(self, query):
        res = self.search(query)
        soup = BeautifulSoup(res)
        result = soup.result
        return result['numfound']

class HarvardWrapper(Wrapper):
    def __init__(self):
        self.docurl = "https://thedata.harvard.edu/dvn/api/metadataSearch/"
        self.metaurl = "https://thedata.harvard.edu/dvn/api/metadata/"
        self.size = 4

    def raw_search(self, query, size=DEFAULT_SIZE):
        query = urllib.quote_plus(query)
        query = " OR ".join(["title:"+query, "description:"+query, "keywordValue:"+query])
        query = urllib.quote(query)
        docid_res = urllib2.urlopen(self.docurl+query).read()
        soup = BeautifulSoup(docid_res)
        docids = soup.find_all('study')
        retlist = []
        for i in range(min(size, len(docids))):
            docid = docids[i]['id']
            meta = urllib2.urlopen(self.metaurl+docid).read()
            meta = BeautifulSoup(meta)
            titleNode = meta.find("titl")
            if titleNode is not None:
                retlist.append(dict(source=meta, title="Harvard: " + titleNode.get_text()))
        return retlist

    def search(self, query, size=DEFAULT_SIZE):
        rawlist = self.raw_search(query, size)
        return SPLIT.join(rawlist)

    def get_count(self, query):
        terms = query.split(' ')
        query = " OR ".join([" AND ".join(["title:"+t for t in terms]), " AND ".join(["description:"+t for t in terms])])
        response = urllib2.urlopen(self.docurl+urllib.quote(query)).read()
        soup = BeautifulSoup(response)
        reslist = soup.find_all('study')
        return len(reslist)

class PubmedWrapper(Wrapper):
    def __init__(self):
        self.docurl = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.metaurl = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.size = 4

    def raw_search(self, query, size=DEFAULT_SIZE):
        params = {
            'db': "pubmed",
            'term': query
        }
        urlparam = urllib.urlencode(params)
        response = urllib.urlopen(self.docurl, urlparam).read().lower()
        soup = BeautifulSoup(response)
        idlist = soup.idlist
        docids = idlist.find_all('id')
        retlist = []
        for i in range(min(size, len(docids))):
            docid = docids[i].get_text()
            params = {
                'retmode': 'xml',
                'db': "pubmed",
                'id': docid
            }
            urlparam = urllib.urlencode(params)
            response = urllib.urlopen(self.metaurl, urlparam)
            content = response.read()
            meta = BeautifulSoup(content)
            titleNode = meta.find("articletitle")
            if titleNode is not None:
                retlist.append(dict(source=meta,title="Pubmed: "+ titleNode.get_text()))
        return retlist

    def search(self, query, size=DEFAULT_SIZE):
        rawlist = self.raw_search(query, size)
        return SPLIT.join(rawlist)

    def get_count(self, query):
        params = {
            'db': "pubmed",
            'term': query
        }
        urlparam = urllib.urlencode(params)
        response = urllib.urlopen(self.docurl, urlparam).read().lower()
        soup = BeautifulSoup(response)
        count = soup.count
        return count.get_text()

class NIFWrapper(Wrapper):
    def __init__(self):
        self.docurl = "http://nif-services.neuinfo.org/servicesv1/v1/federation/search/"
        self.metaurl = "http://nif-services.neuinfo.org/servicesv1/v1/federation/data/"
        self.size = 4

    def raw_search(self, query, size):
        params = {
            'q': query
        }
        urlparam = urllib.urlencode(params)
        url = '?'.join([self.docurl, urlparam])
        response = urllib2.urlopen(url).read()
        soup = BeautifulSoup(response)
        results = soup.result.results
        reslist = results.find_all('result')
        retlist = []
        for i in range(min(size, len(reslist))):
            docid = reslist[i]['nifid']
            db_name = reslist[i]['db']
            category = reslist[i]['category']
            count = reslist[i].find('count')
            url = self.metaurl + docid
            params = {
                'q': query,
            }
            urlparam = urllib.urlencode(params)
            url = "?".join([url, urlparam])
            response = urllib2.urlopen(url).read()
            soup = BeautifulSoup(response)
            retlist.append(dict(source=soup.find('results'), title="NIF: {0} documents from {1} in {2} category."
                           .format(count.get_text(), db_name, category)))
        return retlist

    def search(self, query, size=DEFAULT_SIZE):
        params = {
            'q': query
        }
        urlparam = urllib.urlencode(params)
        url = '?'.join([self.docurl, urlparam])
        response = urllib2.urlopen(url).read()
        soup = BeautifulSoup(response)
        results = soup.result.results
        reslist = results.find_all('result')
        retlist = []
        for i in range(min(size, len(reslist))):
            docid = reslist[i]['nifid']
            url = self.metaurl + docid
            params = {
                'q': query,
            }
            urlparam = urllib.urlencode(params)
            url = "?".join([url, urlparam])
            response = urllib2.urlopen(url).read()
            soup = BeautifulSoup(response)
            values = soup.find_all('value')
            text = "\n".join([v.get_text() for v in values])
            retlist.append(text)
        return SPLIT.join(retlist)

    def get_count(self, query):
        params = {
            'q': query
        }
        urlparam = urllib.urlencode(params)
        url = '?'.join([self.docurl, urlparam])
        response = urllib2.urlopen(url).read()
        soup = BeautifulSoup(response)
        result = soup.result
        return result['total']

class BrainWrapper(Wrapper):
    def __init__(self):
        self.url = "http://api.brain-map.org/api/v2/data/{0}/query.xml?criteria=[name$il'*{1}*']&num_rows={2}"
        self.model = ["Product", "Structure", "Gene", "TransgenicLine"]
        self.model_idx = 0
        self.size = 8

    def raw_search(self, query, size=DEFAULT_SIZE):
        url = self.url.format(self.model[0], query, str(self.size))
        response = urllib2.urlopen(url).read()
        soup = BeautifulSoup(response)
        doclist = soup.find_all('product')
        retlist = []
        for doc in doclist:
            titleNode = doc.find("name")
            if titleNode is not None:
                retlist.append(dict(source=doc,title="Brain Atlas: " + titleNode.get_text()))
        return retlist

    def search(self, query, size=DEFAULT_SIZE):
        url = self.url.format(self.model[self.model_idx], query, str(self.size))
        self.model_idx = (self.model_idx + 1) % len(self.model)
        response = urllib2.urlopen(url).read()
        return response

    def get_count(self, query):
        response = self.search(query)
        soup = BeautifulSoup(response.lower())
        response = soup.response
        return response['total_rows']
