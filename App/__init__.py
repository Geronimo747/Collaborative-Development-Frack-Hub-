from flask import Flask, render_template, redirect, request, flash
from .models import db, User, Item
import os


__all__ = ("create_app", "User", "Item", "render_template",
           "redirect", "request", "flash", "add_new_user")


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


def add_new_user(new_user: User):
    db.session.add(new_user)
    db.session.commit()

