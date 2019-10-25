from flask import (
    Blueprint, current_app, g, render_template, abort, redirect,
    url_for, flash
)
from flask_login import current_user, login_user, logout_user
from flfm.misc import get_banner_string
import flfm as f
from .forms import LoginForm

accounts = Blueprint('accounts', __name__, template_folder='templates')

# These are globals for the Jinja2 engine
# pylint: disable=duplicate-code
@accounts.before_request
def make_vars_available():
    g.available_vars = {
        'app_root': current_app.config.get('APPLICATION_ROOT', '/'),
        'banner_string': get_banner_string(current_app),
        'registration_enabled': current_app.config.get('ACCOUNT_REGISTRATION_ENABLED',
                                                       False),
    }

@accounts.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shell.shell_default'))

    form = LoginForm()
    if form.validate_on_submit():
        user = f.models.User.query.filter_by(name=form.username.data).first()
        if user is not None:
            if user.check_password(form.password.data):
                if user.enabled is True:
                    login_user(user)
                    flash("Login Successful!")
                else:
                    flash("Your account has not been activated yet.")
                return redirect(url_for('shell.shell_default'))
            # bad password
            flash("Invalid Username and/or Password.")
        else:
            # bad username
            flash("Invalid Username and/or Password.")

    return render_template('login.html', form=form)

@accounts.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('shell.shell_default'))

@accounts.route('/register', methods=['GET', 'POST'])
def register():
    if not g.available_vars['registration_enabled']:
        abort(501)

    return render_template('register.html')
