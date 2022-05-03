from flask import Flask, render_template, redirect, request, flash, \
    send_file, url_for, session, send_from_directory

from .models import db, Users, Items, Orders, Transactions, TransactionType, UserType
import os
from datetime import datetime, timedelta
from hashlib import sha512
import subprocess

__all__ = ("create_app", "Users", "Items", "render_template",
           "redirect", "request", "flash", "add_new_user", "send_file",
           "url_for", "add_new_item", "Orders", "add_new_offer", "db",
           "session", "check_age", "CurrentDate", "save_image",
           "send_from_directory", "os", "complete_accept_order",
           "UserType")


def create_app():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    cwd = os.getcwd()

    # Makes sure the current working directory is correct.
    assert current_dir == f"{cwd}\\App" or current_dir == f"{cwd}/App"

    _app = Flask(__name__, static_folder=f"{current_dir}/static", template_folder=f"{current_dir}/templates")
    _app.config["SECRET_KEY"] = "THIS_IS_A_SECRET"  # TODO: This would need to be changed.

    # Sets the database to use.
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
    db.init_app(_app)

    return _app


class CurrentDate:
    """
    To be used to create a max date for html date fields.
    """
    __slots__ = ("current_time",)

    def __init__(self, next_day=False):
        if next_day:
            self.current_time = datetime.now()
            self.current_time += timedelta(days=1)

        else:
            self.current_time = datetime.now()

    @property
    def day(self):
        day_str = str(self.current_time.day)
        if len(day_str) == 1:
            return f"0{day_str}"
        return day_str

    @property
    def max_year(self):
        return str(self.current_time.year)

    @property
    def min_year(self):
        return str(self.current_time.year - 100)

    @property
    def month(self):
        month_str = str(self.current_time.month)
        if len(month_str) == 1:
            return f"0{month_str}"
        return month_str


def save_image(content, size=200) -> tuple:
    """
    Uses the file info from the POST request to create a
    unique save location and name.
    """
    # Cannot size image properly, keeps running into error.
    #   Forces the database to return the error.
    if size == 129:
        return None, None

    # Converts mimetypes to files extensions.
    mime_types = {"image/png": ".png",
                  "image/jpeg": ".jpeg",
                  "image/jpg": ".jpg"}

    # Used for ffmpeg pipe conversions.
    ffm_pipes = {
        "image/jpg": "jpeg_pipe",
        "image/jpeg": "jpeg_pipe",
        "image/png": "png_pipe"
    }

    # Makes sure the desired target directory exists.
    current_date = datetime.now()
    target_dir = f"images/{current_date.year}/{current_date.month}/{current_date.day}"
    os.makedirs(name=f"{os.getcwd()}/{target_dir}", exist_ok=True)

    # Uses the files sha512 as the filename to make it nearly impossible for collision.
    #   Also saves the file in a directory leading to todays date.
    file_data = content.stream.read()
    file_hash = sha512(file_data).hexdigest()
    file_name = f"{file_hash}{mime_types[content.mimetype.lower()]}"

    # Creates the subprocess and subprocess command to shrink the image.
    ffm_command = f"ffmpeg -v error -f {ffm_pipes[content.mimetype.lower()]} " \
                  f"-i - -vf scale=-1:{size} -f image2pipe -"
    proc = subprocess.Popen(ffm_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)

    output, error = proc.communicate(input=file_data)

    # If there is an error, tries again but with a smaller size.
    if error:
        proc.kill()
        content.stream.seek(0)
        return save_image(content, size - 1)

    proc.terminate()

    small_file_name = f"{file_hash}-small-{mime_types[content.mimetype.lower()]}"
    small_file_info = f"{target_dir}/{small_file_name}"

    with open(f"{os.getcwd()}/{small_file_info}", "wb") as f_:
        f_.write(output)

    full_file_info = f"{target_dir}/{file_name}"

    with open(f"{os.getcwd()}/{full_file_info}", "wb") as f_:
        f_.write(file_data)

    return full_file_info, small_file_info


def complete_accept_order(item, user, requester, order):
    # Sorts the item and order information
    item.rented = 1
    item.order = order.id
    item.rent_count += 1

    order.accepted = 1
    order.responded = 1

    # Completes the `transaction` of the request
    requester.credits = requester.credits - item.price
    user.credits += item.price

    db.session.commit()

    add_new_transaction(
        Transactions(
            user_id=requester.id,
            transaction_type=TransactionType.OUT,
            amount=item.price,
            item_id=item.id,
        ))

    add_new_transaction(
        Transactions(
            user_id=user.id,
            transaction_type=TransactionType.IN,
            amount=item.price,
            item_id=item.id,
        ))


def add_new_transaction(transaction: Transactions):
    db.session.add(transaction)
    db.session.commit()


def check_age(dob: datetime):
    current_time = datetime.now()
    result = current_time.year - dob.year - ((current_time.month, current_time.day) < (dob.month, dob.day))
    return result


def add_new_user(new_user: Users):
    db.session.add(new_user)
    db.session.commit()


def add_new_item(new_item: Items):
    db.session.add(new_item)
    db.session.commit()


def add_new_offer(new_offer: Orders):
    db.session.add(new_offer)
    db.session.commit()
