import sys
from flask import Flask
from flask import request, render_template, make_response
import requests
from werkzeug import SharedDataMiddleware
from es import ES

DEFAULT_SIZE = 20

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})
es = ES()

@app.route("/deusre/api/<path:path>")
def route(path):
    #: pass all request to elasticsearch server
    target = "http://compute-1-33:9200/" + path
    method = request.method
    data = request.get_data()
    res = make_response(requests.get(target, data=data, params=request.args).content)
    return res

@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    res = []
    params = request.args
    if len(params) == 0:
        return render_template('search.html', hits=[], query="")
    size = DEFAULT_SIZE
    if 'size' in params:
        size = params['size']
    page = 0
    query = params['q']
    if len(query) == 0:
        text_response = es.match_all(page, size)
    else:
        text_response = es.text_search(query, page, size)
    res += text_response.filter(params)
    page += 1
    return render_template('search.html', hits=res, len=len(res), query=params['q'])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
