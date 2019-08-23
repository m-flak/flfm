import os
import shutil
import tempfile as tf

class UploadedFile:
    def __init__(self, dir_id, upload_dest, dest_filename):
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
        return os.path.exists(os.path.join(self.destination_dir, self.filename))

    @property
    def temporary(self):
        return os.path.exists(os.path.join(self.temporary_dir, self.filename))

    # Creates and opens the temporary file for writing
    def create_temporary(self):
        if not os.path.exists(self.temporary_dir):
            os.mkdir(self.temporary_dir, 0o664)

        if self._file is not None:
            self._file.close()
        self._file = open(os.path.join(self.temporary_dir, self.filename), 'wb')

    # Moves the temporary file to where it's supposed to go
    def make_permanent(self):
        if self.permanent:
            raise FileExistsError
        if not self.temporary:
            raise FileNotFoundError

        shutil.move(os.path.join(self.temporary_dir, self.filename),
                    os.path.join(self.destination_dir, self.filename))
        shutil.rmtree(self.temporary_dir, ignore_errors=True)
