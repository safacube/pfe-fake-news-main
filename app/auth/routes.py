from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from bson import ObjectId

from ..models.user import User


auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
        existing = db.users.find_one({'email': email})
        if existing:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('auth.login'))

        user_id = str(ObjectId())
        password_hash = User.hash_password(password)
        db.users.insert_one({'_id': user_id, 'email': email, 'password_hash': password_hash})
        user = User(id=user_id, email=email, password_hash=password_hash)
        login_user(user)
        flash('Registration successful. Welcome!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        db = current_app.mongo_client[current_app.config['MONGO_DB_NAME']]
        doc = db.users.find_one({'email': email})
        user = User.from_document(doc)
        if not user or not user.verify_password(password):
            flash('Invalid credentials.', 'error')
            return render_template('login.html')

        login_user(user)
        flash('Logged in successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.landing'))
