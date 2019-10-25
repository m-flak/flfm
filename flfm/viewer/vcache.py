"""
    Viewer Cache for Built-In Viewer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The viewer cache.

"""
import base64
import hashlib
import os
from io import BytesIO, SEEK_SET, SEEK_END
import operator
import threading
from cachetools import LFUCache, cachedmethod
from cachetools.keys import hashkey

class VCFile:
    """A File that has been cached.

    :param filepath: The path to said file.
    :type filepath: str
    """
    def __init__(self, filepath):
        with open(filepath, 'rb') as file:
            self.buffer = BytesIO(file.read())
            self.buffer.seek(0, SEEK_END)
            self.file_bytes = self.buffer.tell()
            self.buffer.seek(0, SEEK_SET)

    # pylint: disable=anomalous-backslash-in-string

    def read_contents(self, **kwargs):
        """Read the contents of the file into cached memory.

        :param \**kwargs: See below

        :Keyword Arguments:
            * *decode_as* --
              Can be: ``none``, ``base64`` , or ``utf-8``

        """
        encoding = kwargs.get('decode_as', '')

        # Important to Logic
        # pylint: disable=no-else-return

        if encoding:
            if 'none' in encoding or not encoding:
                return self.buffer.getvalue()
            elif 'base64' in encoding:
                return base64.b64encode(self.buffer.getvalue())

            return self.buffer.getvalue().decode(encoding)
        return self.buffer.getvalue()

    def __hash__(self):
        md5 = hashlib.md5()
        md5.update(self.buffer.getvalue())
        return int(md5.hexdigest()[0:16], 16)

class ViewerCache:
    """The viewer cache.

    +-------------------------+---------------------------------------------------+
    | Configuration Variables | Description                                       |
    +=========================+===================================================+
    |``VCACHE_MAX_FILESIZE``  | This controls the maximum size of the file.       |
    +-------------------------+---------------------------------------------------+
    |``VCACHE_MAX_FILES``     | This controls the max cacheable files at one time.|
    +-------------------------+---------------------------------------------------+

    :param app: The Flask application
    :type app: Flask
    """
    been_setup = False
    max_file_size = 0
    max_files = 0

    @staticmethod
    def getsizeof(obj):
        return getattr(obj, 'file_bytes', 1)

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

        self.lock = threading.RLock()
        self.cache = None
        if self.been_setup:
            self.finish_setup()

    def init_app(self, app):
        self.max_file_size = app.config['VCACHE_MAX_FILESIZE']
        self.max_files = app.config['VCACHE_MAX_FILES']

        self.been_setup = True
        self.finish_setup()

    def finish_setup(self):
        self.cache = LFUCache(self.max_file_size*self.max_files, self.getsizeof)

    def is_file_cacheable(self, filepath):
        if os.stat(filepath).st_size > self.max_file_size:
            return False
        return True

    @cachedmethod(operator.attrgetter('cache'), hashkey,
                  operator.attrgetter('lock'))
    def view_file(self, filepath):
        return VCFile(filepath)

###############################################################################
vcache = ViewerCache()
