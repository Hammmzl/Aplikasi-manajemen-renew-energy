from flask import Blueprint

client_bp = Blueprint('client', __name__, url_prefix='/client')

from . import routes  # import routes agar route terdaftar
