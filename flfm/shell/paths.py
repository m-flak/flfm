from pathlib import Path
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


class ShellFile(ShellItem):
    file = True

    def __init__(self, path_obj):
        super().__init__(path_obj)

    def is_mimetype(self, want_type):
        our_type = filetype.guess(self.path)
        if our_type == want_type:
            return True
        return False

    def is_mimetype_family(self, want_family):
        our_type = filetype.guess(self.path)
        if our_type is None:
            return False
        if re.match(want_family, our_type.mime) is not None:
            return True
        return False

class ShellDirectory(ShellItem):
    directory = True

    def __init__(self, path_obj):
        super().__init__(path_obj)

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
        self.files = [ShellFile(file) for file in get_files(self.path.iterdir())]
        self.directories = [ShellDirectory(dir) for dir in get_dirs(self.path.iterdir())]
        # Directories followed by files
        self.children = self.directories + self.files

        self.mapping = None
        if dir_mappings is not None:
            if len(dir_mappings) > 0:
                self.mapping = dir_mappings.get_mapped_dir(self.str_path)
