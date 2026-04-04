from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if not current_user.is_admin:
            flash('Akses hanya untuk admin.', 'danger')
            return redirect(url_for('main.index'))

        return view_func(*args, **kwargs)

    return wrapped_view
