import os
import werkzeug.exceptions
from flask import current_app, url_for
from flask_testing import TestCase
from flfm import create_app
from flfm.misc import make_filepond_id
from flfm.shell.paths import ShellDirectory
from flfm.shell.uploads import UploadedFile
from .config import Config

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class UploadsTest(TestConfig, TestCase):
    def __init__(self, *args, **kwargs):
        super(UploadsTest, self).__init__(*args, **kwargs)

        our_path = os.path.abspath(os.path.dirname(__file__))
        self.sample = os.path.join(
            our_path,
            'samples',
            'text_upload.txt'
        )
        self.sample_rules = os.path.join(
            our_path,
            'samples',
            'sample_rules'
        )
        self.output = os.path.join(
            our_path,
            'output',
            'text_upload.txt'
        )

        self.test_rule_dir = ShellDirectory.from_str_loc(os.path.dirname(self.output)).path

    def setUp(self):
        rule_contents = 'Allowed={0}\nAllowUploads={0}'.\
                        format(self.test_rule_dir)

        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

        with open(self.sample_rules, 'w') as f:
            f.write(rule_contents)

    def tearDown(self):
        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

    def create_app(self):
        return create_app(self)

    def test_uploaded_file(self):
        test_file = UploadedFile(make_filepond_id(),
                                 os.path.dirname(self.output),
                                 os.path.basename(self.output))
        test_buffer = None
        test_buffer2 = None

        print("\n\nTEST UPLOADS:\n")
        print("UploadedFile")

        self.assertFalse(test_file.permanent)
        self.assertFalse(test_file.temporary)

        with self.assertRaises(FileNotFoundError):
            test_file.make_permanent()

        with self.assertRaises(FileNotFoundError):
            boo = test_file.file

        test_file.create_temporary()
        self.assertTrue(test_file.temporary)

        with open(self.sample, 'rb') as f:
            test_buffer = f.read()

        test_file.file.write(test_buffer)
        test_file.file.close()
        test_file.make_permanent()

        self.assertTrue(test_file.permanent)

        with self.assertRaises(FileExistsError):
            test_file.make_permanent()

        with open(self.output, 'rb') as f:
            test_buffer2 = f.read()

        self.assertEqual(test_buffer, test_buffer2)

        os.remove(self.output)

    def test_uploading(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        ul_to = self.test_rule_dir
        ul_to_2 = ul_to + '/subdir'
        ul_to_3 = '/var/some/cool/place'

        print("\nTesting uploading through the web interface.")

        url = url_for('shell.process')
        response = self.client.post(url, headers=dict({'X-Uploadto': ul_to }),
                                    data=dict(filepond=open(self.sample, 'rb')))
        self.assert200(response)
        response = self.client.post(url, headers=dict({'X-Uploadto': ul_to_2 }),
                                    data=dict(filepond=open(self.sample, 'rb')))
        self.assert200(response)
        response = self.client.post(url, headers=dict({'X-Uploadto': ul_to_3 }),
                                    data=dict(filepond=open(self.sample, 'rb')))
        self.assert403(response)
