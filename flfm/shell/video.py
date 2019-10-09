import struct
from abc import ABCMeta, abstractmethod
from pathlib import Path
from io import FileIO, SEEK_SET, SEEK_CUR
from .paths import ShellFile

class NoMoovAtomException(Exception):
    pass

class NoReadVideoHeaderException(Exception):
    pass

class VideoFile(ShellFile, metaclass=ABCMeta):
    def __init__(self, path_to_file):
        if isinstance(path_to_file, Path):
            super().__init__(path_to_file)
        elif isinstance(path_to_file, str):
            super().__init__(Path(path_to_file))
        else:
            raise TypeError

        if not self.is_mimetype_family('video'):
            raise ValueError("{} is not a video file.".format(self.name))

    @property
    @abstractmethod
    def video_format(self):
        pass

    @property
    @abstractmethod
    def video_width(self):
        pass

    @property
    @abstractmethod
    def video_height(self):
        pass

    @property
    @abstractmethod
    def video_wxh(self):
        pass

    @abstractmethod
    def parse_file(self):
        pass

class MP4File(VideoFile):
    def __init__(self, path_to_file):
        super().__init__(path_to_file)

        self._width = -1
        self._height = -1
        self._parsed_header = False

    @property
    def video_format(self):
        return 'mp4'

    @property
    def video_width(self):
        if self._parsed_header:
            return self._width
        self.parse_file()
        return self._width

    @property
    def video_height(self):
        if self._parsed_header:
            return self._height
        self.parse_file()
        return self._height

    @property
    def video_wxh(self):
        if self._parsed_header:
            return self._width, self._height
        self.parse_file()
        return self._width, self._height

    def _read_moov_size(self, fio_handle, start_at):
        cur_offset = fio_handle.tell()
        fio_handle.seek(start_at, SEEK_SET)
        moov_atom = fio_handle.read(8)
        # fetch a tuple of (Atom Size, Atom Name)
        moov_atom = struct.unpack('>I4s', moov_atom)

        fio_handle.seek(cur_offset, SEEK_SET)

        if moov_atom[1] != b'moov':
            raise NoMoovAtomException
        return moov_atom[0]

    def _read_mp4_container(self, fio_handle, compat_brand_end):
        track_head = b''
        alignment_corrected = False
        # Find our search limit from the moov atom's size
        total_bytes = self._read_moov_size(fio_handle, compat_brand_end)
        bytes_read = 0
        # Search for MP4 track header
        while bytes_read < total_bytes:
            buffer = fio_handle.read(4)
            # Check for & correct misalignment
            if not alignment_corrected and \
            struct.pack('>L', struct.unpack('>L', buffer)[0]<<8&0xffffffff) == b'tkh\x00':
                fio_handle.seek(-4, SEEK_CUR)
                fio_handle.seek(1, SEEK_CUR)
                alignment_corrected = True
            # Found the track_head, extract information
            if buffer == b'tkhd':
                fio_handle.seek(-8, SEEK_CUR)
                tkhd_size = fio_handle.read(4)
                tkhd_size = struct.unpack('>I', tkhd_size)[0]
                fio_handle.seek(-4, SEEK_CUR)
                track_head = fio_handle.read(tkhd_size)
                break
            bytes_read += 4

        if track_head == b'':
            raise NoReadVideoHeaderException
        # We now have the track header for the video file
        # Time to get important information like the width & height...
        # W & H = offset 0x52-0x5A ~ 82 & 90
        w, h = struct.unpack('>II', track_head[82:90])
        self._width = w
        self._height = h

    def parse_file(self):
        the_file = FileIO(self.path, 'rb')

        # the mimetype could be incorrect
        # we'll let the file decide
        if not self.video_format in self.mimetype:
            the_file.seek(0x00, SEEK_SET)
            first_12 = the_file.read(12)
            # split the dword and the ftyp
            size_dword = struct.unpack('>I', first_12[0:4])[0]
            ftyp_val = first_12[4:]
            # validate if mp4
            if size_dword > 0:
                if ftyp_val != b'ftypmp42' and ftyp_val != b'ftypisom':
                    the_file.close()
                    raise ValueError("{} is not an MP4 video.".format(self.name))
            else:
                the_file.close()
                raise ValueError("{} is not an MP4 video.".format(self.name))

        # determine the size of the `compatible_brand` field
        # this is the very first DWORD of the file
        the_file.seek(0x00, SEEK_SET)
        compat_brand_end = the_file.read(4)
        compat_brand_end = struct.unpack('>I', compat_brand_end)[0]
        compat_brand_size = compat_brand_end - 0x10
        # get the `compatible_brand` field
        the_file.seek(0x10, SEEK_SET)
        compat_brand = the_file.read(compat_brand_size)

        # PARSE THE FILE!!!
        try:
            if compat_brand == b'isommp42':
                self._read_mp4_container(the_file, compat_brand_end)
            # This compat_brand is similar to isommp42 so...
            elif compat_brand == b'isomiso2avc1mp41':
                self._read_mp4_container(the_file, compat_brand_end)
        except NoMoovAtomException:
            #TODO: ADD LOGGING
            #FIXME: MAKE THIS INTO A LOGGER
            print("WARNING: {} has no moov atom!".format(self.name))
        except NoReadVideoHeaderException:
            print("WARNING: Couldn't get information from {}!".format(self.name))

        the_file.close()
        self._parsed_header = True
