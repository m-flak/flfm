from flask_testing import TestCase
from flfm import create_app
from .config import Config

class TestConfig(Config):
    TESTING = True

class RulesTest(TestConfig, TestCase):
    def create_app(self):
        return create_app(self)

    def test_rule_mappings(self):
        return
