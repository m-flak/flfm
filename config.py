import os
from flask_dotenv import DotEnv

class Config:
    SESSION_TYPE = 'filesystem'
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'flfm-session:'
    SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', os.path.join(os.getcwd(), 'flask_session'))
    RULES_FILE = os.environ.get('RULES_FILE', None)

    @classmethod
    def init_app(self, app):
        env = DotEnv()
        env.init_app(app, verbose_mode=True)
