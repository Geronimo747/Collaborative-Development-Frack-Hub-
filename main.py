from App import *
from flask_login.login_manager import LoginManager
from flask_login import logout_user, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import validators

# FFMPEG used to resize image files quicker than PILLOW as it's written in C.
os.environ["ffmpeg"] = f"{os.getcwd()}/bin/ffmpeg.exe"
os.environ["ffprobe"] = f"{os.getcwd()}/bin/ffprobe.exe"
os.environ["ffplay"] = f"{os.getcwd()}/bin/ffplay.exe"

app = create_app()
max_content_length = 8000000  # FILE LIMIT IS CURRENTLY 8mb
app.config["MAX_CONTENT_LENGTH"] = max_content_length
login_manager = LoginManager(app=app)
SALT = "CHEESE"
accepted_mime_types = {"image/png", "image/jpeg", "image/jpg"}


@login_manager.user_loader
def load_user(user_id):
    """
    Used by the flask plugin to load information about a user.
    """
    return Users.query.get(user_id)


def display_employee() -> bool:
    """
    Whether extra employee tab is added to the tab bar.
    """
    return current_user.user_type > 0


# Routes:
#   login
#   signup
#   home [frackhub menu]
#   my items
#   employee
#   item view
#   item image
#   list of renting items
#   confirm order
#   search items
#   add item


@app.route("/", methods=("GET",))
def front_page():
    """
    This is the root page of the entire website.
    If you are logged in. You are automatically directed to your home page.
    If you are not logged in. You are automatically directed to the login page.
    """
    if current_user.is_authenticated:
        return redirect("/home")
    else:
        return redirect("/login")


@app.route("/login", methods=("POST", "GET"))
def login_page():
    """
    This is the login page for this website.
    To login you should already have an account.
    """

    # The post method is used by the page to send information to the server.
    #   In this instance we'll be checking for user login details.
    if request.method == "POST":

        # Removes all flash messages.
        session.pop('_flashes', None)

        # Gets the form data from the post.
        form = request.form.to_dict()

        # For whatever reason a form wasn't present.
        if not form:
            return render_template("login/loginBasicBuild.html")

        # Makes sure both email and password are present in the form data.
        items_in_form = ("pswd", "email")
        if any(x not in form for x in items_in_form):
            return render_template("login/loginBasicBuild.html")

        # Checks that a valid email address has been entered.
        if not validators.email(form["email"]):
            flash(message="You need to enter a valid email.", category="error")

        # Checks that a password has been entered.
        if not form["pswd"]:
            flash(message="You need to enter a password.", category="error")

        # Both items have been entered.
        if form["pswd"] and validators.email(form["email"]):

            # The user is attempting a login even though they're already
            #   logged in, this logs them out.
            if current_user.is_authenticated:
                logout_user()

            # Tries to find the user.
            user = Users.query.filter_by(email=form["email"]).first()

            # If a user with that email actually exists.
            if user:
                if check_password_hash(user.password, SALT + form["pswd"]):
                    flash("Logged in!", category="success")
                    login_user(user, duration=timedelta(minutes=1))
                    return redirect(f"/home")

            # The users details are not correct.
            flash("Email or password is incorrect.", category="error")

    # Called by the GET method, or the POST method if users details are incorrect.
    return render_template("login/loginBasicBuild.html")


