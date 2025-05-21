from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates/volt_dashboard')

from . import routes  # nanti import routes auth biar route terdaftar
