from flask import Flask
from flask import request
from es import ES

DEFAULT_SIZE = 10

app = Flask(__name__)
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
    while len(res) < size:
        text_response = es.text_search(params['q'], page, size*2)
        res += text_response.filter(params)
        page += 1
    return str(res)

if __name__ == "__main__":
    app.run(debug=True)
