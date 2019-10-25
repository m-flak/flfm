from flask import current_app, url_for
from flask_login import current_user, login_user
from flask_testing import TestCase
from flfm import create_app, db
from flfm.models import User
from flfm.accounts.forms import LoginForm
from .config import Config

class TestConfig(Config):
    BYPASS_DOTENV = True
    TESTING = True
    PROPAGATE_EXCEPTIONS = True
    DB_SCHEMA = 'mysql'
    DB_USERNAME = 'flfm_user'
    DB_PASSWORD = 'drowssap'
    DB_HOST = 'localhost'
    DB_DATABASE = 'flfm_tests'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

class AccountsTesting(TestConfig, TestCase):
    def create_app(self):
        app = create_app(self)
        # the .env still overwrites fgsfds
        app.config['DB_DATABASE'] = 'flfm_tests'
        return app

    def setUp(self):
        db.create_all()

        test_user = User(name='test_user', password='', admin=False,
                         enabled=True)
        test_user.set_password('testpass1')
        test_admin = User(name='test_admin', password='', admin=True,
                          enabled=True)
        test_admin.set_password('testpass2')
        test_disabled = User(name='test_disabled', password='',
                             admin=False, enabled=False)
        test_disabled.set_password('testpass3')

        db.session.add(test_user)
        db.session.add(test_admin)
        db.session.add(test_disabled)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_users_present_in_db(self):
        user1 = User.query.filter_by(name='test_user').first()
        user2 = User.query.filter_by(name='test_admin').first()
        user3 = User.query.filter_by(name='test_disabled').first()

        self.assertIsNotNone(user1)
        self.assertIsNotNone(user2)
        self.assertIsNotNone(user3)

    def test_user_check_password(self):
        user1 = User.query.filter_by(name='test_user').first()
        user2 = User.query.filter_by(name='test_admin').first()
        user3 = User.query.filter_by(name='test_disabled').first()

        self.assertTrue(user1.check_password('testpass1'))
        self.assertTrue(user2.check_password('testpass2'))
        self.assertTrue(user3.check_password('testpass3'))

    def test_shell_default_no_user(self):
        response = self.client.get(url_for('shell.shell_default'))
        self.assert200(response)
        self.assertTrue(current_user.is_anonymous)

    def test_login_of_user(self):
        with self.client as c:
            login_form = LoginForm()
            response = c.post(url_for('accounts.login'), data={
                login_form.username.name: 'test_user',
                login_form.password.name: 'testpass1',
            }, follow_redirects=True)

            self.assert200(response)
            user = User.query.filter_by(name='test_user').first()
            self.assertIsNotNone(user)
            login_user(user)
            self.assertEqual(user, current_user)
            self.assertFalse(current_user.is_admin)
            self.assertTrue(current_user.is_active)

    def test_login_of_admin(self):
        with self.client as c:
            login_form = LoginForm()
            response = c.post(url_for('accounts.login'), data={
                login_form.username.name: 'test_admin',
                login_form.password.name: 'testpass2',
            }, follow_redirects=True)

            self.assert200(response)
            user = User.query.filter_by(name='test_admin').first()
            self.assertIsNotNone(user)
            login_user(user)
            self.assertEqual(user, current_user)
            self.assertTrue(current_user.is_admin)
            self.assertTrue(current_user.is_active)

    def test_login_of_disabled(self):
        with self.client as c:
            login_form = LoginForm()
            response = c.post(url_for('accounts.login'), data={
                login_form.username.name: 'test_disabled',
                login_form.password.name: 'testpass3',
            }, follow_redirects=True)

            self.assert200(response)
            user = User.query.filter_by(name='test_disabled').first()
            self.assertIsNotNone(user)
            self.assertNotEqual(user, current_user)
            self.assertTrue(current_user.is_anonymous)

    def test_login_with_wrong_password(self):
        with self.client as c:
            login_form = LoginForm()
            response = c.post(url_for('accounts.login'), data={
                login_form.username.name: 'test_user',
                login_form.password.name: 'wrongpassword',
            })

            self.assert200(response)
            self.assertTrue(current_user.is_anonymous)

    def test_registration_disabled(self):
        current_app.config['ACCOUNT_REGISTRATION_ENABLED'] = False
        response = self.client.get(url_for('accounts.register'))
        self.assertStatus(response, 501)
