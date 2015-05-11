from flask import Flask, render_template, request, redirect, url_for
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    # proxy for a database of users
    user_database = {"kyle": ("kyle", "kyle")}

    def __init__(self, username, password):
        self.id = username
        self.password = password

    @classmethod
    def get(cls, id):
        return cls.user_database.get(id)

@login_manager.user_loader
def load_user(userid):
    user = User.get(userid)
    return User(user[0], user[1])

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/deusre/judge/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    # login
    userid = request.form['username']
    password = request.form['password']
    user = User.get(userid)
    if user:
        if user[1] == password:
            login_user(User(userid, password))
            return redirect(url_for('judge'))
    return render_template("login.html")

@app.route('/deusre/judge/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/deusre/judge", methods=["GET"])
@login_required
def judge():
    return render_template("neuro.html", params={})

if __name__ == "__main__":
    app.config["SECRET_KEY"] = "BLAHBLAHBLAH"
    app.run(host="0.0.0.0", port=8080, debug=True)
