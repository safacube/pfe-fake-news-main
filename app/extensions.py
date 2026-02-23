from flask_login import LoginManager
from pymongo import MongoClient

login_manager = LoginManager()
mongo_client = None


def init_login_manager(app):
    login_manager.init_app(app)
    return login_manager


def init_mongo(uri: str):
    global mongo_client
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return mongo_client
