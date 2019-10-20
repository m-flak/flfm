from flask_login import UserMixin
from flfm import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True)
    password = db.Column(db.String(255))
    admin = db.Column(db.Boolean)
    enabled = db.Column(db.Boolean)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
