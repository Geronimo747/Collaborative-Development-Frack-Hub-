from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from enum import IntEnum
from datetime import datetime

# Creates the database instance
db = SQLAlchemy()


class UserType(IntEnum):
    NORMAL = 0
    STAFF = 1
    ADMIN = 2


class TransactionType(IntEnum):
    IN = 0
    OUT = 1


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    user_type = db.Column(db.Integer, nullable=False, default=0)
    items = db.relationship("Items", backref="items", lazy=True)
    transactions = db.relationship("Transactions", backref="user_transactions", lazy=True)
    dob = db.Column(db.DateTime, nullable=False)
    join_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    address = db.Column(db.String(255), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)
    number = db.Column(db.String(15))
    suspended = db.Column(db.DateTime)
    ratings = db.relationship("Ratings", backref="user_ratings", lazy=True)
    credits = db.Column(db.Integer, nullable=False, default=100)
    verified = db.Column(db.Boolean, nullable=False, default=0)


class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(527), nullable=False)                     # The image file location.
    small_image = db.Column(db.String(527), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rented = db.Column(db.Boolean, default=0, nullable=False)
    order = db.Column(db.Integer)           # ID of the current renting order.
    orders = db.relationship("Orders", backref="orders", lazy=True)     # All orders relating to this item.
    added_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ratings = db.relationship("Ratings", backref="item_ratings", lazy=True)
    rent_count = db.Column(db.Integer, nullable=False, default=0)
    transactions = db.relationship("Transactions", backref="item_transactions", lazy=True)


class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    transaction_type = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    responded = db.Column(db.Boolean, default=0, nullable=False)
    accepted = db.Column(db.Boolean, default=0, nullable=False)


class Ratings(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
