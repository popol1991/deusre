import logging
import pickle
import json
import filters
from assessments import Assessment
from subprocess import check_output
from datetime import datetime
from merge import interleave
from es import ES
from flask import Flask, render_template, request, redirect, url_for
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

ACCOUNT_FILE = ".account"
SURVEY_FILE = ".survey"
JUDGE_INDEX    = 'judge'
DEFAULT_SIZE   = 30
#BEST_WEIGHT    = [[5, 1, 1, 1, 1, 1, 1], # neuron
                 #[1, 1, 2, 5, 5, 1, 1]] # property

BEST_WEIGHT = [
    [1,0,0,0,0,1,0],
    [0,1,0,0,0,0,0],
    [0,0,1,0,0,0,0],
    [0,0,0,1,0,0,0],
    [0,0,0,0,1,0,0],
    [0,0,0,0,0,0,1],
    [0,1,1,0,1,0,0]
]
CELL_FEATURE   = ["magnitude", "mainValue", "precision", "pvalue"]
COLUMN_FEATURE = ["int_ratio", "real_ration", "mean", "stddev", "range", "accuracy", "magnitude"]
FILTER_LIST    = CELL_FEATURE + COLUMN_FEATURE

ARXIV_FIELDS = ["article-title", "caption", "row_header_field", "footnotes", "col_header_field", "abstract", "citations"]

app = Flask(__name__)
app.config["SECRET_KEY"] = "BLAHBLAHBLAH"
login_manager = LoginManager()
login_manager.init_app(app)

DEFAULT_INDEX = None
DEFAULT_FILTERS = None
es = None
assessed = None

# initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('judge.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info('started')

def build_app(config_path):
    global DEFAULT_INDEX
    global DEFAULT_FILTERS
    global JUDGE_INDEX
    global es
    global assessed
    config = json.load(open(config_path))
    es = ES(config['es_server'])
    JUDGE_INDEX = config['judgeIndex']
    assessed = Assessment(config)
    DEFAULT_INDEX = config['index']
    if 'filter' in config:
        DEFAULT_FILTERS = [config['filter']]
    else:
        DEFAULT_FILTERS = None
    return app

class User(UserMixin):
    # proxy for a database of users
    user_database = {"demo" : ("demo", "demo", True),
                     "kyle": ("kyle", "kyle", False)}
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
        cls.user_database[id] = (id, password, True)
        with open(ACCOUNT_FILE, "w") as fout:
            pickle.dump(cls.user_database, fout)

    @classmethod
    def first_time_login(cls, id):
        user = cls.user_database[id]
        cls.user_database[id] = (id, user[1], False)
        with open(ACCOUNT_FILE, "w") as fout:
            pickle.dump(cls.user_database, fout)

@login_manager.user_loader
def load_user(userid):
    user = User.get(userid)
    if user is None:
        return None
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

@app.route('/deusre/judge/description')
def description():
    return render_template('description.html')

@app.route('/deusre/judge/consent', methods=['GET'])
def consent():
        try:
            user = User.get(current_user.id)
            print user
            if user[2]:
                return render_template("consent.html")
            else:
                return redirect(url_for("survey"))
        except:
            return redirect(url_for("login"))

@app.route('/deusre/judge/survey', methods=['GET','POST'])
def survey():
    if request.method == 'GET':
        try:
            print current_user.id
            user = User.get(current_user.id)
            print user
            if user[2]:
                return render_template("survey.html")
            else:
                return redirect(url_for("judge"))
        except:
            return redirect(url_for("login"))
    elif request.method == 'POST':
        # save survey result
        empty = True
        survey_dict = {}
        with open(SURVEY_FILE) as fin:
            content = "\n".join(fin.readlines())
            if len(content) != 0:
                empty = False
        if not empty:
            fin = open(SURVEY_FILE)
            survey_dict = pickle.load(fin)
            fin.close()
        survey_dict[current_user.get_id()] = request.form
        with open(SURVEY_FILE, "w") as fout:
            pickle.dump(survey_dict, fout)

        User.first_time_login(current_user.id)
        return redirect(url_for("judge"))

