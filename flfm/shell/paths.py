from pathlib import Path
import mimetypes
import re
import filetype

class ShellItem:
    file = False
    directory = False

    def __init__(self, path_obj):
        path = ''
        for p in path_obj.parts:
            if '\\' in p or '/' in p:
                continue
            path += '/{}'.format(p)
        self.name = path_obj.name
        self.path = path
        self.uri_path = self.path[1:len(self.path)]
        self.size = path_obj.lstat().st_size

    def parent_directory(self):
        before_name = self.path.index(self.name)
        return self.path[0:before_name].rstrip('/')

class ShellFile(ShellItem):
    file = True

    def __init__(self, path_obj):
        super().__init__(path_obj)
        self._mimetype = None

    def is_mimetype(self, want_type):
        our_type = filetype.guess(self.path).mime
        if our_type == want_type:
            return True
        return False

    def is_mimetype_family(self, want_family):
        our_type = filetype.guess(self.path)

        if our_type is None:
            # sometimes, filetype fails horribly
            # # like with text files. works great for images though
            type, encoding = mimetypes.guess_type(self.path)
            if type is None:
                return False
            if re.match(want_family, type) is not None:
                return True
            return False
        if re.match(want_family, our_type.mime) is not None:
            return True
        return False

    def __repr__(self):
        return '<{} \'{}\' at \'{}\'>'.format(self.__class__.__name__,
                                              self.name, self.path)

    @property
    def mimetype(self):
        if self._mimetype is None:
            try:
                self._mimetype = filetype.guess(self.path).mime
            except AttributeError:
                self._mimetype = mimetypes.guess_type(self.path)[0]
        return self._mimetype

class ShellDirectory(ShellItem):
    directory = True

    def __init__(self, path_obj):
        super().__init__(path_obj)

    @classmethod
    def from_str_loc(cls, str_location):
        path_object = Path(str_location)
        return cls(path_object)

    def to_shell_path(self):
        return ShellPath(self.path)

class ShellPath:
    def __init__(self, path_string, dir_mappings=None):
        def get_files(dirs):
            while True:
                try:
                    with next(dirs) as file:
                        if file.is_file():
                            yield file
                except StopIteration:
                    break
        def get_dirs(dirs):
            while True:
                try:
                    with next(dirs) as dirsss:
                        if dirsss.is_dir():
                            yield dirsss
                except StopIteration:
                    break

        self.path = Path(path_string)
        self.str_path = path_string

        if self.path.exists():
            self.files = [ShellFile(file) for file in get_files(self.path.iterdir())]
            self.directories = [ShellDirectory(dir) for dir in get_dirs(self.path.iterdir())]
            # Directories followed by files
            self.children = self.directories + self.files
        else:
            self.files = []
            self.directories = []
            self.children = []

        # So far, this used to let us get the allow/disallow properties from
        ## jinja
        self.mapping = None
        if dir_mappings is not None:
            if len(dir_mappings) > 0:
                self.mapping = dir_mappings.get_mapped_dir(self.str_path)

    @property
    def has_files(self):
        if not self.files:
            return False
        return True

    @property
    def has_subdirectories(self):
        if not self.directories:
            return False
        return True