@app.route("/signup", methods=("POST", "GET"))
def signup_page():
    """
    This is the signup page for this website.
    You use this page to create an account.
    """
    current_time = CurrentDate()

    # The post method is used by the page to send information to the server.
    #   In this instance we'll be checking for user signup details.
    if request.method == "POST":

        # Removes all flash messages.
        session.pop('_flashes', None)

        # Gets the form data from the post.
        form = request.form.to_dict()

        # For whatever reason a form wasn't present.
        if not form:
            return render_template("login/customerSignUp.html")

        # Makes sure all items are present in from data.
        items_in_form = ("fname", "lname", "phone", "DoB", "address", "postcode", "email", "pswd")
        if any(x not in form for x in items_in_form):
            return render_template("login/customerSignUp.html")

        passed_initial = True

        # Checks that a valid email address has been entered.
        if not validators.email(form["email"]):
            flash(message="You need to enter a valid email.", category="error")
            passed_initial = False

        # Checks a first name has been entered.
        if not form["fname"]:
            flash(message="You need to enter a first name.", category="error")
            passed_initial = False

        # Check a last name has been entered.
        if not form["lname"]:
            flash(message="You need to enter a last name.", category="error")
            passed_initial = False

        # Check a password has been entered.
        if not form["pswd"]:
            flash(message="You need to enter a password.", category="error")
            passed_initial = False

        # Check an address has been entered.
        if not form["address"]:
            flash(message="You need to enter a address.", category="error")
            passed_initial = False

        # Check a postcode has been entered.
        if not form["postcode"]:
            flash(message="You need to enter a postcode.", category="error")
            passed_initial = False

        # Check a date of birth has been entered.
        if not form["DoB"]:
            flash(message="You need to enter your date of birth.", category="error")
            passed_initial = False

        # Makes sure all checks have passed.
        if not passed_initial:
            return render_template("login/customerSignUp.html", code=400, current_time=current_time)

        # At this point, all initial checks should have passed, now
        #   starting to perform form data checks.

        # Tries to find a user, this is to make sure someone with that
        #   email address isn't already taken.
        user = Users.query.filter_by(email=form["email"]).first()

        # A user with that email already exists.
        if user:
            flash(message="An account with that email address already exists.", category="error")
            return render_template("login/customerSignUp.html", code=400, current_time=current_time)

        # An account `can` be created. But the user should be of age first.
        year, month, day = form["DoB"].split("-")
        dob = datetime(year=int(year), month=int(month), day=int(day))

        # Checks if the user is older than 18.
        if check_age(dob) < 18:
            flash(message="Must be 18+ years old.", category="error")
            return render_template("login/customerSignUp.html", code=400, current_time=current_time)

        # The checks have been passed. A new account can now be created.
        pswd = SALT + form["pswd"]

        # Creates a new user object for the database.
        new_user = Users(
            name=f"{form['fname']} {form['lname']}",
            email=form["email"],
            password=generate_password_hash(pswd, "sha256"),
            postcode=form["postcode"],
            address=form["address"],
            number=form["phone"] if form["phone"] else None,
            dob=dob
        )

        # Calls the function to add the new user to the database then redirects the user to the login page.
        add_new_user(new_user)
        flash(message="Created new account.", category="success")
        return redirect("/login")

    return render_template("login/customerSignUp.html", current_time=current_time)


@app.route("/home", methods=("GET",))
@login_required
def home_page():
    """
    This is the homepage of the frackhub, the user should be logged in to reach this page.
    """
    return render_template("menu/FrackHubMenu.html", employee=display_employee())


@app.route("/my_items", methods=("GET", "POST"))
@login_required
def my_items_page():
    """
    The user should be logged in to view this.
    A page to list all the users items.
    """
    items = [x for x in current_user.items]

    # Sets the variables to be used by the html template.
    for item in items:
        item.has_orders = False
        for order in item.orders:
            if not order.responded:
                user = Users.query.get(order.requester_id)
                order.requester = user
                item.has_orders = True

    return render_template("menu/MyItems.html", employee=display_employee(), user=current_user, items=items)


