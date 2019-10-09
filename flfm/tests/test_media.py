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
        self.samples_dir = ShellDirectory.from_str_loc(os.path.dirname(self.sample_rules)).path

    def setUp(self):
        rule_contents = 'Allowed={}\nAllowed={}\nDisallowed={}'.\
                        format(self.faketree_dir, self.samples_dir,
                               self.disallow_dir)

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

        print("\n\nTEST MEDIALIST SHELL ROUTE:\n")

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

    def test_media_info(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_dir = self.samples_dir
        file_1 = 'test_mp4_file.mp4'
        redundant_file_1 = os.path.join(root_dir, file_1)
        file_2 = 'text_upload.txt'
        redundant_file_2 = os.path.join(root_dir, file_2)
        malformed_file_name = file_1 + file_2

        print("\n\nTEST MEDIAINFO SHELL ROUTE:\n")

        url = url_for('shell.mediainfo')

        print("directory, file pair")
        #
        # ON MEDIA
        #
        response = self.client.post(url, data=dict(directory=root_dir,
                                                   file=file_1))
        self.assert200(response)
        self.assertTrue(response.is_json)
        r_data = response.get_json(False, True, False)
        self.assertIsNotNone(r_data)
        self.assertEqual(r_data['filename'], file_1)
        self.assertEqual(r_data['width'], 1920)
        self.assertEqual(r_data['height'], 1080)
        #
        # ON NON-MEDIA
        #
        response = self.client.post(url, data=dict(directory=root_dir,
                                                   file=file_2))
        self.assertStatus(response, 501)

        print("directory, full_path_to_file pair")
        #
        # ON MEDIA
        #
        response = self.client.post(url, data=dict(directory=root_dir,
                                                   file=redundant_file_1))
        self.assert200(response)
        self.assertTrue(response.is_json)
        r_data = response.get_json(False, True, False)
        self.assertIsNotNone(r_data)
        self.assertEqual(r_data['filename'], file_1)
        self.assertEqual(r_data['width'], 1920)
        self.assertEqual(r_data['height'], 1080)
        #
        # ON NON-MEDIA
        #
        response = self.client.post(url, data=dict(directory=root_dir,
                                                   file=redundant_file_2))
        self.assertStatus(response, 501)

        print("bad filename")
        response = self.client.post(url, data=dict(directory=root_dir,
                                                   file=malformed_file_name))
        self.assert400(response)
