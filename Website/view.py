from flask import Blueprint, render_template,request,flash,jsonify,redirect,url_for,session
from flask_login import login_required,current_user
from .models import Product,User,Cart,Order
from . import db
from flask_login import login_user, login_required,logout_user,current_user
import os
import json
from . import db
from flask_mail import Message
from flask import current_app as app
from . import mail
views = Blueprint('views', __name__)
# define when it a / it is routed to home
@views.route('/')
@login_required
def home():
    products = Product.query.all()
    return render_template('home.html',user= current_user,products=products)
@views.context_processor
@login_required
def cart_count():
    # user_id = 1  # Replace with your logged-in user's ID
    cart_count = db.session.query(db.func.sum(Cart.quantity)).filter(Cart.user_id == current_user.id).scalar()
    return {'cart_count': cart_count or 0}

@views.route('/admin/delete',methods=['POST'])
def deletePro():
    product = json.loads(request.data)
    productID = product['productID']
    product = Product.query.get(productID)
    if product:
        if current_user.role == "admin":
            db.session.delete(product)
            db.session.commit()
    return jsonify({})

# -================================ Cart =================================
@views.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # user_id = session['User.id']  # User is already logged in
    # Fetch product from the database
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found!", "error")
        return redirect(url_for('views.home'))

    # Check if the product is already in the cart
    existing_cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_cart_item:
        # Update the quantity
        existing_cart_item.quantity += 1
    else:
        # Add a new item to the cart
        new_cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(new_cart_item)

    db.session.commit()
    flash(f"{product.name} added to your cart!", "success")
    return redirect(url_for('views.home'))
@views.route('/view_cart')
def view_cart():
     # User is logged in

    # Retrieve cart items for the logged-in user
    cart_items = db.session.query(Cart, Product).join(Product).filter(Cart.user_id == current_user.id).all()

    # Calculate the total price of the items in the cart
    total_price = sum(item.Cart.quantity * item.Product.price for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

# ==========================Check out ==============================

@views.route('/checkout', methods=['POST'])
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    for item in cart_items:
        product = Product.query.get(item.product_id)
        product.stock -= item.quantity
        if product.stock < 0:
            flash(f"Not enough stock for {product.name}.", "error")
            return redirect(url_for('views.view_cart'))
        order = Order(
            user_id=current_user.id,
            product_id=product.id,
            product_name=product.name,
            product_price=product.price,
            quantity=item.quantity,
            total_price=item.quantity * product.price,
            status='Pending'
        )
        db.session.add(order)
    db.session.commit()
    send_checkout_email(current_user, cart_items)
    # Clear the cart after successful checkout
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash("Checkout successful!.", "success")
    return redirect(url_for('views.home'))
def send_checkout_email(user, cart_items):
    msg = Message(
        subject="Order Confirmation",
        sender='Example@gmail.com',
        recipients=[user.email, 'Example@gmail.com'],  # Customer and Admin email
        reply_to=user.email
    )
    msg.body = f"""
    Dear {user.fname},

    Your order has been placed successfully.

    Order Summary:
    - User: {user.email}
    - Items: {', '.join([item.product.name for item in cart_items])}

    Regards,
    Your Store Team
    """

    # Send the email
    mail.send(msg)
@views.route('/view_cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    # Get the new quantity from the form
    quantity = int(request.form['quantity'])

    # Find the cart item for the current user and product
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if cart_item:
        if quantity > 0:
            cart_item.quantity = quantity  # Update the quantity
            db.session.commit()
            flash(f"Quantity updated to {quantity}.", "success")
        else:
            flash("Quantity must be at least 1.", "error")
    else:
        flash("Item not found in your cart.", "error")

    return redirect(url_for('views.view_cart'))

@views.route('/view_cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    # Find the cart item for the current user and product
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if cart_item:
        db.session.delete(cart_item)  # Remove the item from the cart
        db.session.commit()
        flash("Item removed from your cart.", "success")
    else:
        flash("Item not found in your cart.", "error")

    return redirect(url_for('views.view_cart'))

# ==============================check order and check History =================

@views.route('/admin/orders', methods=['GET'])
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    return render_template('admin_orders.html', orders=orders)
@views.route('/admin/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    new_status = request.form['status']
    order = Order.query.get_or_404(order_id)

    # Send email notification
    send_order_update_email(order.user, order, new_status)

    if new_status in ['Complete', 'Canceled']:
        # Move to history if completed or canceled
        order.status = new_status
        db.session.commit()
    else:
        # Update order status
        order.status = new_status

    db.session.commit()
    flash(f"Order #{order.id} updated to {new_status}.", "success")
    return redirect(url_for('views.admin_orders'))
def send_order_update_email(user, order, new_status):
    msg = Message(
        subject="Order Update Notification",
        sender='Example@gmail.com',
        recipients=[user.email],  # Customer
        reply_to=user.email
    )
    msg.body = f"""
    Dear {user.fname},

    Your order for {order.product_name} has been updated.
    Status: {new_status}

    Thank you for shopping with us!

    Regards,
    Your Store Team
    """
    mail.send(msg)


@views.route('/history', methods=['GET'])
@login_required
def user_history():
    history = Order.query.filter_by(user_id=current_user.id).order_by(Order.timestamp.desc()).all()
    return render_template('user_history.html', history=history)
