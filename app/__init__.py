from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import json
import os
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Jinja Filters
    @app.template_filter('from_json')
    def from_json(val):
        try:
            return json.loads(val)
        except Exception:
            return []

    @app.template_filter('basename')
    def get_basename(path):
        return os.path.basename(path)

    # Register Blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.patient import bp as patient_bp
    app.register_blueprint(patient_bp, url_prefix='/patient')

    from app.doctor import bp as doctor_bp
    app.register_blueprint(doctor_bp, url_prefix='/doctor')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.caregiver import bp as caregiver_bp
    app.register_blueprint(caregiver_bp, url_prefix='/caregiver')

    from app.ai import bp as ai_bp
    app.register_blueprint(ai_bp, url_prefix='/ai')

    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    return app
