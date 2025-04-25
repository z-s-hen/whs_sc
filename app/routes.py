from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db, bcrypt
from app.models import User, Item, BlockList, Transaction
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import RegisterForm, LoginForm, ItemForm
from flask_socketio import emit, join_room
from app import socketio

main = Blueprint('main', __name__)

@main.route('/')
def home():
    items = Item.query.all()
    return render_template('home.html', items=items)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            flash('Login failed.', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route('/post', methods=['GET', 'POST'])
@login_required
def post_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(name=form.name.data, description=form.description.data, price=form.price.data, user_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('main.home'))
    return render_template('post_item.html', form=form)

@main.route('/block/<int:user_id>')
@login_required
def block_user(user_id):
    if user_id != current_user.id:
        block = BlockList(blocker_id=current_user.id, blocked_id=user_id)
        db.session.add(block)
        db.session.commit()
        flash('User blocked.', 'info')
    return redirect(url_for('main.home'))

@main.route('/send/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_money(user_id):
    if request.method == 'POST':
        amount = float(request.form['amount'])
        tx = Transaction(sender_id=current_user.id, receiver_id=user_id, amount=amount)
        db.session.add(tx)
        db.session.commit()
        flash('Payment sent (mock).', 'success')
        return redirect(url_for('main.home'))
    return render_template('send_money.html', user_id=user_id)

@main.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Admins only.', 'danger')
        return redirect(url_for('main.home'))
    users = User.query.all()
    items = Item.query.all()
    txs = Transaction.query.all()
    return render_template('admin.html', users=users, items=items, txs=txs)

@main.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'msg': f"{data['username']} has entered the room."}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    emit('message', {'msg': f"{data['username']}: {data['msg']}"}, room=room)