from flask import Flask
from app.extensions import csrf, db, login_manager
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.main.utils import format_quantity


load_dotenv()  # <-- ini wajib buat load .env ke os.environ
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    app.jinja_env.filters['format_quantity'] = format_quantity

    # Import semua model di sini biar migrate bisa detect
    from app import models  # noqa: F401

    # Import blueprint dari package (sudah didefinisikan di __init__.py masing-masing)
    from app.main import main_bp
    from app.auth import auth_bp
    from app.client import client_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(client_bp)

    return app
