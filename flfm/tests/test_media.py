import os
from flask import current_app, url_for
from flask_testing import TestCase
from flfm import create_app
from flfm.shell.paths import ShellDirectory
from .config import Config

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class MediaTest(TestConfig, TestCase):
    def __init__(self, *args, **kwargs):
        super(MediaTest, self).__init__(*args, **kwargs)

        our_path = os.path.abspath(os.path.dirname(__file__))
        self.sample_rules = os.path.join(
            our_path,
            'samples',
            'sample_rules'
        )
        self.allow_root = os.path.join(
            our_path,
            'faketree'
        )
        self.explicit_disallow = os.path.join(
            our_path,
            'faketree',
            'subdir2'
        )

        self.faketree_dir = ShellDirectory.from_str_loc(self.allow_root).path
        self.disallow_dir = ShellDirectory.from_str_loc(self.explicit_disallow).path

    def setUp(self):
        rule_contents = 'Allowed={}\nDisallowed={}'.\
                        format(self.faketree_dir, self.disallow_dir)

        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

        with open(self.sample_rules, 'w') as f:
            f.write(rule_contents)

    def tearDown(self):
        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

    def create_app(self):
        return create_app(self)

    def test_media_list(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_path = self.faketree_dir
        allowed_subdir = root_path + '/subdir1'
        disallow_subdir = root_path + '/subdir2'

        print("\n\nTEST MEDIA STUFF:\n")
        print("medialist shell route")

        url = url_for('shell.medialist')
        #
        # Medialist in ./faketree/
        #
        print(root_path)
        response = self.client.post(url, data=dict(directory=root_path,
                                                   whatkind='text/plain'))
        self.assert200(response)
        self.assertTrue(response.is_json)
        r_data = response.get_json(False, True, False)
        self.assertIsNotNone(r_data)
        # don't be empty
        self.assertFalse(not r_data)
        # be just one
        self.assertTrue(len(r_data) == 1)
        self.assertTrue(all(['File1.txt' in x['cur'] for x in r_data]))

        #
        # Medialist in ./faketree/subdir1
        #
        print(allowed_subdir)
        response = self.client.post(url, data=dict(directory=allowed_subdir,
                                                   whatkind='text/plain'))
        self.assert200(response)
        self.assertTrue(response.is_json)
        r_data = response.get_json(False, True, False)
        self.assertIsNotNone(r_data)
        # don't be empty
        self.assertFalse(not r_data)
        # be three
        self.assertTrue(len(r_data) == 3)
        self.assertTrue(any(['File1.txt' in x['cur'] for x in r_data]))
        self.assertTrue(any(['File2.txt' in x['cur'] for x in r_data]))
        self.assertTrue(any(['File3.txt' in x['cur'] for x in r_data]))

        #
        # Medialist in ./faketree/subdir2
        #
        print(disallow_subdir)
        response = self.client.post(url, data=dict(directory=disallow_subdir,
                                                   whatkind='text/plain'))
        self.assert403(response)
