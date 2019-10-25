from itsdangerous import Signer
from itsdangerous.exc import BadSignature
from flask import current_app
from flask_login import UserMixin
import flfm as f

class User(UserMixin, f.db.Model):
    __tablename__ = 'users'
    id = f.db.Column(f.db.Integer, primary_key=True)
    name = f.db.Column(f.db.String(255), index=True, unique=True)
    password = f.db.Column(f.db.String(255))
    admin = f.db.Column(f.db.Boolean)
    enabled = f.db.Column(f.db.Boolean)

    # UserMixin override method
    @property
    def is_active(self):
        return self.enabled

    @property
    def is_admin(self):
        return self.admin

    def set_password(self, password):
        # since secret_key is read from a blob, it will be a byte string
        signer_guy = Signer(current_app.secret_key)
        # signing a string with a bytes makes it too also a bytes
        signature = signer_guy.sign(password)
        dot = signature.index(b'.')
        signature = signature[1+dot:]
        # make it string for the DB
        self.password = signature.decode('utf-8')

    def check_password(self, password):
        stored_sig = bytes(self.password, 'utf-8')
        check_pass = bytes(password, 'utf-8')
        full_challenge = check_pass + b'.' + stored_sig
        ricks_buddy = Signer(current_app.secret_key)
        # Make sure the password is legitimate before it's pawned ;)
        try:
            ricks_buddy.unsign(full_challenge)
        except BadSignature:
            # NOPE!
            return False

        return True

    def change_password(self, new_password):
        return self.set_password(new_password)

@f.login.user_loader
def load_user(id):
    return User.query.get(int(id))
