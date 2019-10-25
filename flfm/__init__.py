import os
from flask import Flask, redirect, url_for, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from flask_session import Session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from .shell import shell
from .viewer import viewer, vcache
from .accounts import accounts

db = SQLAlchemy()
bootstrap = Bootstrap()
e_session = Session()
login = LoginManager()
socketio = SocketIO()

def format_root(*args, **kwargs):
    root = kwargs.get('root', '')
    if not args:
        return root

    formatted = root
    for arg in args:
        add_me = arg
        if root[len(root)-1] == '/' and arg[0] == '/':
            add_me = arg.lstrip('/')
        formatted += add_me

    return formatted

def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # .env can fuck up tests
    if app.config['BYPASS_DOTENV'] is False:
        config_object.init_app(app)

    # Get secret key
    secret_path = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(secret_path, 'secret.key'), 'rb') as key:
        secret_key = key.read()
        app.secret_key = secret_key

    # Setup database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = '{0}://{1}:{2}@{3}/{4}?ssl=false'.\
                                            format(app.config.get('DB_SCHEMA'),
                                                   app.config.get('DB_USERNAME'),
                                                   app.config.get('DB_PASSWORD'),
                                                   app.config.get('DB_HOST'),
                                                   app.config.get('DB_DATABASE'))

    # Setup extensions
    db.init_app(app)
    bootstrap.init_app(app)
    login.init_app(app)
    e_session.init_app(app)
    socketio.init_app(app)

    # Setup dependents
    vcache.init_app(app)

    root = app.config.get('APPLICATION_ROOT', '/')
    app.register_blueprint(shell, url_prefix=format_root(root=root))
    app.register_blueprint(viewer, url_prefix=format_root('/viewer/', root=root))
    app.register_blueprint(accounts, url_prefix=format_root('/accounts/', root=root))

    if root != '/':
        app.add_url_rule(format_root(root=root), app_route.__name__, app_route)
        app.add_url_rule(format_root('/', root=root), app_route.__name__,
                         app_route)
    else:
        app.add_url_rule('/', app_route.__name__, app_route)

    # REGISTER ERROR HANDLERS
    app.register_error_handler(403, forbidden_route)
    app.register_error_handler(501, notimpl_route)

    # REGISTER CURRENT_USER TO JINJA2
    app.add_template_global(lambda cu=current_user: cu, 'the_cur_user')

    # SOCKET-IO STUFF GOES HERE
    # Imports required as they cause the decorators to be trigg'd
    # pylint: disable=unused-import
    from .sockets import prepare_video, received_video
    # DB models
    from flfm import models

    return app

def app_route():
    return redirect(url_for('shell.shell_default'))

def forbidden_route(e):
    return render_template('403.html'), 403

def notimpl_route(e):
    return render_template('501.html'), 501
