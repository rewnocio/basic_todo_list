from pymongo import Connection

from .config import Config

# Mongo DB
connection = Connection(Config.MONGO['host'], Config.MONGO['port'])
db = connection[Config.DB]

def init_db():
    from models import Admin
    admin = { 'email': Config.ADMIN_USER['login'] }
    exists = Admin.find_one(admin)
    if not exists:
        u = Admin(admin)
        u.encrypt_password(Config.ADMIN_USER['password'])