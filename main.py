from App import *
from flask_login.login_manager import LoginManager
from flask_login import logout_user, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import flask_sqlalchemy
from io import BytesIO
import base64

app = create_app()
max_content_length = 8000000  # FILE LIMIT IS CURRENTLY 8mb
app.config["MAX_CONTENT_LENGTH"] = max_content_length
login_manager = LoginManager(app=app)
SALT = "CHEESE"
accepted_mime_types = {"image/png", "image/jpeg", "image/jpg"}


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
    return render_template("login/loginBasicBuild.html")


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
                new_user = User(name=form["name"], email=form["email"],
                                password=generate_password_hash(psw, "sha256"))
                add_new_user(new_user)
                flash(message="Created new account.", category="success")
                return redirect("/login")

    return render_template("login/customerSignUp.html")


@app.route("/home")
@login_required
def home_view():
    return render_template("menu/FrackHubMenu.html")


@app.route("/my_items")
@login_required
def my_items_view():
    user_items = current_user.items
    offers = {}

    for x in user_items:
        offers[x.id] = []

        for y in x.offers:
            offers[x.id].append(User.query.get(y.user_id))

    return render_template("menu/MyItems.html", items=current_user.items, offers=offers)


@app.route("/my_rented_items")
@login_required
def my_rented_items_view():
    all_offers = Offers.query.filter(db.and_(Offers.user_id == current_user.id)).all()
    the_items = []

    for x in all_offers:
        rent_status = Rented.query.filter(db.and_(Rented.offer_id == x.id)).first()
        if not rent_status.returned:
            the_items.append(Item.query.get(x.item_id))

    return render_template("menu/MyItemsRented.html", items=the_items)


@app.route("/search_items", methods=["GET", "POST"])
@login_required
def rented_items_view():
    result = Item.query.all()

    if request.method == "POST":

        form_data = request.form.to_dict()
        item_id = int(form_data["item"])

        all_offers = Offers.query.filter(
            db.and_(Offers.user_id == current_user.id,
                    Offers.item_id == item_id)).first()

        if all_offers is None:

            # Creates the new offer
            new_offer = Offers(item_id=item_id, user_id=current_user.id)
            add_new_offer(new_offer)
            flash("Made offer request", "success")

        else:
            flash("Already rending", "error")

    offers = []

    for x in result:
        offer_result = Offers.query.filter(
            db.and_(Offers.user_id == current_user.id, Offers.item_id == x.id,
                    Offers.answered == 0)).first()

        if offer_result is not None:
            offers.append(x.id)

    return render_template("menu/SearchItems.html", items=result,
                           user_id=current_user.id, offers=offers)


@app.route("/add_items", methods=["POST", "GET"])
@login_required
def add_items_view():
    result = Item.query.all()

    if request.method == "POST":
        post_info = request.form.to_dict()

        if any(not post_info[x] for x in post_info):
            flash("Not all fields were completed!", "error")
            return render_template("menu/UploadItems.html")

        elif not request.files:
            flash("No file was uploaded!", "error")
            return render_template("menu/UploadItems.html")

        file_info = request.files["img"]
        if file_info.mimetype.lower() not in accepted_mime_types:
            flash("Incorrect image type, use jpeg, jpg or png only!", "error")
            return render_template("menu/UploadItems.html")

        elif file_info.content_length > max_content_length:
            flash("FILE TO LARGE!", "error")
            return render_template("menu/UploadItems.html")

        # Encodes the image to base64; so it can easily
        #  be stored in a database and viewed in a browser.
        file_data = file_info.stream.read()
        file_data = "data:" + file_info.content_type + ";base64," + \
                    base64.b64encode(file_data).decode("utf-8")

        poster = current_user.id
        new_item = Item(name=post_info["name"], user_id=poster,
                        description=post_info["description"], image=file_data,
                        price=post_info["Price"])
        add_new_item(new_item)
        flash("Created new item", "success")

    return render_template("menu/UploadItems.html")


@app.errorhandler(413)
def request_entity_too_large(error):
    return "<h1>FILE TO LARGE!</h1>" \
           f"<h3><a href=\"{request.path}\">Return</a></h3>", 413


if __name__ == "__main__":
    app.run(debug=True)
