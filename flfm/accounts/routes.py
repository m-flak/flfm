from flask import (
    Blueprint, current_app, g, render_template, abort, redirect,
    url_for, flash, request
)
from flask_login import current_user, login_user, logout_user, login_required
from flfm.misc import get_banner_string
# i hate how flask-sqlalchemy forces me to do this >:(
import flfm as f
from .forms import (
    LoginForm, RegisterForm, UpdatePasswordForm, ManageAccountsForm,
    MySharesForm
)

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

    form = RegisterForm()
    if form.validate_on_submit():
        user = f.models.User.query.filter_by(name=form.username.data).first()
        if user is None:
            new_user = f.models.User(name=form.username.data, password='',
                                     admin=False, enabled=False)
            new_user.set_password(form.password.data)
            f.db.session.add(new_user)
            f.db.session.commit()
            flash("""Your account has been created. However, you'll need to wait
                  for an administrator to activate your account.
                  """)
            return redirect(url_for('shell.shell_default'))
        # Username exists :O
        flash("The user name you've specified already exists. Try Again...")

    return render_template('register.html', form=form)

@accounts.route('/dashboard/<string:dash_tab>', methods=['GET', 'POST'])
@login_required
def dashboard(dash_tab):
    if 'admin' in dash_tab and current_user.is_admin is False:
        flash("You do not have sufficient privileges for this tab...")
        return redirect(url_for('accounts.dashboard', dash_tab='user'))

    _dash_tab = dash_tab
    # default to the `user` tab if fed a bogus tab name
    if dash_tab not in ('admin', 'user', 'shares'):
        _dash_tab = 'user'

    form = None
    share_with_me = None
    if 'user' in _dash_tab:
        form = UpdatePasswordForm()
    elif 'admin' in _dash_tab:
        form = ManageAccountsForm()
        # populate accounts when GET'ing the route
        if request.method == 'GET':
            for account in f.models.User.query.all():
                form.manage_us.append_entry(dict(user_name=account.name,
                                                 is_enabled=account.enabled,
                                                 is_admin=account.admin))
    elif 'shares' in _dash_tab:
        # Populate `share_with_me`
        shares = f.models.Share.query.filter_by(shared_to_id=current_user.id)
        if shares.count() > 0:
            share_with_me = [s.owner.name for s in shares]

        form = MySharesForm()
        # GET shares for the form
        form.sharing_to.choices = [(s.id, s.receiver.name) for s in f.models.Share.query.filter_by(owner_id=current_user.id)]

    if form and form.validate_on_submit():
        # Submit POST from the Users Tab
        if isinstance(form, UpdatePasswordForm):
            submit_update_password(form)
        # Submit POST from the Admin Tab
        elif isinstance(form, ManageAccountsForm):
            submit_manage_accounts(form)
        elif isinstance(form, MySharesForm):
            submit_my_shares(form)

        # POST return
        return redirect(url_for('accounts.dashboard', dash_tab=_dash_tab))

    # GET return
    return render_template('dashboard.html', current_tab=_dash_tab, form=form,
                           share_with_me=share_with_me)

#### FOR THE DASHBOARD ROUTE ####
# Update Password
def submit_update_password(form):
    if not current_user.check_password(form.current_password.data):
        flash("Please enter your current password correctly...")
    else:
        current_user.set_password(form.new_password_again.data)
        f.db.session.commit()
        flash("Password successfully changed.")

# Manage Accounts
def submit_manage_accounts(form):
    changes_made = False
    for entry, acct in zip(form.manage_us.entries, f.models.User.query.all()):
        assert entry.user_name.data == acct.name
        changed = False
        if entry.is_enabled.data != acct.enabled:
            acct.enabled = entry.is_enabled.data
            changed = True
        if entry.is_admin.data != acct.admin:
            acct.enabled = entry.is_admin.data
            changed = True

        changes_made = changes_made or changed
        # Only call commit if there be changes. Arr!
        if changed:
            f.db.session.commit()
    if changes_made:
        flash("Account(s) have been updated...")
    else:
        flash("No changes were made to account(s)...")

# The Shares Form
def submit_my_shares(form):
    if 'manage' in form.what_to_do.data:
        if form.stop_sharing_to.data is True:
            stop = f.models.Share.query.filter_by(id=form.sharing_to.data).first()
            if stop is not None:
                f.db.session.delete(stop)
                f.db.session.commit()
            else:
                flash("Unable to remove share.")
        else:
            flash("Nothing changed. Perhaps you meant to click 'Stop Sharing'?")
    elif 'new' in form.what_to_do.data:
        user = f.models.User.query.filter_by(name=form.new_share_with.data).first()

        if user is not None:
            new_share = f.models.Share(owner_id=current_user.id,
                                       shared_to_id=user.id)
            f.db.session.add(new_share)
            f.db.session.commit()
            flash("Success! You are now sharing your files with: {}!".\
                  format(user.name))
        else:
            flash("Invalid user specified. Please try again.")
