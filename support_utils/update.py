#!/usr/bin/env python
"""Simple utility to assist with updating versions and
mirrored property lists."""
from __future__ import print_function

# pylint: disable=line-too-long
# pylint: disable=too-many-nested-blocks

import os
import subprocess

from datetime import datetime
from glob import glob
from sys import argv


BASE_DIR = os.getcwd().replace('support_utils', '')
LP10_DIR = os.path.join(BASE_DIR, 'lp10_ms3_content_2016')
LIB_DIR = os.path.join(BASE_DIR, 'src', 'loopslib')
SUPPORTED_FILE = os.path.join(LIB_DIR, 'supported.py')
VERSION_FILE = os.path.join(LIB_DIR, 'version.py')
CURL_PATH = ['/usr/bin/curl', '--http1.1']
APPLE_URL = 'https://audiocontentdownload.apple.com/lp10_ms3_content_2016'

APPS = {'garageband': range(1010, 1099),
        'logicpro': range(1020, 1099),
        'mainstage': range(320, 399)}


def get_headers(url):
    """Gets the headers of the provided URL, and returns the result as a dictionary.
    Does not follow redirects."""
    result = None
    redirect_statuses = ['301 Moved Permanently',
                         '302 Found',
                         '302 Moved Temporarily',
                         '303 See Other',
                         '307 Temporary Redirect',
                         '308 Permanent Redirect']

    cmd = CURL_PATH + ['-I', '-L', url]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_result, p_error = process.communicate()

    if process.returncode is 0:
        if isinstance(p_result, bytes):
            result = dict()
            # There's a trailing `\n` in the output, so tidy it up.
            p_result = p_result.decode().strip()

            # This handles if there is a redirect
            if '\r\n\r' in p_result and any([status.lower() in p_result.lower() for status in redirect_statuses]):
                p_result = p_result.split('\r\n\r')
                p_result = p_result[-1]  # The redirect should be the last item in the output.

            # Now tidy up
            p_result = p_result.strip().splitlines()

            for _line in p_result:
                if (_line.startswith('HTTP/1.1 ') or _line.startswith('HTTP/2 ')) and ':' not in _line:
                    result['Status'] = _line

                    # Set the status code as a seperate value so we can minimise curl usage.
                else:
                    if ':' in _line:
                        _key = _line.split(': ')[0]
                        value = ''.join(_line.split(': ')[1:])

                        if 'content-length' in _key.lower():
                            value = int(value)

                        result[_key] = value
    else:
        print('Error:\n{}'.format(p_error))

    return result


def get_status(headers):
    """Returns the HTTP status code as its own attribute."""
    result = None

    if headers:
        status = headers.get('Status', None)

        # HTTP status codes should be the first three numbers of this header.
        if status:
            result = status.split(' ')[1]

    if result:
        try:
            result = int(result)
        except Exception:
            raise

    return result


def get(url, output):
    """Retrieves the specified URL. Saves it to path specified in 'output' if present."""
    cmd = CURL_PATH + ['-L', '-C', '-', url, '--progress-bar', '--create-dirs', '-o', output]

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        raise


def convert_plist(plist_path):
    """Used to convert a binary property list file to a format readable by Python 2.
    The plist is converted out to stdout and then returned as a string."""
    result = None
    plutil = '/usr/bin/plutil'

    if not os.path.exists(plutil):
        print('{} is required. Exiting.'.format(plutil))
        exit(1)

    cmd = [plutil, '-convert', 'xml1', plist_path]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_result, p_error = process.communicate()

    if process.returncode is 0:
        result = p_result
    else:
        print(p_error)

    return result


NEW_FILES = set()

for app, version in APPS.items():
    for ver in version:
        filename = '{}{}.plist'.format(app, ver)
        _output = os.path.join(LP10_DIR, filename)
        _url = '{}/{}'.format(APPLE_URL, filename)

        _headers = get_headers(_url)

        if get_status(_headers) == 200:
            if os.path.exists(_output):
                print('Skipping {}'.format(filename))
            else:
                print('Fetching {}'.format(filename))
                get(_url, _output)
                NEW_FILES.add(_output)

NEW_FILES = list(NEW_FILES)

if NEW_FILES:
    for nf in NEW_FILES:
        print('Converting {} to non binary plist'.format(nf))
        convert_plist(nf)


SUPPORTED = dict()

DOCSTRING = '"""Contains a basic dictionary for the supported releases of\nApple\'s audio applications, and relevant \'feed\' files."""\n'
IMPORT_LINE = 'import logging\n\nLOG = logging.getLogger(__name__)\n\n\n'
SUPPORT_METHOD = ('def show_supported_plists():\n'
                  '    """Prints out the supported plists for help."""\n'
                  '    print(\'Supported plist files are:\')\n\n'
                  '    for _plist in sorted(SUPPORTED.values()):\n'
                  '        print(\'  {}\'.format(_plist))\n\n'
                  '    exit(0)\n')

PLISTS = glob('{}/*.plist'.format(LP10_DIR))

for plist in PLISTS:
    basename = os.path.basename(plist)
    _key = basename.replace('.plist', '')

    SUPPORTED[_key] = basename

with open(SUPPORTED_FILE, 'w') as _f:
    _f.write(DOCSTRING)
    _f.write(IMPORT_LINE)
    _f.write('SUPPORTED = {\n')

    for _key, _value in sorted(SUPPORTED.items()):
        _f.write("    '{}': '{}',\n".format(_key, SUPPORTED[_key]))

    _f.write('}\n\n')
    _f.write('LOG.debug(\'Supported: {}\'.format(SUPPORTED))\n\n\n')
    _f.write(SUPPORT_METHOD)


if 'update_ver' in argv or NEW_FILES:
    with open(VERSION_FILE, 'r') as _f:
        DOC = _f.readlines()

    for _line in DOC:
        if _line.startswith('VERSION = '):
            index = DOC.index(_line)
            break

    VER = DOC[index].strip().split('VERSION = ')[-1].strip('\'')
    VER = ''.join(VER.split('.'))
    VER = int(VER)

    if VER < 1000:
        VER += 1
        VER = str(VER)
        VER = '.'.join([n for n in VER])
        print('Incremented version to {}'.format(VER))
        VER = "VERSION = '{}'\n".format(VER)

        NOW = datetime.now().strftime('%Y-%m-%d')
        DOC[index] = VER
        DOC[index + 1] = 'VER_DATE = \'{}\'\n'.format(NOW)

    with open(VERSION_FILE, 'w') as _f:
        _f.write(''.join(DOC))
