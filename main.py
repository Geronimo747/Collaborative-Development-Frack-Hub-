from App import *
from flask_login.login_manager import LoginManager
from flask_login import logout_user, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
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
    code = 200

    if request.method == "POST":
        form = request.form.to_dict()

        # Checks the form has been filled in.
        if not form["email"]:
            flash(message="You need to enter an email.", category="error")
            code = 400
        elif not form["fname"]:
            flash(message="You need to enter a first name.", category="error")
            code = 400
        elif not form["pswd"]:
            flash(message="You need to enter a password.", category="error")
            code = 400
        elif not form["address"]:
            flash("You need to enter an address.", category="error")
            code = 400
        elif not form["postcode"]:
            flash("You need to enter a postcode.", category="error")
            code = 400
        else:

            # Makes sure the user isn't unique.
            user = User.query.filter_by(email=form["email"]).first()
            if user:
                flash(message="That email is taken, you need to enter a unique email.", category="error")

            # Adds the new user to the database.
            else:
                dob = None

                if form["DoB"]:
                    year, month, day = form["DoB"].split("-")
                    dob = datetime(year=year, month=month, day=day)

                psw = SALT + form["pswd"]
                new_user = User(name=f'{form["fname"]} {form["lname"]}', email=form["email"],
                                password=generate_password_hash(psw, "sha256"),
                                postcode=form["postcode"],
                                address=form["address"],
                                number=form["phone"] if form["phone"] else None,
                                dob=dob)

                add_new_user(new_user)
                flash(message="Created new account.", category="success")
                return redirect("/login")

    return render_template("login/customerSignUp.html", code=code)


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
            if y.answered == False:
                offers[x.id].append({"user": User.query.get(y.user_id), "offer": y})

    return render_template("menu/MyItems.html", items=current_user.items, offers=offers)


@app.route("/my_rented_items", methods=("GET", "POST"))
@login_required
def my_rented_items_view():
    """Loads all the items the user is renting from other people."""

    all_offers = Offers.query.filter(db.and_(Offers.user_id == current_user.id,
                                             Offers.answered == True,
                                             Offers.returned == False)).all()

    if request.method == "POST":
        form_data = request.form.to_dict()

        if "return" in form_data:
            item_id = int(form_data["return"])
            item = Item.query.get(item_id)

            if item is None:
                flash("Error returning item.", "error")

            else:
                for offer in all_offers:
                    if offer.item_id == item.id:
                        item.is_rented = False
                        offer.returned = True
                        db.session.commit()
                        flash("Successfully returned item.", "success")

                        all_offers = Offers.query.filter(db.and_(Offers.user_id == current_user.id,
                                                                 Offers.answered == True,
                                                                 Offers.returned == False)).all()
                        break

    the_items = []

    for x in all_offers:
        the_items.append(Item.query.get(x.item_id))

    return render_template("menu/MyItemsRented.html", items=the_items)


@app.route("/search_items", methods=["GET", "POST"])
@login_required
def rented_items_view():
    result = Item.query.filter(Item.is_rented == 0).all()

    # A request is being made to rent an item on the list
    if request.method == "POST":

        form_data = request.form.to_dict()
        item_id = int(form_data["item"])

        all_offers = Offers.query.filter(
            db.and_(Offers.user_id == current_user.id,
                    Offers.item_id == item_id,
                    Offers.answered == False)).first()

        the_item = Item.query.get(item_id)
        if the_item is None:
            flash("Error finding item.", "error")

        elif the_item.is_rented is True:
            flash("Item is already being rented.", "error")

        elif all_offers is None:

            # Creates the new offer
            new_offer = Offers(item_id=item_id, user_id=current_user.id)
            add_new_offer(new_offer)
            flash("Made offer request", "success")

        else:
            flash("Already renting.", "error")

    # Loads all the items not currently being rented.
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


@app.route("/confirm_offer/<offer_id>", methods=("GET", "POST"))
@login_required
def confirm_offer_route(offer_id: str):
    offer = Offers.query.get(offer_id)

    if offer is not None:

        item = Item.query.get(offer.item_id)
        requester = User.query.get(offer.user_id)

        if item is not None and requester is not None:
            owner = User.query.get(item.user_id)
            if owner is not None and owner.id != current_user.id:
                flash("Unauthorized.", "error")
                return render_template("menu/FrackHubMenu.html", code=403)

            if request.method == "POST":
                if item.is_rented is True:
                    flash("Item already being rented.", "error")

                result = request.form.to_dict()
                if "response" in result and item.is_rented is False:

                    if result["response"] == "acc":
                        flash("Successfully accepted request.", "success")

                        # Sets the items rented status
                        item.is_rented = True
                        offer.answered = True
                        db.session.commit()

                        return redirect("/home")

                    else:
                        flash("Successfully declined request.", "success")
                        offer.answered = True
                        db.session.commit()
                        return redirect("/home")

            return render_template("menu/OrderConfimration.html",
                                   requester=requester,
                                   offer=offer,
                                   item=item)

        else:
            flash("Unable to load offer.", "error")
    else:
        flash("Unable to load offer.", "error")

    # offer_id
    return render_template("menu/FrackHubMenu.html")


@app.errorhandler(413)
def request_entity_too_large(error):
    return "<h1>FILE TO LARGE!</h1>" \
           f"<h3><a href=\"{request.path}\">Return</a></h3>", 413


if __name__ == "__main__":
    app.run(debug=True)
