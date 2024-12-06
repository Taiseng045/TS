from . import db
from flask_login import UserMixin
from sqlalchemy import func
# from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    fname = db.Column(db.String(150))
    lname = db.Column(db.String(150))
    role = db.Column(db.String(20), nullable=False)
    # make connection

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each cart item
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to User model
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)  # Link to Product model
    quantity = db.Column(db.Integer, nullable=False)  # Quantity of the product
    # Relationships
    user = db.relationship('User', backref='cart_items', lazy=True)  # Link Cart to User
    product = db.relationship('Product', lazy=True) 

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)  # Store product name
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Shipped, Complete, Canceled
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())

    user = db.relationship('User', backref='orders')
    product = db.relationship('Product', backref='orders')