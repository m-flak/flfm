from flask_script import Manager, prompt, prompt_bool, prompt_pass
from flask_migrate import Migrate, MigrateCommand
from flfm import create_app, db
from flfm.models import User
from config import Config

app = create_app(Config)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

@manager.option('-u', '--username', dest="username", required=False)
@manager.option('-p', '--password', dest="password", required=False)
@manager.option('-a', '--admin', dest="admin", required=False)
def createuser(username=None, password=None, admin=None):
    """Create a user account for the application.
    """
    u_name = username
    pw = password
    make_admin = admin

    if u_name is None:
        while True:
            u_name = prompt("User Name")
            user = User.query.filter(User.name==u_name).first()
            if user is not None:
                print("{}: USER ALREADY EXISTS!".format(u_name))
            else:
                break

    if pw is None:
        pw = prompt_pass("Password")
        while True:
            pw_again = prompt_pass("Password Again")
            if pw != pw_again:
                print("PASSWORDS DO NOT MATCH!")
            else:
                break

    if make_admin is None:
        make_admin = prompt_bool("Do you wish to make {} an administrator?".\
                                 format(u_name))

    user = User(name=u_name, password="", admin=make_admin, enabled=True)
    user.set_password(pw)

    db.session.add(user)
    db.session.commit()
    print("Successfully created '{}' with ID: {}.".format(user.name, user.id))

if __name__ == '__main__':
    manager.run()