@app.route('/deusre/judge/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.get_id() is None or User.get(current_user.id)[2]:
            return render_template("login.html")
        else:
            return redirect(url_for('judge'))
    # login
    userid = request.form['username']
    logger.info("User {0} trying to login".format(userid))
    password = request.form['password']
    user = User.get(userid)
    if user:
        if user[1] == password:
            login_user(User(userid, password))
            return render_template("entry.html")
    logger.info("User {0} login successfully".format(userid))
    return render_template("login.html")

@app.route('/deusre/judge/logout')
def logout():
    logger.info("User: {0} logging out".format(current_user.id))
    logout_user()
    return redirect(url_for('login'))

def judge_body(judge):
    return {
        "user" : current_user.id,
        "judge" : judge,
        "data" : DEFAULT_INDEX,
        "timestamp" : datetime.utcnow()
    }

@app.route("/deusre/judge/log", methods=["POST"])
@login_required
def log():
    """Log whatever message received from clients."""
    userid = current_user.id
    message = request.form['message']
    logger.info("User {0} Client: ".format(userid) + message)
    return 'succeed'

@app.route("/deusre/judge/result", methods=["POST"])
@login_required
def result():
    logger.info("Result submitted from User {0}".format(current_user.id))
    params = request.form
    if len(params) != 1:
        return "error" #TODO: something is wrong with the posted data
    judge = params.keys()[0]
    print judge
    body = judge_body(judge)
    logger.info("Sending result to ES")
    es.index(index=JUDGE_INDEX, doc_type="judge", body=body)
    logger.info("Result indexed in ES")
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

@app.route("/deusre/validate")
@login_required
def validate():
    userid = current_user.id
    if User.get(userid)[2]:
        return redirect(url_for('login'))

    toValid = assessed.nextToValidate(userid)
    if toValid is None:
        return "All queries have been validated.  Thanks!"

    params = dict()
    query = toValid['judge']['query']
    for kvp in query:
        params[kvp['name']] = kvp['value']
    return pool(params)

@app.route("/deusre/judge", methods=["GET"])
@app.route("/deusre/submit", methods=["GET"])
@login_required
def judge():
    userid = current_user.id
    if User.get(userid)[2]:
        return redirect(url_for('login'))

    params = request.args
    if len(params) == 0:
        logger.info("Received empty query")
        return render_template("judge.html", hits=[], len=0, params=None)
    logger.info("Received query: {0} from user {1}".format(str(params), userid))
    return pool(params)

def pool(params):
    logger.info("Pooling result...")
    query = params['q']
    domain = params['domain']
    domain_filter = [domain] if domain != 'all' else None
    if len(query) == 0:
        init_rank = es.match_all(0, DEFAULT_SIZE, index=DEFAULT_INDEX)
        res = init_rank.rerank(params)
    else:
        #init_rank = es.text_search(query, 0, DEFAULT_SIZE, index=DEFAULT_INDEX, highlight=False)
        rank_simple = es.search_with_weight(query, [1]*len(ARXIV_FIELDS), DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
        # search with neuron best weight and best_fields type
        #rank_neuro_best = es.search_with_weight(query, BEST_WEIGHT[0], DEFAULT_INDEX, size=DEFAULT_SIZE, type="best_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
        # search with property best weight and best_fields type
        #rank_prop_best = es.search_with_weight(query, BEST_WEIGHT[1], DEFAULT_INDEX, size=DEFAULT_SIZE, type="best_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
        # search with neuron best weight and cross_fields type
        #rank_neuro_cross = es.search_with_weight(query, BEST_WEIGHT[0], DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
        # search with property best weight and cross_fields type
        #rank_prop_cross = es.search_with_weight(query, BEST_WEIGHT[1], DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
        ranklist = [rank_simple]
        for weight in BEST_WEIGHT:
            rank = es.search_with_weight(query, weight, DEFAULT_INDEX, size=DEFAULT_SIZE, type="cross_fields", filter=domain_filter, fields=ARXIV_FIELDS, highlight=False)
            ranklist.append(rank)

        res = interleave(ranklist, params)

    filterlist = get_filter_list(params)
    filter_index = filters.get_filter_index(res)
    idlist = [hit['_id'] for hit in res]
    logger.info("Ready to return ranking: " + str(idlist))

    return render_template('judge.html', hits=res, len=len(res), params=params, filterlist=filterlist, filter_index=json.dumps(filter_index))

@app.route("/deusre/mlt", methods=["GET"])
def mlt():
    params = request.args
    query = params['q']
    path = params['path']
    out = check_output(["java", "-cp", "/Users/Kyle/IdeaProjects/mlt/lib/table2query.jar:/Users/Kyle/IdeaProjects/mlt/lib/stanford-corenlp-full-2015-04-20/stanford-corenlp-3.5.2.jar:/Users/Kyle/IdeaProjects/mlt/lib/stanford-corenlp-full-2015-04-20/stanford-corenlp-3.5.2-models.jar:/Users/Kyle/IdeaProjects/mlt/lib/", "MoreLikeThis", query, path])
    print out
    result = es.search_with_term_weight(out, DEFAULT_INDEX, filter=DEFAULT_FILTERS)
    result = result.rerank(params)
    return render_template('judge.html', hits=result, len=len(result), params=params, filterlist=[])

if __name__ == "__main__":
    build_app("./config-physics.json")
    app.run(host="0.0.0.0", port=8080, debug=True)
