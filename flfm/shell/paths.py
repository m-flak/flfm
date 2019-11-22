"""
    Paths and Filesystem
    ~~~~~~~~~~~~~~~~~~~~

    Objects representing files, directories, and paths for FLFM.

"""
from pathlib import Path
import mimetypes
import re
import stat
import filetype

def create_proper_shellitem(str_path):
    """Creates either a :class:`ShellFile` or a :class:`ShellDirectory`
    depending on whatever the passed path actually is.

    :param str_path: A path
    :type str_path: str
    :returns: :class:`ShellFile` **OR** :class:`ShellDirectory`
    """
    untyped_path = Path(str_path)
    its_mode = untyped_path.lstat().st_mode

    # It's a directory
    if bool(stat.S_ISDIR(its_mode)):
        return ShellDirectory(untyped_path)

    # It's gotta be a file
    return ShellFile(untyped_path)

class ShellItem:
    """Base class for items contained within a
    :class:`ShellPath` container.

    :param path_obj: A **pathlib** *Path* object.
    :type path_obj: pathlib.Path
    """
    file = False #: Boolean stating if object is a file
    directory = False #: Boolean stating if object is a directory

    def __init__(self, path_obj):
        path = ''
        for p in path_obj.parts:
            if '\\' in p or '/' in p:
                continue
            path += '/{}'.format(p)
        self.name = path_obj.name
        self.path = path
        self.uri_path = self.path[1:len(self.path)]

        try:
            self.size = path_obj.lstat().st_size
        except FileNotFoundError:
            self.size = 0

    def parent_directory(self):
        """Returns the parent directory of this :class:`ShellItem`.

        :returns: str -- the path to of the parent directory.
        """
        before_name = self.path.index(self.name)
        return self.path[0:before_name].rstrip('/')

class ShellFile(ShellItem):
    """See :class:`ShellItem`.
    """
    file = True

    def __init__(self, path_obj):
        super().__init__(path_obj)
        self._mimetype = None

    def is_mimetype(self, want_type):
        """Check whether or not this file is a mimetype of ``want_type``.

        :param want_type: the full mimetype to test for.
        :type want_type: str
        :returns: bool
        """
        our_type = self.mimetype
        if our_type == want_type:
            return True
        return False

    def is_mimetype_family(self, want_family):
        """Check whether or not this file is of a specific mimetype family.

        :param want_family: The mimetype family.
        :type want_family: str
        :returns: bool

        .. note::
            The *mimetype family* refers to the first portion of the mimetype
            prior to the /.

        """
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
        """The mimetype of this :class:`ShellFile`.
        """
        if self._mimetype is None:
            try:
                self._mimetype = filetype.guess(self.path).mime
            except AttributeError:
                self._mimetype = mimetypes.guess_type(self.path)[0]
        return self._mimetype

class ShellDirectory(ShellItem):
    """See :class:`ShellItem`.
    This class can also be instantiated via :meth:`from_str_loc`.
    """
    directory = True

    def __init__(self, path_obj):
        super().__init__(path_obj)

    @classmethod
    def from_str_loc(cls, str_location):
        """Instantiates a :class:`ShellDirectory` from a string to a path.

        :param str_location: A string containing a path to a directory.
        :type str_location: str
        """
        path_object = Path(str_location)
        return cls(path_object)

    def to_shell_path(self):
        """Converts to a :class:`ShellPath`.

        :returns: A :class:`ShellPath` representing this directory.
        """
        return ShellPath(self.path)

class ShellPath:
    """A container of :class:`ShellItem` representing the files in a filesytem.

    :param path_string: A string containing a path on the local filesytem.
    :type path_string: str
    :param dir_mappings: A reference to a :class:`~flfm.shell.rules.MappedDirectories`.

    .. note::
        The ``dir_mappings`` parameter is only used for the template-side code,
        and will probably be removed in the future.

    """
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

        #: A pathlib.Path object representing this class.
        self.path = Path(path_string)
        #: The string version of this path
        self.str_path = path_string

        if self.path.exists():
            #: A list of all :class:`ShellFile` at this path.
            self.files = [ShellFile(file) for file in get_files(self.path.iterdir())]
            #: A list of all :class:`ShellDirectory` at this path.
            self.directories = [ShellDirectory(dir) for dir in get_dirs(self.path.iterdir())]
            # Directories followed by files
            #: Contains all children, both :attr:`files` & :attr:`directories`.
            self.children = self.directories + self.files
        else:
            self.files = []
            self.directories = []
            self.children = []

        # So far, this used to let us get the allow/disallow properties from
        ## jinja
        self.mapping = None
        if dir_mappings is not None:
            # check if MappedDirectories container is empty
            if not dir_mappings:
                self.mapping = None
            else:
                self.mapping = dir_mappings.get_mapped_dir(self.str_path)

    @property
    def has_files(self):
        """Whether or not this path contains files.
        """
        if not self.files:
            return False
        return True

    @property
    def has_subdirectories(self):
        """Whether or not this path has any subdirectories.
        """
        if not self.directories:
            return False
        return True
