from flask import Flask
from app.models import User
from app.users.routes import users_bp
from config import Config
from app.extensions import db, login_manager, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = "warning"

    # 🔑 USER LOADER (THIS FIXES YOUR ERROR)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.public.routes import public_bp
    from app.users.routes import users_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(public_bp, url_prefix='/')
    app.register_blueprint(users_bp, url_prefix='/users')
    # app.register_blueprint(users_bp, url_prefix='/users')

    return app