@app.route("/employee", methods=("GET", "POST"))
@login_required
def employee_page():
    """
    A private page for employees and administrators.
    """
    def check_user(_user_id_):
        _user_ = Users.query.get(int(_user_id_))
        if _user_ is not None and _user_:
            return _user_
        else:
            return False

    if current_user.user_type == UserType.NORMAL:
        return redirect("/home")

    new_accounts = [x for x in Users.query.filter(Users.verified == 0).all()]
    existing_accounts = []

    # If the user is an admin, get listing for staff and normal users.
    if current_user.user_type == UserType.ADMIN:
        existing_accounts = [x for x in Users.query.filter(
            Users.verified == 1
        ).filter(
            (Users.user_type == UserType.NORMAL) | (Users.user_type == UserType.STAFF)
        ).all()]

    # If user is staff, get listing for normal users only.
    elif current_user.user_type == UserType.STAFF:
        existing_accounts = [x for x in Users.query.filter(
            Users.verified == 1
        ).filter(
            Users.user_type == UserType.NORMAL
        ).all()]

    # The staff or admin member is modifying user statuses.
    if request.method == "POST":
        form_data = request.form.to_dict()

        # A user has been declined access to the website.
        if "decline" in form_data:
            user = check_user(form_data["decline"])
            if not user:
                flash("User not found in database.", "error")
            else:
                db.session.delete(user)
                db.session.commit()
                flash("Deleted user.", "success")
                new_accounts.remove(user)

        # A user has been allowed to use the website.
        elif "accept" in form_data:
            user = check_user(form_data["accept"])
            if not user:
                flash("User not found in database.", "error")
            else:
                user.verified = 1
                db.session.commit()
                flash("User has been verified.", "success")
                new_accounts.remove(user)
                existing_accounts.append(user)

        # A user has been elevated to employee status.
        elif "make_employee" in form_data:
            if current_user.user_type != 2:
                flash("Only an administrator can use this.", "error")
            else:
                user = check_user(form_data["make_employee"])
                if not user:
                    flash("User not found in database.", "error")
                else:
                    user.user_type = UserType.STAFF
                    db.session.commit()
                    flash("User is now a staff member.", "success")

        # A user has had their employee status removed.
        elif "disable_employee" in form_data:
            if current_user.user_type != 2:
                flash("Only an administrator can use this.", "error")
            else:
                user = check_user(form_data["disable_employee"])
                if not user:
                    flash("User not found in database.", "error")
                else:
                    user.user_type = UserType.NORMAL
                    db.session.commit()
                    flash("User staff privileges has been revoked.", "success")

        # A normal user is getting suspended.
        elif "suspend" in form_data and "user" in form_data:
            user = check_user(form_data["user"])
            if not user:
                flash("User not found in database.", "error")
            else:
                if user.user_type == 1:
                    flash("Cannot suspend an employee.", "error")
                elif user.user_type == 2:
                    flash("Cannot suspend an admin.", "error")
                else:
                    year, month, day = form_data["suspend"].split("-")
                    sus_time = datetime(year=year, month=month, day=day)
                    user.suspended = sus_time
                    db.session.commit()
                    flash(f"User has been suspended until "
                          f"{sus_time.day}/{sus_time.month}/{sus_time.year}.", "success")

        else:
            flash("Error parsing form data.", "error")

    return render_template("menu/Employee.html", employee=display_employee(),
                           existing_accounts=existing_accounts,
                           new_accounts=new_accounts,
                           current_user=current_user,
                           current_time=CurrentDate(True))


@app.route("/item/<ITEM_ID>/", methods=("GET", "POST"))
@login_required
def view_item_page(ITEM_ID: int):
    """
    A page to display information about a specific item.

    parameters
    ----------
    ITEM_ID :class:`int`
        The ID of the item in the database.
    """

    # Checks to see if the item exists.
    item = Items.query.get(int(ITEM_ID))
    if not item or item is None:
        return render_template("menu/ItemView.html", employee=display_employee(), exists=0)

    # At the moment this shouldn't happen. Just a failsafe for when users are able to delete their accounts.
    user = Users.query.get(int(item.user_id))
    if not user or user is None:
        return render_template("menu/ItemView.html", employee=display_employee(), exists=0)

    rating = None
    renting_user = False

    # Gets the info on the person renting the item currently.
    if item.rented:
        order = Orders.query.get(item.order)

        if order is not None and order:
            renting_user = Users.query.get(order.requester_id)

    # The item has ratings, starts to calculate the items overall rating.
    if item.ratings:
        total = 0
        count = 0

        for x in item.ratings:
            total += x
            count += 1

        rating = round(total / count, 1)

    return render_template("menu/ItemView.html", employee=display_employee(), exists=1,
                           item=item, rating=rating, user=user, current_user=current_user,
                           img_url=f"/item/{ITEM_ID}/image", renting_user=renting_user)


@app.route("/item/<ITEM_ID>/image", methods=("GET",))
@login_required
def get_item_image(ITEM_ID: int):
    """
    Retrieves a none static image.
    """
    item = Items.query.get(int(ITEM_ID))
    if not item or item is None:
        return ""

    return send_from_directory(directory=os.getcwd(), path=item.image)


@app.route("/item/<ITEM_ID>/small_image", methods=("GET",))
@login_required
def get_item_small_image(ITEM_ID: int):
    """
    Retrieves a none static image.
    """
    item = Items.query.get(int(ITEM_ID))
    if not item or item is None:
        return ""

    return send_from_directory(directory=os.getcwd(), path=item.small_image)


