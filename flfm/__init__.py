import os
from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_socketio import SocketIO
from .shell import shell
from .viewer import viewer, vcache

bootstrap = Bootstrap()
e_session = Session()
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

    # Setup extensions
    bootstrap.init_app(app)
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

    # SOCKET-IO STUFF GOES HERE
    # Imports required as they cause the decorators to be trigg'd
    # pylint: disable=unused-import
    from .sockets import prepare_video, received_video

    return app

def app_route():
    return redirect(url_for('shell.shell_default'))
