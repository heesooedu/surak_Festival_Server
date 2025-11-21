import os
from flask import Flask
from .extensions import db, login_manager
from .models import Student, AdminUser, Booth
from .auth import auth_bp
from .views import main_bp
from .admin import admin_bp
from .cli import register_cli


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_secret_key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///festival.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", os.path.join(app.root_path, "static", "img")),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    register_cli(app)

    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    role, _, raw_id = user_id.partition(":")
    if role == "student":
        return Student.query.get(int(raw_id))
    if role == "admin":
        return AdminUser.query.get(int(raw_id))
    return None
