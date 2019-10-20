import os
from flask import Flask, redirect, url_for, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_session import Session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from .shell import shell
from .viewer import viewer, vcache

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
    config_object.init_app(app)

    # Get secret key
    secret_path = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(secret_path, 'secret.key'), 'rb') as key:
        secret_key = key.read()
        app.secret_key = secret_key

    # Setup database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = '{0}://{1}:{2}@{3}/{4}'.\
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

    if root != '/':
        app.add_url_rule(format_root(root=root), app_route.__name__, app_route)
        app.add_url_rule(format_root('/', root=root), app_route.__name__,
                         app_route)
    else:
        app.add_url_rule('/', app_route.__name__, app_route)

    # REGISTER ERROR HANDLERS
    app.register_error_handler(403, forbidden_route)

    # SOCKET-IO STUFF GOES HERE
    # Imports required as they cause the decorators to be trigg'd
    # pylint: disable=unused-import
    from .sockets import prepare_video, received_video
    # DATABASE MODELS
    from flfm import models

    return app

def app_route():
    return redirect(url_for('shell.shell_default'))

def forbidden_route(e):
    return render_template('403.html'), 403
