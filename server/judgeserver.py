import pickle
import json
from datetime import datetime
from merge import interleave
from es import ES
from flask import Flask, render_template, request, redirect, url_for
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

ACCOUNT_FILE = ".account"
JUDGE_INDEX    = 'judge'
DEFAULT_SIZE   = 50
BEST_WEIGHT    = [[5, 1, 1, 1, 1, 1], # neuron
                 [1, 1, 2, 5, 5, 1]] # property
CELL_FEATURE   = ["magnitude", "mainValue", "precision", "pvalue"]
COLUMN_FEATURE = ["int_ratio", "real_ration", "mean", "stddev", "range", "accuracy", "magnitude"]
FILTER_LIST    = CELL_FEATURE + COLUMN_FEATURE

app = Flask(__name__)
app.config["SECRET_KEY"] = "BLAHBLAHBLAH"
login_manager = LoginManager()
login_manager.init_app(app)

DEFAULT_INDEX = None
DEFAULT_FILTERS = None
es = None
def build_app(config_path):
    global DEFAULT_INDEX
    global DEFAULT_FILTERS
    global es
    config = json.load(open(config_path))
    es = ES(config['es_server'])
    DEFAULT_INDEX = config['index']
    if 'filter' in config:
        DEFAULT_FILTERS = [config['filter']]
    else:
        DEFAULT_FILTERS = None
    return app

class User(UserMixin):
    # proxy for a database of users
    user_database = {"demo" : ("demo", "demo"),
                     "kyle": ("kyle", "kyle")}
    empty = True
    with open(ACCOUNT_FILE) as fin:
        users = {}
        content = "\n".join(fin.readlines())
        if len(content) != 0:
            empty = False
    if not empty:
        fin = open(ACCOUNT_FILE)
        users = pickle.load(fin)
        user_database.update(users)
        fin.close()

    def __init__(self, username, password):
        self.id = username
        self.password = password

    @classmethod
    def get(cls, id):
        return cls.user_database.get(id)

    @classmethod
    def user_exists(cls, id):
        return id in cls.user_database

    @classmethod
    def create_user(cls, id, password):
        cls.user_database[id] = (id, password)
        with open(ACCOUNT_FILE, "w") as fout:
            pickle.dump(cls.user_database, fout)

@login_manager.user_loader
def load_user(userid):
    user = User.get(userid)
    return User(user[0], user[1])

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/deusre/judge/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")
    form = request.form
    userid = form['username']
    if User.user_exists(userid):
        return "existed"
    else:
        password = form['password']
        User.create_user(userid, password)
        return "success"

@app.route('/deusre/judge/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.get_id() is None:
            return render_template("login.html")
        else:
            return redirect(url_for('judge'))
    # login
    userid = request.form['username']
    password = request.form['password']
    user = User.get(userid)
    if user:
        if user[1] == password:
            login_user(User(userid, password))
            return redirect("http://boston.lti.cs.cmu.edu/eager/deusre/about/judgescale.html")
    return render_template("login.html")

@app.route('/deusre/judge/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

def judge_body(judge):
    return {
        "user" : current_user.id,
        "judge" : judge,
        "data" : DEFAULT_INDEX,
        "timestamp" : datetime.utcnow()
    }

@app.route("/deusre/judge/result", methods=["POST"])
@login_required
def result():
    params = request.form
    if len(params) != 1:
        return "error" #TODO: something is wrong with the posted data
    judge = params.keys()[0]
    print judge
    body = judge_body(judge)
    es.index(index=JUDGE_INDEX, doc_type="judge", body=body)
    # if validate result
    return "succeed"

def get_filter_list(params):
    ret_list = []
    for f in FILTER_LIST:
        max_key = f + "_max"
        min_key = f + "_min"
        if max_key in params or min_key in params:
            flter = dict(name=f,min=params[min_key],max=params[max_key])
            ret_list.append(flter)
    return ret_list

@app.route("/deusre/judge", methods=["GET"])
@app.route("/deusre/submit", methods=["GET"])
@login_required
def judge():
    params = request.args
    if len(params) == 0:
        return render_template("judge.html", hits=[], len=0, params=None)
    query = params['q']
    if len(query) == 0:
        init_rank = es.match_all(0, DEFAULT_SIZE, index=DEFAULT_INDEX)
        res = init_rank.rerank(params)
    else:
        #init_rank = es.text_search(query, 0, DEFAULT_SIZE, index=DEFAULT_INDEX, highlight=False)
        # search with neuron best weight and best_fields type
        rank_neuro_best = es.search_with_weight(query, BEST_WEIGHT[0], DEFAULT_INDEX, size=DEFAULT_SIZE, type="best_fields", filter=DEFAULT_FILTERS)
        # search with property best weight and best_fields type
        rank_prop_best = es.search_with_weight(query, BEST_WEIGHT[1], DEFAULT_INDEX, size=DEFAULT_SIZE, type="best_fields", filter=DEFAULT_FILTERS)
        # search with neuron best weight and cross_fields type
        rank_neuro_cross = es.search_with_weight(query, BEST_WEIGHT[0], DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=DEFAULT_FILTERS)
        # search with property best weight and cross_fields type
        rank_prop_cross = es.search_with_weight(query, BEST_WEIGHT[1], DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=DEFAULT_FILTERS)
        ranklist = [rank_neuro_best, rank_prop_best, rank_neuro_cross, rank_prop_cross]
        res = interleave(ranklist, params)

    filterlist = get_filter_list(params)
    print filterlist

    return render_template('judge.html', hits=res, len=len(res), params=params, filterlist=filterlist)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)