@app.route("/renting_items", methods=("GET", "POST"))
@login_required
def renting_items_page():
    """
    A page to display items the current user is renting from other users.
    """
    # Retrieves all accepted orders from the user.
    orders = Orders.query.filter(
        Orders.requester_id == current_user.id
    ).filter(
        Orders.responded == 1
    ).filter(
        Orders.accepted == 1
    ).all()

    items = []

    # Adds all items to a list that the user is currently renting.
    for x in orders:
        item = Items.query.get(x.item_id)

        # Statements to ignore the item.
        if item in items:
            continue
        elif not item.rented:
            continue
        elif x.id != item.order:
            continue

        items.append(item)

    # The user is returning the item.
    if request.method == "POST":

        # Makes sure the user is verified
        if not current_user.verified:
            flash("You're not verified yet.", "error")
            return render_template("menu/MyItemsRented.html", employee=display_employee(),
                                   items=items, user=current_user), 401

        form_data = request.form.to_dict()

        # The only value we need.
        if "return" in form_data:
            item = Items.query.get(int(form_data["return"]))

            if item is not None and item in items:
                items.remove(item)

                # Sets the item values back to nothing.
                item.rented = 0
                item.order = None
                db.session.commit()

                flash(f"Returned {item.name}.", "success")

    return render_template("menu/MyItemsRented.html", employee=display_employee(),
                           items=items, user=current_user)


@app.route("/confirm_order/<ORDER_ID>", methods=("GET", "POST"))
@login_required
def confirm_order_page(ORDER_ID: int):
    """
    A page to confirm an order for an item requested from other users.
    """
    order = Orders.query.get(int(ORDER_ID))

    # Makes sure the order exists.
    if order is None or not order:
        flash("Order does not exist.", "error")
        return redirect("/home")

    # The order has already been responded to, cannot change response.
    if order.responded:
        flash("Order has already been responded to.", "error")
        return redirect("/home")

    # Makes sure the item exists.
    item = Items.query.get(order.item_id)
    if item is None or not item:
        flash("Item does not exist.", "error")
        return redirect("/home")

    # Makes sure the item is the users to accept.
    if item.user_id != current_user.id:
        flash("You do not own that item.", "error")
        return redirect("/home")

    # Makes sure the user still exists.
    requester = Users.query.get(order.requester_id)
    if requester is None or not requester:
        flash("Requesting user no longer exists.", "error")
        return redirect("/home")

    # Requester does not have enough to pay for item.
    if requester.credits < item.price:
        flash("Requesting user does not have enough credits.", "error")
        return redirect("/home")

    # If the user is responding to the order.
    if request.method == "POST":

        form_data = request.form.to_dict()

        # Makes sure the user is verified
        if not current_user.verified:
            flash("You're not verified yet.", "error")
            return render_template("menu/OrderConfimration.html", employee=display_employee(),
                                   item=item, requester=requester, order=order), 401

        # Makes sure the field we need is in the form data.
        if "response" in form_data:

            # User has declined the request.
            if "dec" == form_data["response"]:
                order.responded = 1
                order.accepted = 0
                db.session.commit()

            elif "acc" == form_data["response"]:
                complete_accept_order(item, current_user, requester, order)
                flash("Accepted order.", "success")
                return redirect("/my_items")

    return render_template("menu/OrderConfimration.html", employee=display_employee(),
                           item=item, requester=requester, order=order)


