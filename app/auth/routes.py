from flask import flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from app.models import User
from app.extensions import db
from app.auth.decorators import admin_required
from app.auth import auth_bp
from .forms import LoginForm, RegisterForm


def _public_registration_open():
    return User.query.count() == 0


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.username) == form.username.data.lower()).first()
        if user and user.is_active and user.verify_password(form.password.data):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('main.index'))
        flash('Username atau password salah.', 'danger')

    return render_template(
        'volt_dashboard/login.html',
        form=form,
        allow_registration=_public_registration_open(),
    )


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Berhasil logout!', 'success')
    return redirect(url_for('auth.login'))



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    public_registration_open = _public_registration_open()

    if not public_registration_open:
        if not current_user.is_authenticated:
            flash('Registrasi akun baru hanya bisa dilakukan oleh admin.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Hanya admin yang dapat menambahkan user baru.', 'danger')
            return redirect(url_for('main.index'))

    form = RegisterForm()
    can_assign_role = current_user.is_authenticated and current_user.is_admin

    if public_registration_open:
        form.role.data = 'admin'
    elif not can_assign_role:
        form.role.data = 'user'

    if form.validate_on_submit():
        existing_user = User.query.filter(func.lower(User.username) == form.username.data.lower()).first()
        if existing_user:
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('auth.register'))

        existing_email = User.query.filter(func.lower(User.email) == form.email.data.lower()).first()
        if existing_email:
            flash('Email sudah digunakan.', 'danger')
            return redirect(url_for('auth.register'))

        role = 'admin' if public_registration_open else form.role.data
        if role not in User.ALLOWED_ROLES:
            role = 'user'

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=role,
        )
        new_user.password = form.password.data
        db.session.add(new_user)
        db.session.commit()

        if current_user.is_authenticated:
            flash('User baru berhasil ditambahkan.', 'success')
            return redirect(url_for('auth.user_list'))

        flash('Registrasi berhasil, silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template(
        'volt_dashboard/register.html',
        form=form,
        can_assign_role=can_assign_role,
        public_registration_open=public_registration_open,
    )


@auth_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('volt_dashboard/user_list.html', users=users)


@auth_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get('role', 'user')

    if role not in User.ALLOWED_ROLES:
        flash('Level user tidak valid.', 'danger')
        return redirect(url_for('auth.user_list'))

    if user.id == current_user.id and role != 'admin':
        flash('Admin yang sedang login tidak bisa menurunkan level dirinya sendiri.', 'warning')
        return redirect(url_for('auth.user_list'))

    user.role = role
    db.session.commit()
    flash('Level user berhasil diperbarui.', 'success')
    return redirect(url_for('auth.user_list'))
