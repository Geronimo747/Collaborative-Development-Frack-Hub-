from flask import Flask, request, render_template, flash, redirect, get_flashed_messages, session
from flask_login.login_manager import LoginManager
from flask_login import UserMixin, logout_user, login_required, login_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta


SALT = "CHEESE"


# Initialize this web application.
app = Flask(__name__)
app.config["SECRET_KEY"] = "HAHA_PLZ_DON'T_STEAL_ME"


# Creates the login manager instance
login_manager = LoginManager(app=app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Creates the database instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
db = SQLAlchemy(app=app)


# The user database model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


@app.route('/')
def hello_world():  # put application's code here
    session.pop('_flashes', None)
    return "<h1>Boop</h1>"


@app.route("/logout")
def log_out_route():
    session.pop('_flashes', None)

    # The user is logged in.
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", category="success")
        return redirect("/login")

    # The user isn't logged in.
    else:
        flash("You are not logged in.", category="error")
        return redirect("/home")


@app.route("/home")
def logged_in():
    session.pop('_flashes', None)

    # The user is logged in.
    if current_user.is_authenticated:
        flash("You are logged in.", category="success")
        show_login = False
    # The user isn't logged in.
    else:
        flash("You are not logged in.", category="error")
        show_login = True
    return render_template("results.html", show_login=show_login)


@app.route("/login", methods=["POST", "GET"])
def login_route():
    session.pop('_flashes', None)

    if request.method == "POST":
        form = request.form.to_dict()

        # Checks the form has been filled in.
        if not form["email"]:
            flash(message="You need to enter an email.", category="error")
        elif not form["pswd"]:
            flash(message="You need to enter a password.", category="error")
        else:

            # The user is attempting a login even though they're already
            #   logged in, this logs them out.
            if current_user.is_authenticated:
                logout_user()

            user = User.query.filter_by(email=form["email"]).first()

            # There is a user with that email address.
            if user:
                if check_password_hash(user.password, SALT + form["pswd"]):
                    flash("Logged in!", category="success")
                    login_user(user, duration=timedelta(minutes=1))
                    return redirect(f"/home")

            flash("Email or password is incorrect.", category="error")

    return render_template("loginBasicBuild.html")


@app.route("/signup", methods=["POST", "GET"])
def signup_route():
    session.pop('_flashes', None)

    if request.method == "POST":
        form = request.form.to_dict()

        # Checks the form has been filled in.
        if not form["email"]:
            flash(message="You need to enter an email.", category="error")
        elif not form["name"]:
            flash(message="You need to enter a name.", category="error")
        elif not form["pswd"]:
            flash(message="You need to enter a password.", category="error")
        else:
            user = User.query.filter_by(email=form["email"]).first()
            if user:
                flash(message="That email is taken, you need to enter a unique email.", category="error")
            else:
                psw = SALT + form["pswd"]
                new_user = User(name=form["name"], email=form["email"], password=generate_password_hash(psw, "sha256"))
                db.session.add(new_user)
                db.session.commit()
                flash(message="Created new account.", category="success")
                return redirect("/login")
        return redirect("/signup")

    return render_template("customerSignUp.html")


if __name__ == '__main__':
    app.run(debug=True)
