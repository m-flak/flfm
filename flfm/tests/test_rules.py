import pathlib
import tempfile
import werkzeug.exceptions
from flask import current_app, url_for
from flask_testing import TestCase
from flfm import create_app
from flfm.shell.paths import ShellPath, ShellDirectory
from flfm.shell.rules import (
    Rules, MappedDirectories, enforce_mapped
)
from .config import Config

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class RulesTest(TestConfig, TestCase):
    def create_app(self):
        return create_app(self)

    def test_rule_mappings(self):
        rules_file = current_app.config['RULES_FILE']
        the_rules = Rules(rules_file)

        rule_mapping = MappedDirectories.from_rules(the_rules)

        allowed_path = None
        disallowed_path = None
        for md in rule_mapping:
            if allowed_path is None and md.dir_allowed:
                allowed_path = ShellPath(md.dir_path)
            if disallowed_path is None and not md.dir_allowed:
                disallowed_path = ShellPath(md.dir_path)
            if allowed_path is not None and disallowed_path is not None:
                break

        allow_mapping = MappedDirectories.from_shell_path(allowed_path).\
                        apply_rule_map(rule_mapping)
        disallow_mapping = MappedDirectories.from_shell_path(disallowed_path).\
                           apply_rule_map(rule_mapping)

        temp_path = ShellDirectory(pathlib.Path(tempfile.gettempdir())).path

        #
        # TESTING enforce_mapped() method from rules
        #
        print("\n\nTEST enforce_mapped() METHOD:\n")
        print("enforce_mapped() on a path root.")
        # allowed
        print(allowed_path.str_path)
        enforce_mapped(allow_mapping, allowed_path.str_path)
        # disallowed
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            enforce_mapped(disallow_mapping, disallowed_path.str_path)

        print("\nenforce_mapped() on a path's subdirectories.")
        # allowed
        for subdirectory in allowed_path.directories:
            # An explicitly disallowed directory should not be a test case
            if allow_mapping.get_mapped_dir(subdirectory.path) \
            == disallow_mapping.get_mapped_dir(subdirectory.path):
                continue
            enforce_mapped(allow_mapping, subdirectory.path)
        # disallowed
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            for subdirectory in disallowed_path.directories:
                print(subdirectory.path)
                enforce_mapped(disallow_mapping, subdirectory.path)

        print("\nenforce_mapped() on the system's temp folder.")
        print(temp_path)
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            enforce_mapped(allow_mapping, temp_path)
            enforce_mapped(disallow_mapping, temp_path)
        #
        # TESTING URL ROUTES FROM `shell`
        #
        print("\n\nTEST WEB INTERFACE:\n")
        print("Navigating to an allowed path in browser.")
        path = allowed_path.str_path
        response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
        print(path)
        self.assert200(response)

        print("\nNavigating to a disallowed path in browser.")
        path = disallowed_path.str_path
        response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
        print(path)
        self.assert403(response)

        print("\nNavigating to an allowed path's subdirectories in browser.")
        for subdirectory in allowed_path.directories:
            path = subdirectory.path
            try:
                response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
            except PermissionError:
                continue
            # An explicitly disallowed directory should not be a test case
            if allow_mapping.get_mapped_dir(subdirectory.path) \
            == disallow_mapping.get_mapped_dir(subdirectory.path):
                continue
            print(path)
            self.assert200(response)

        print("\nNavigating to a disallowed path's subdirectories in browser.")
        for subdirectory in disallowed_path.directories:
            path = subdirectory.path
            # An explicitly allowed subirectory should not be in the test case
            if rule_mapping.get_mapped_dir(path).dir_allowed:
                continue
            try:
                response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
            except PermissionError:
                continue
            print(path)
            self.assert403(response)

        print("\nNavigating to the system's temp folder in browser.")
        path = temp_path
        response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
        print(path)
        self.assert403(response)
