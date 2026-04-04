from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.filter_by(username='admin_demo').first()
    if not u:
        u = User(username='admin_demo', email='demo@example.com', role='admin')
        u.password = 'admin123'
        db.session.add(u)
        db.session.commit()
        print('Demo user created')
    else:
        print('Demo user already exists')
