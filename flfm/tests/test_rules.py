import pathlib
import random
import tempfile
import werkzeug.exceptions
from flask import current_app, url_for
from flask_testing import TestCase
from flfm import create_app
from flfm.shell.paths import ShellPath, ShellDirectory
from flfm.shell.rules import (
    Rules, VirtualRules, MappedDirectories, enforce_mapped
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

    def test_without_rules(self):
        rules_file = current_app.config['RULES_FILE']
        current_app.config['RULES_FILE'] = None
        assert current_app.config['RULES_FILE'] is None

        blank_rules = Rules(None)
        rule_mapping = MappedDirectories.from_rules(blank_rules)

        temp_path = ShellDirectory(pathlib.Path(tempfile.gettempdir())).path
        temp_shell_path = ShellPath(temp_path)

        #
        # APPLYING AN EMPTY RULE MAP
        #
        print("\n\nTEST apply_rule_map WITH EMPTY RULES.\n")
        print("Applying empty rule map to: {}".format(temp_path))
        temp_mapping = MappedDirectories.from_shell_path(temp_shell_path).\
                       apply_rule_map(rule_mapping)

        #
        # ENFORCE_MAPPED W/O RULES
        #
        print("\n\nTEST enforce_mapped() METHOD W/O RULES:\n")
        print("On: {}".format(temp_path))
        with self.assertRaises(werkzeug.exceptions.Forbidden):
            enforce_mapped(temp_mapping, temp_path)

        #
        # TESTING URL ROUTES FROM `shell`
        #
        print("\n\nTEST WEB INTERFACE W/O RULES:\n")
        print("On: {}".format(temp_path))
        path = temp_path
        response = self.client.get(url_for('shell.shell_view', view_path=path.lstrip('/')))
        self.assert403(response)

        print("\nLoading 'default.html'...")
        response = self.client.get(url_for('shell.shell_default'))
        self.assert200(response)

        # restore RULES_FILE to initial
        current_app.config['RULES_FILE'] = rules_file
        assert current_app.config['RULES_FILE'] is rules_file

    def test_serve_rules(self):
        rules_file = current_app.config['RULES_FILE']
        the_rules = Rules(rules_file)
        rule_mapping = MappedDirectories.from_rules(the_rules)

        allowed_path = None
        disallowed_path = None

        for md in rule_mapping:
            if allowed_path is None and md.dir_allowed:
                allowed_path = ShellPath(md.dir_path)
                if not allowed_path.files:
                    del allowed_path
                    allowed_path = None
            if disallowed_path is None and not md.dir_allowed:
                disallowed_path = ShellPath(md.dir_path)
                if not disallowed_path.files:
                    del disallowed_path
                    disallowed_path = None
            if allowed_path is not None and disallowed_path is not None:
                break

        total_a_files = len(allowed_path.files)
        total_d_files = len(disallowed_path.files)
        the_a_file = allowed_path.files[random.randint(0, total_a_files-1)]
        the_d_file = disallowed_path.files[random.randint(0, total_d_files-1)]

        #
        # TEST PERMISSIONS WITH THE SERVE URL ROUTE
        #
        print("\n\nTEST SERVING FILES:\n")
        print("Serving allowed file: {}".format(the_a_file.path))
        the_url = url_for('shell.serve_file')
        response = self.client.get(the_url,
                                   query_string=dict(f=the_a_file.path))
        self.assert200(response)
        print("\nServing disallowed file: {}".format(the_d_file.path))
        response = self.client.get(the_url,
                                   query_string=dict(f=the_d_file.path))
        self.assert403(response)

        # # NOW, TEST WITH FILES WITHIN SUBDIRECTORIES

        total_a_dirs = len(allowed_path.directories)
        total_d_dirs = len(disallowed_path.directories)
        try:
        # random allowed subdirectory
            a_dir = [(lambda i=i, k=k: k if i == random.randint(0, total_a_dirs-1)
                      else None)() for i, k in enumerate(allowed_path.directories)]
            a_dir = list(filter(lambda x: x is not None, a_dir)).pop().to_shell_path()
        # random disallowed subdirectory
            d_dir = [(lambda i=i, k=k: k if i == random.randint(0, total_d_dirs-1)
                      else None)() for i, k in enumerate(disallowed_path.directories)]
            d_dir = list(filter(lambda x: x is not None, d_dir)).pop().to_shell_path()
        # OOPs. We can't find a decent random directory
        except (IndexError, PermissionError, ValueError):
            for subdirectory in allowed_path.directories:
                try:
                    as_sp = subdirectory.to_shell_path()
                    if as_sp.has_files:
                        a_dir = as_sp
                except PermissionError:
                    continue
            for subdirectory in disallowed_path.directories:
                try:
                    as_sp = subdirectory.to_shell_path()
                    if as_sp.has_files:
                        d_dir = as_sp
                except PermissionError:
                    continue

        total_a_files = len(a_dir.files)
        total_d_files = len(d_dir.files)
        try:
            the_a_file = a_dir.files[random.randint(0, total_a_files-1)]
        except ValueError:
            the_a_file = a_dir.files[0]
        try:
            the_d_file = d_dir.files[random.randint(0, total_d_files-1)]
        except ValueError:
            the_d_file = d_dir.files[0]

        print("\nServing allowed file from subdirectory...")
        print(the_a_file.path)
        response = self.client.get(the_url,
                                   query_string=dict(f=the_a_file.path))
        self.assert200(response)
        print("\nServing disallowed file from subdirectory...")
        print(the_d_file.path)
        response = self.client.get(the_url,
                                   query_string=dict(f=the_d_file.path))
        self.assert403(response)

class VirtualRulesTest(TestConfig, TestCase):
    def create_app(self):
        return create_app(self)

    def test_virtual_rules_template(self):
        rules_file = current_app.config['RULES_FILE']
        reg_rules = Rules(rules_file)
        virt_rules = VirtualRules(rules_file)

        self.assertEqual(reg_rules.num_rules, virt_rules.num_rules)
        self.assertEqual(reg_rules.rules, virt_rules.rules)

    def test_virtual_rules_addition(self):
        virt_rules = VirtualRules()

        virt_rules.allowed('/fake/path')
        virt_rules.allow_uploads('/faker/path')
        virt_rules.disallowed('/fakest/path')

        self.assertEqual(virt_rules.num_rules, 3)

        virt_rules.allowed('/icky/vicky')
        virt_rules.allow_uploads('/fairies/crocker')
        virt_rules.disallowed('/timmys/happiness')

        self.assertEqual(virt_rules.num_rules, 6)

    def test_virtual_rules_deletion(self):
        virt_rules = VirtualRules()

        virt_rules.allowed('/fake/path')
        virt_rules.allow_uploads('/faker/path')
        virt_rules.disallowed('/fakest/path')
        self.assertEqual(virt_rules.num_rules, 3)

        virt_rules.allowed('/fake/path', True)
        self.assertEqual(virt_rules.num_rules, 3-1)
        virt_rules.allow_uploads('/faker/path', True)
        self.assertEqual(virt_rules.num_rules, 3-2)
        virt_rules.disallowed('/fakest/path', True)
        self.assertEqual(virt_rules.num_rules, 3-3)

    def test_virtual_rules_template_add(self):
        rules_file = current_app.config['RULES_FILE']
        reg_rules = Rules(rules_file)
        virt_rules = VirtualRules(rules_file)

        virt_rules.allowed('/fake/path')
        virt_rules.allow_uploads('/faker/path')
        virt_rules.disallowed('/fakest/path')
        self.assertEqual(virt_rules.num_rules, 3+reg_rules.num_rules)

    def test_rules_to_virtual_rules(self):
        rules_file = current_app.config['RULES_FILE']
        reg_rules = Rules(rules_file)
        virt_rules = VirtualRules.make_virtual(reg_rules)

        self.assertEqual(reg_rules.num_rules, virt_rules.num_rules)
        self.assertEqual(reg_rules.rules, virt_rules.rules)
