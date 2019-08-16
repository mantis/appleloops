"""Contains the class for Disk statistics."""
import logging
import subprocess
import sys

from os import path

try:
    import plist
except ImportError:
    from . import plist

LOG = logging.getLogger(__name__)


class DiskStats(object):
    """Class for attributes about disk usage."""
    def __init__(self, disk=None, space_used=None):
        self._disk = disk if disk and path.exists(disk) else '/'
        self._space_used = space_used if space_used else 0

    def _get_disk_stats(self):
        """Gets the amount of free space and returns a byte value."""
        result = None

        cmd = ['/usr/sbin/diskutil', 'info', '-plist', self._disk]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_result, p_error = process.communicate()

        if process.returncode is 0:
            result = plist.readPlistFromString(p_result)
        else:
            print(p_error)
            sys.exit(process.returncode)

        return result

    def _get_has_space(self):
        """Returns a True/False if there is enough free space."""
        result = None

        _freespace = self._get_disk_stats()['FreeSpace']
        LOG.debug('Freespace (disk {}): {}'.format(self._disk, _freespace))

        if all([isinstance(value, int) for value in [self._space_used, _freespace]]):
            result = self._space_used < _freespace
            LOG.debug('Space used: {}, Freespace: {}, Has enough space: {}'.format(self._space_used,
                                                                                   _freespace,
                                                                                   result))

        return result

    @property
    def freespace(self):
        """Returns the amount of free space as a byte value (int)."""
        result = None

        result = self._get_disk_stats()['FreeSpace']

        return result

    @property
    def has_space(self):
        """Returns True/False if the download and install size is less than
        the available free space on disk."""
        result = None

        result = self._get_has_space()

        return result