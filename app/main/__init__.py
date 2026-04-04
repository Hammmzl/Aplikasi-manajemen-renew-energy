from flask import Blueprint

main_bp = Blueprint('main', __name__, template_folder='templates/volt_dashboard')

from app.main import routes
