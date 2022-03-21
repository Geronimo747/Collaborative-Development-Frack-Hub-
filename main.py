from App import *
from flask_login.login_manager import LoginManager
from flask_login import logout_user, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta


app = create_app()
login_manager = LoginManager(app=app)
SALT = "CHEESE"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
def front_page():
    if current_user.is_authenticated:
        return redirect("/home")
    else:
        return redirect("/login")


@app.route("/login", methods=("POST", "GET"))
def login_route():

    # The user has posted a form.
    if request.method == "POST":
        form = request.form.to_dict()

        # Checks the form has been filled in.
        if not form["email"]:
            flash(message="You need to enter a valid email.", category="error")
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

            # The users details are not correct.
            flash("Email or password is incorrect.", category="error")

    # The login html page in templates.
    return render_template("loginBasicBuild.html")


@app.route("/signup", methods=("GET", "POST"))
def signup_route():
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

            # Makes sure the user isn't unique.
            user = User.query.filter_by(email=form["email"]).first()
            if user:
                flash(message="That email is taken, you need to enter a unique email.", category="error")

            # Adds the new user to the database.
            else:
                psw = SALT + form["pswd"]
                new_user = User(name=form["name"], email=form["email"], password=generate_password_hash(psw, "sha256"))
                add_new_user(new_user)
                flash(message="Created new account.", category="success")
                return redirect("/login")

    return render_template("customerSignUp.html")


@app.route("/home")
@login_required
def home_view():
    return render_template("FrackHubMenu.html")


@app.route("/my_items")
@login_required
def my_items_view():
    # TODO: Retrieve items here
    return render_template("MyItems.html")


@app.route("/my_rented_items")
@login_required
def my_rented_items_view():
    return render_template("MyItemsRented.html")


@app.route("/rented_items")
@login_required
def rented_items_view():
    return render_template("RentItems.html")


@app.route("/add_items")
@login_required
def add_items_view():
    return render_template("UploadItems.html")



if __name__ == "__main__":
    app.run(debug=True)
