import hashlib
from io import BytesIO, SEEK_SET, SEEK_END
import operator
import threading
from cachetools import LFUCache, cachedmethod
from cachetools.keys import hashkey

class VCFile:
    def __init__(self, filepath):
        with open(filepath, 'rb') as file:
            self.buffer = BytesIO(file.read())
            self.buffer.seek(0, SEEK_END)
            self.file_bytes = self.buffer.tell()
            self.buffer.seek(0, SEEK_SET)

    def read_contents(self, **kwargs):
        encoding = kwargs.get('decode_as', '')
        if not len(encoding) == 0:
            return self.buffer.getvalue().decode(encoding)
        return self.buffer.getvalue()

    def __hash__(self):
        md5 = hashlib.md5()
        md5.update(self.buffer.getvalue())
        return int(md5.hexdigest()[0:16], 16)

class ViewerCache:
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
        self.cache = LFUCache(self.max_file_size*self.max_files)

    @cachedmethod(operator.attrgetter('cache'), hashkey,
                  operator.attrgetter('lock'))
    def view_file(self, filepath):
        return VCFile(filepath)

###############################################################################
vcache = ViewerCache()
