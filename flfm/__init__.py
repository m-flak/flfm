import os
from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_session import Session
from .shell import shell
from .viewer import viewer, vcache

bootstrap = Bootstrap()
e_session = Session()

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

    # Setup dependents
    vcache.init_app(app)

    app.register_blueprint(shell, url_prefix='/')
    app.register_blueprint(viewer, url_prefix='/viewer/')

    app.add_url_rule('/', app_route.__name__, app_route)

    return app

def app_route():
    return redirect(url_for('shell.shell_default'))
