import sys
from flask import Flask
from flask import request, render_template
from werkzeug import SharedDataMiddleware
from es import ES

DEFAULT_SIZE = 10

app = Flask(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
    {'/static': '/deusre/search/static'})
es = ES()

@app.route("/deusre/api/<path:path>")
def route(path):
    #: pass all request to elasticsearch server
    return path

@app.route("/deusre/search/")
def search():
    #: build structured query to elasticsearch
    res = []
    params = request.args
    size = DEFAULT_SIZE
    if 'size' in params:
        size = params['size']
    page = 0
    all = sys.maxint
    while len(res) < size < all:
        text_response, all = es.text_search(params['q'], page, size*2)
        res += text_response.filter(params)
        page += 1
    print res
    return render_template('search.html', hits=res)

if __name__ == "__main__":
    app.run(debug=True)