@app.route("/search_items", methods=("GET", "POST"))
@login_required
def search_items_page():
    """
    A page to search for items to rent.
    """
    result = list(Items.query.filter(Items.rented == 0).all())

    # Fetches all the unanswered orders.
    orders = list(Orders.query
                  .filter(Orders.requester_id == current_user.id)
                  .filter(Orders.responded == 0).all())
    orders = [x.item_id for x in orders]

    # A list to be used to remove items to display.
    to_remove = []

    # Selects only items the user is able to rent.
    #   Avoids repeat unanswered orders.
    for item in result:
        if item.user_id == current_user.id:
            to_remove.append(item)

        elif item.id in orders:
            to_remove.append(item)

    # Removes the items here.
    for item in to_remove:
        result.remove(item)

    # Only used if the user is requesting an item.
    if request.method == "POST":

        # Removes all flash messages.
        session.pop('_flashes', None)

        # The only thing we need from this form is the item.
        form_data = request.form.to_dict()

        # Makes sure the user is verified
        if not current_user.verified:
            flash("You're not verified yet.", "error")
            return render_template("menu/SearchItems.html", employee=display_employee(),
                                   user=current_user, items=result), 401

        if "search" in form_data:
            words = [f"%{x}%" for x in form_data["search"].split()]
            items = []

            for word in words:
                query_result1 = Items.query.filter(Items.description.like(word)).all()
                query_result2 = Items.query.filter(Items.name.like(word)).all()
                final_result = list(set([x for x in query_result1] + [x for x in query_result2]))
                items = list(set(items + final_result))

            result = items[:]
            del items

        if "item" in form_data:
            item = Items.query.get(int(form_data["item"]))

            if item is not None and item:
                if item in current_user.items:
                    flash("You own this item.", "error")
                elif item.price > current_user.credits:
                    flash("You don't have enough credits.", "error")
                else:
                    rent_error = False

                    if item.rented:

                        # Makes sure the user isn't already renting the item.
                        order = Orders.query.get(item.order)
                        if order is not None and order:
                            if order.requester_id == current_user.id:
                                flash("You're already renting this item.", "error")
                                rent_error = True

                    # Makes sure the user hasn't already got a pending order
                    order = Orders.query.filter(
                        Orders.item_id == item.id
                    ).filter(
                        Orders.requester_id == current_user.id
                    ).filter(
                        Orders.responded == 0
                    ).first()

                    if order is not None or order:
                        flash("You already have a pending request for this item.", "error")

                    # A new order can be made.
                    elif not rent_error:
                        new_order = Orders(
                            item_id=item.id,
                            requester_id=current_user.id
                        )
                        add_new_offer(new_order)
                        result.remove(item)
                        flash("Successfully made offer request.", "success")

    return render_template("menu/SearchItems.html", employee=display_employee(),
                           user=current_user, items=result)


@app.route("/add_item", methods=("GET", "POST"))
@login_required
def add_item_page():
    """
    A page to add an item to your list of items.
    """

    # The user is trying to add an item.
    if request.method == "POST":
        # Removes all flash messages.
        session.pop('_flashes', None)

        form_info = request.form.to_dict()

        if not current_user.verified:
            flash("You are not verified.", "error")
            return render_template("menu/UploadItems.html", employee=display_employee()), 401

        # Makes sure all items are present in from data.
        items_in_form = ("Price", "name", "description")
        if any(x not in form_info for x in items_in_form):
            return render_template("menu/UploadItems.html", employee=display_employee())

        initial_check = True

        if not form_info["Price"]:
            flash("You need to specify a price.", "error")
            initial_check = False

        if not form_info["name"]:
            flash("You need to specify a name.", "error")
            initial_check = False

        if not form_info["description"]:
            flash("You need to add an item description.")
            initial_check = False

        if not request.files:
            flash("You need to add an image, preferably one of the item you're advertising.", "error")
            initial_check = False

        # The initial checks have failed.
        if not initial_check:
            return render_template("menu/UploadItems.html", employee=display_employee())

        # Makes sure data, info about the image was uploaded.
        #   this helps avoid future possible errors.
        file_info = request.files.get("img")
        if file_info is None:
            return render_template("menu/UploadItems.html", employee=display_employee())

        # Makes sure the correct type of image was uploaded.
        if file_info.mimetype.lower() not in accepted_mime_types:
            flash("Incorrect image type, use jpeg, jpg or png only!", "error")
            return render_template("menu/UploadItems.html", employee=display_employee())

        # If the file somehow managed to get past the built-in max content length.
        if file_info.content_length > max_content_length:
            flash("File is too large. 8MB is the limit.", "error")
            return render_template("menu/UploadItems.html", employee=display_employee())

        # Saves the image info, returns the filedir and name.
        file_name, small_file_name = save_image(file_info)

        # Creates and adds the new item to the database here.
        new_item = Items(
            name=form_info["name"],
            user_id=current_user.id,
            description=form_info["description"],
            image=file_name,
            small_image=small_file_name,
            price=int(form_info["Price"])
        )
        add_new_item(new_item)
        flash("Successfully created new item.", "success")

        # Redirects user to newly created item.
        return redirect(f"/item/{new_item.id}")

    return render_template("menu/UploadItems.html", employee=display_employee())


@app.errorhandler(413)
def request_entity_too_large(error):
    return "<h1>FILE TO LARGE! 8MB is the limit.</h1>" \
           f"<h3><a href=\"{request.path}\">Return</a></h3>", 413


if __name__ == "__main__":
    app.run(debug=True)
