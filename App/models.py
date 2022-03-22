from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


# Creates the database instance
db = SQLAlchemy()


# The items users use to rent
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.String(255))
    image = db.Column(db.Text())
    price = db.Column(db.Integer, nullable=False)
    is_rented = db.Column(db.Boolean(), nullable=False, default=0)
    offers = db.relationship("Offers", backref="offers", lazy=True)


# The user database model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    items = db.relationship("Item", backref="items", lazy=True)
    requests = db.relationship("Offers", backref="requests", lazy=True)


class Rented(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id"), nullable=False)
    returned = db.Column(db.Boolean(), nullable=False, default=0)


# Table for offers concerning the items
class Offers(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    answered = db.Column(db.Boolean(), nullable=False, default=False)
    rent_status = db.relationship("Rented", backref="rent", lazy=True)
