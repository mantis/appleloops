"""Contains basic information about the appleloops package and functions relating to
version checking."""
import logging

from distutils.version import LooseVersion
from sys import version_info

LOG = logging.getLogger(__name__)

AUTHOR = 'Carl Windus'
VERSION = '3.1.9'
VER_DATE = '2020-07-20'
LICENSE = 'Apache License, Version 2.0'
COPYRIGHT = 'Copyright 2019, {}'.format(AUTHOR)
VERSION_STR = 'appleloops {} ({})'.format(VERSION, LICENSE)
USERAGENT = 'appleloops/{}'.format(VERSION)
PYTHON_VER = '{}.{}.{}'.format(version_info.major, version_info.minor, version_info.micro)


def in_version_range(min_version, compare_version, max_version):
    """Checks if a provided version string is in the ranges provided."""
    result = None

    if all([isinstance(ver, (str, unicode)) for ver in [min_version, compare_version, max_version]]):
        result = (LooseVersion(min_version) <=
                  LooseVersion(compare_version) <=
                  LooseVersion(max_version))

    return result
