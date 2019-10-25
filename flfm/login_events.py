import os
from flask import current_app, session
from flask_login import user_logged_in

@user_logged_in.connect
def user_logon_event(sender, user, **extra):
    users_folder = current_app.config['USERS_HOME_FOLDERS']
    curusr_home_folder = os.path.join(users_folder, user.name)

    if not os.path.exists(curusr_home_folder):
        os.mkdir(curusr_home_folder)

    session['user_home'] = curusr_home_folder
