import os
from flask import current_app, url_for
from flask_testing import TestCase
from flfm import create_app
from flfm.misc import make_arg_url
from flfm.shell.paths import ShellDirectory
from flfm.viewer.vcache import VCFile
from .config import Config

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class ViewerTest(TestConfig, TestCase):
    def __init__(self, *args, **kwargs):
        super(ViewerTest, self).__init__(*args, **kwargs)

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
        self.large_file = os.path.join(
            our_path,
            'output',
            'large_file.txt'
        )

        self.faketree_dir = ShellDirectory.from_str_loc(self.allow_root).path
        self.disallow_dir = ShellDirectory.from_str_loc(self.explicit_disallow).path
        self.output_dir = ShellDirectory.from_str_loc(os.path.dirname(self.large_file)).path

    def setUp(self):
        rule_contents = 'Allowed={}\nAllowed={}\nDisallowed={}'.\
                        format(self.faketree_dir,
                               self.output_dir,
                               self.disallow_dir)

        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

        with open(self.sample_rules, 'w') as f:
            f.write(rule_contents)

        if os.path.exists(self.large_file):
            os.remove(self.large_file)

        with open(self.large_file, 'wb') as f:
            f.seek(self.VCACHE_MAX_FILESIZE+1024)
            f.write(b'\x20')

    def tearDown(self):
        if os.path.exists(self.sample_rules):
            os.remove(self.sample_rules)

        if os.path.exists(self.large_file):
            os.remove(self.large_file)

    def create_app(self):
        return create_app(self)

    def test_viewer_redirect(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_path = self.faketree_dir
        test_file = root_path + '/File1.txt'
        mimetype = 'text/plain'

        serve_url = url_for('shell.serve_file')
        view_url = make_arg_url(url_for('viewer.view_file'), {
            'f': test_file,
            'mt': mimetype,
        })

        print("\n\nTEST VIEWER REDIRECT")
        self.client.set_cookie('localhost', 'flfm_viewer', 'enabled')
        response = self.client.get(serve_url,
                                   query_string=dict(f=test_file))
        self.assertStatus(response, 302)
        self.assertRedirects(response, view_url)

    def test_viewer_restrictions(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_path = self.faketree_dir
        test_file_1 = root_path + '/File1.txt'
        test_file_2 = root_path + '/subdir1/File1.txt'
        test_file_3 = root_path + '/subdir2/File1.txt'
        mimetype = 'text/plain'

        view_url = url_for('viewer.view_file')

        print("\n\nTEST VIEWER RESTRICTIONS")
        # allowed
        response = self.client.get(view_url,
                                   query_string=dict(f=test_file_1,
                                                     mt=mimetype))
        self.assert200(response)
        # allowed subdirectory
        response = self.client.get(view_url,
                                   query_string=dict(f=test_file_2,
                                                     mt=mimetype))
        self.assert200(response)
        # disallowed subdirectory
        response = self.client.get(view_url,
                                   query_string=dict(f=test_file_3,
                                                     mt=mimetype))
        self.assert403(response)

    def test_viewer_caching(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_path = self.faketree_dir
        mimetype = 'text/plain'
        test_files = [root_path + '/File1.txt',
                      root_path + '/subdir1/File1.txt',
                      root_path + '/subdir1/File2.txt',
                      root_path + '/subdir1/File3.txt']

        view_url = url_for('viewer.view_file')

        print("\n\nTEST VIEWER CACHING/VIEWING")
        for test_file in test_files:
            response = self.client.get(view_url,
                                       query_string=dict(f=test_file,
                                                         mt=mimetype))
            self.assert200(response)
            self.assertTemplateUsed('viewer.html')
            vc_file = self.get_context_variable('current_contents')
            self.assertTrue(isinstance(vc_file, VCFile))
            with open(test_file, 'rb') as f:
                on_fs = f.read()
                in_flfm = vc_file.read_contents(decode_as='none')
                self.assertEqual(on_fs, in_flfm)

    def test_viewer_large_file(self):
        current_app.config['RULES_FILE'] = self.sample_rules
        root_path = self.output_dir
        test_file = root_path + '/large_file.txt'
        mimetype = 'text/plain'

        view_url = url_for('viewer.view_file')

        print("\n\nTEST VIEWER LARGE FILES")
        response = self.client.get(view_url,
                                   query_string=dict(f=test_file,
                                                     mt=mimetype))
        self.assert200(response)
        self.assertTemplateUsed('viewer.html')
        was_cacheable = self.get_context_variable('was_cacheable')
        cache_id = self.get_context_variable('cache_id')
        self.assertFalse(was_cacheable)
        self.assertEqual(cache_id, -1)
