import os
from flask import Flask
from dotenv import load_dotenv
from flask_login import current_user

from .extensions import init_login_manager, init_mongo
from .models.user import User


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    app.config['MONGO_DB_NAME'] = os.getenv('MONGO_DB_NAME', 'fake_news_lab')

    if not app.config['MONGO_URI']:
        raise RuntimeError('MONGO_URI is required. Set it in your .env file.')

    # Initialize services
    mongo_client = init_mongo(app.config['MONGO_URI'])
    login_manager = init_login_manager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        db = mongo_client[app.config['MONGO_DB_NAME']]
        doc = db.users.find_one({'_id': user_id})
        return User.from_document(doc) if doc else None

    # Blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp

    app.mongo_client = mongo_client  # Expose for blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Ensure indexes exist
    with app.app_context():
        db = mongo_client[app.config['MONGO_DB_NAME']]
        db.users.create_index('email', unique=True)
        db.articles.create_index([('user_id', 1), ('created_at', -1)])

    @app.context_processor
    def inject_user():
        return {'current_user': current_user}

    return app
