"""Contains basic functions for reading/converting property lists."""
import logging
import plistlib
import subprocess
import xml

from distutils.version import LooseVersion

# pylint: disable=relative-import
try:
    import version
except ImportError:
    from . import version
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


class ConversionException(Exception):
    """Exception handler for converting binary property list to stdout string."""
    pass


def is_binary(plist_path):
    """Checks if a plist is a binary or not."""
    result = False
    with open(plist_path, 'rb') as _f:
        for _block in _f:
            if b'\0' in _block:
                result = True
                break

    return result


def convert(obj):
    """Converts a binary property list file and returns it as a string."""
    result = None

    _err_chars = {
        '\xe2\x80\x9c': '"',
        '\xe2\x80\x9d': '"',
        '\xe2\x80\x99': "'"}

    cmd = ['/usr/bin/plutil', '-convert', 'xml1', '-o', '-', obj]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_result, p_error = process.communicate()  # 'p_error' is useless. Errors goe to stdout.

    if process.returncode is 0:
        result = p_result
    else:
        p_error = p_result

        if isinstance(p_error, str):
            for _k, _v in _err_chars.items():
                p_error = p_result.replace(_k, _v)

        p_error = p_error.strip()

        # LOG.debug(p_error)
        raise ConversionException(p_error)

    return result


# pylint: disable=invalid-name
def readPlist(plist_path):
    """A wrapper function to read property list files with either Python 2 or Python 3 versions.
    If the file is a binary file, and the Python version is 2.7+, the file is converted using 'plutil'."""
    result = None

    # Python 3.4.0+ deprecates the old '.readPlist*' methods.
    if LooseVersion(version.PYTHON_VER) > LooseVersion('3.4.0'):
        with open(plist_path, 'rb') as plistfile:
            # pylint: disable=no-member
            result = plistlib.load(plistfile)
            # pylint: enable=no-member
    elif version.in_version_range('2.7.0', version.PYTHON_VER, '3.3.99'):
        if is_binary(plist_path):
            plist_str = convert(plist_path)
            result = plistlib.readPlistFromString(plist_str)
        else:
            result = plistlib.readPlist(plist_path)

    return result


def readPlistFromString(obj):
    """A wrapper function to read property lists from string with either Python 2 or Python 3 versions."""
    result = None

    # Python 3.4.0+ deprecates the old '.readPlist*' methods.
    if LooseVersion(version.PYTHON_VER) > LooseVersion('3.4.0'):
        # pylint: disable=no-member
        result = plistlib.loads(obj)
        # pylint: enable=no-member
    elif version.in_version_range('2.7.0', version.PYTHON_VER, '3.3.99'):
        try:
            result = plistlib.readPlistFromString(obj)
        except xml.parsers.expat.ExpatError:
            result = plistlib.readPlistFromString(obj)

    return result
# pylint: enable=invalid-name
