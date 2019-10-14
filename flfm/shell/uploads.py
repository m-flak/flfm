"""
    Uploaded Files
    ~~~~~~~~~~~~~~

    Files in the process of being uploaded and copied to their destination.

"""
import os
import shutil
import tempfile as tf
from pathlib import Path
from .paths import ShellFile

class UploadedShellFileMeta(type):
    """Metaclass for meshing of the :class:`UploadedFile` and
    :class:`~flfm.shell.paths.ShellFile` types.
    """
    def __new__(mcls, name, bases, attrs):
        new_attrs = dict()

        for attr_name, attr_value in attrs.items():
            if ShellFile.__name__ in name and attr_name == 'file':
                new_attrs['__file'] = attr_value
            else:
                new_attrs[attr_name] = attr_value

        return super(UploadedShellFileMeta, mcls).__new__(mcls, name, bases,
                                                          new_attrs)

class UploadedFile(ShellFile, metaclass=UploadedShellFileMeta):
    """Object representing a file that has been upload and is in the process of
    being copied from a temporary location to a permanent location.

    :param dir_id: A random identifier for a temporary directory.
    :type dir_id: int / str
    :param upload_dest: A destination folder to copy ``dest_filename`` to.
    :type upload_dest: str
    :param dest_filename: The name of the destination file.
    :type dest_filename: str

    .. note::
        It is assumed that you will wait until after calling :meth:`make_permanent`
        before using any of the methods inherited from
        :class:`~flfm.shell.paths.ShellFile`.

    """
    def __init__(self, dir_id, upload_dest, dest_filename):
        ShellFile.__init__(self, Path(os.path.join(upload_dest, dest_filename)))
        temp_dir = dir_id
        if not isinstance(dir_id, str):
            temp_dir = str(dir_id)

        self.temporary_dir = os.path.join(tf.gettempdir(), temp_dir)
        self.destination_dir = upload_dest
        self.filename = dest_filename
        self._file = None

    def __del__(self):
        if self._file is not None:
            self._file.close()

    # File handle will be read-only, UNLESS create_temporary is called
    @property
    def file(self):
        """The file handle. **READ-ONLY** *unless* :meth:`create_temporary` is
        called.
        """
        if self._file is None:
            if self.permanent and self.temporary:
                raise FileExistsError
            if self.permanent:
                self._file = open(os.path.join(self.destination_dir,
                                               self.filename), 'rb')
            elif self.temporary:
                self._file = open(os.path.join(self.temporary_dir,
                                               self.filename), 'rb')
            else:
                raise FileNotFoundError
        return self._file

    @property
    def permanent(self):
        """Is a file permanent? Has it been copied over??

        :returns: bool
        """
        return os.path.exists(os.path.join(self.destination_dir, self.filename))

    @property
    def temporary(self):
        """Is a file temporary? Has it yet to be copied over??

        :returns: bool
        """
        return os.path.exists(os.path.join(self.temporary_dir, self.filename))

    def create_temporary(self):
        """Creates and opens the temporary file for writing.
        """
        if not os.path.exists(self.temporary_dir):
            os.mkdir(self.temporary_dir, 0o774)

        if self._file is not None:
            self._file.close()
        self._file = open(os.path.join(self.temporary_dir, self.filename), 'wb')

    def make_permanent(self):
        """Moves the temporary file to where it's supposed to go.
        """
        if self.permanent:
            raise FileExistsError
        if not self.temporary:
            raise FileNotFoundError

        shutil.move(os.path.join(self.temporary_dir, self.filename),
                    os.path.join(self.destination_dir, self.filename))
        shutil.rmtree(self.temporary_dir, ignore_errors=True)
