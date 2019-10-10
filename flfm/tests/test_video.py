import os
from flask_testing import TestCase
from flfm import create_app
from flfm.shell.video import MP4File
from .config import Config

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class VideoFormatTests(TestConfig, TestCase):
    def __init__(self, *args, **kwargs):
        super(VideoFormatTests, self).__init__(*args, **kwargs)

        our_path = os.path.abspath(os.path.dirname(__file__))
        self.non_video_sample = os.path.join(
            our_path,
            'samples',
            'text_upload.txt'
        )
        self.mp4_sample = os.path.join(
            our_path,
            'samples',
            'test_mp4_file.mp4'
        )
        self.mp4_sample_2 = os.path.join(
            our_path,
            'samples',
            'test_mp4_file2.mp4'
        )

    def create_app(self):
        return create_app(self)

    def test_mp4_file(self):
        print("\n\nTESTING MP4 CONTAINER PARSER")
        good_file = MP4File(self.mp4_sample)

        self.assertEqual(good_file.video_width, 1920)
        self.assertEqual(good_file.video_height, 1080)
        self.assertEqual(good_file.video_wxh, (1920, 1080))

        good_file2 = MP4File(self.mp4_sample_2)
        self.assertEqual(good_file2.video_width, 1920)
        self.assertEqual(good_file2.video_height, 1080)
        self.assertEqual(good_file2.video_wxh, (1920, 1080))

        with self.assertRaises(ValueError):
            bad_file = MP4File(self.non_video_sample)
