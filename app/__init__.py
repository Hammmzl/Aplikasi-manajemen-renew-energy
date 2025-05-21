from flask import Flask
from app.extensions import db, login_manager
from app.main.routes import main_bp
from flask_migrate import Migrate

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:19desember2000@localhost/minyak_jelantah_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_object('app.config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)

    from .models import User # pastikan models di-import

    # Import blueprint di sini supaya extensions sudah diinisialisasi duluan
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
