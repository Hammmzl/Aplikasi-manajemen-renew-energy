from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from .forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('volt_dashboard/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Berhasil logout!', 'success')
    return redirect(url_for('auth.login'))



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.password = form.password.data
        db.session.add(new_user)
        db.session.commit()

        flash('Registrasi berhasil, silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('volt_dashboard/register.html', form=form)


@auth_bp.route('/users')
@login_required
def user_list():
    users = User.query.all()
    return render_template('volt_dashboard/user_list.html', users=users)
