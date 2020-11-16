"""Contains basic information about the appleloops package and functions relating to
version checking."""
import logging
import subprocess

from distutils.version import LooseVersion
from sys import version_info

LOG = logging.getLogger(__name__)

AUTHOR = 'Carl Windus'
VERSION = '3.2.1'
VER_DATE = '2020-11-15'
LICENSE = 'Apache License, Version 2.0'
COPYRIGHT = 'Copyright 2019, {}'.format(AUTHOR)
VERSION_STR = 'appleloops v{} built {}, {}'.format(VERSION, VER_DATE, LICENSE)
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


def os_vers(arg='productVersion'):
    """Return OS version."""
    result = None

    cmd = ['/usr/bin/sw_vers', '-{}'.format(arg)]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r, e = p.communicate()

    if r and isinstance(r, bytes):
        r = r.decode('utf-8')

    if r and isinstance(r, bytes):
        r = r.decode('utf-8')

    if p.returncode == 0 and r:
        result = r.strip()
    elif p.returncode != 0 and e:
        LOG.debug('Error returning \'sw_ver\': {}'.format(e.strip()))

    return result
