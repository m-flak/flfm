import os
from flask_dotenv import DotEnv

class Config:
    ACCOUNT_REGISTRATION_ENABLED = False
    BANNER = 'Flask File Manager'
    BANNER_TYPE = 'string'
    BYPASS_DOTENV = False
    DB_SCHEMA = os.environ.get('DB_SCHEMA', 'mysql')
    DB_USERNAME = os.environ.get('DB_USERNAME', '')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', '')
    DB_DATABASE = os.environ.get('DB_DATABASE', '')
    SESSION_TYPE = 'filesystem'
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'flfm-session:'
    SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR',
                                      os.path.join(os.getcwd(),
                                                   'flask_session'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RULES_FILE = os.environ.get('RULES_FILE', None)
    VCACHE_MAX_FILESIZE = 1048576
    VCACHE_MAX_FILES = 16
    VIEWER_VIDEO_DIRECTORY = os.environ.get('VIEWER_VIDEO_DIRECTORY',
                                            os.path.join(os.getcwd(),
                                                         'videos'))

    @classmethod
    def init_app(cls, app):
        env = DotEnv()
        env.init_app(app, verbose_mode=True)
