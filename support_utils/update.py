#!/usr/bin/env python
import os
import re
import subprocess

from datetime import datetime
from glob import glob
from sys import argv


base_dir = os.getcwd().replace('support_utils', '')
lp10_dir = os.path.join(base_dir, 'lp10_ms3_content_2016')
lib_dir = os.path.join(base_dir, 'src', 'loopslib')
supported_file = os.path.join(lib_dir, 'supported.py')
version_file = os.path.join(lib_dir, 'version.py')
curl_path = ['/usr/bin/curl']
apple_url = 'https://audiocontentdownload.apple.com/lp10_ms3_content_2016'

apps = {'garageband': range(1010, 1099),
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

    cmd = curl_path + ['-I', '-L', url]
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

            for line in p_result:
                if re.match(r'^HTTP/\d{1}.\d{1} ', line) and ':' not in line:
                    result['Status'] = line

                    # Set the status code as a seperate value so we can minimise curl usage.
                else:
                    if ':' in line:
                        key = line.split(': ')[0]
                        value = ''.join(line.split(': ')[1:])

                        if 'content-length' in key.lower():
                            value = int(value)

                        result[key] = value
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
            result = re.sub(r'^HTTP/\d{1}.\d{1} ', '', status).split(' ')[0]

    if result:
        try:
            result = int(result)
        except Exception:
            raise

    return result


def get(url, output):
    """Retrieves the specified URL. Saves it to path specified in 'output' if present."""
    cmd = curl_path + ['-L', '-C', '-', url, '--progress-bar', '--create-dirs', '-o', output]

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

    return result


new_files = set()

for app, version in apps.items():
    for ver in version:
        filename = '{}{}.plist'.format(app, ver)
        output = os.path.join(lp10_dir, filename)
        url = '{}/{}'.format(apple_url, filename)

        headers = get_headers(url)

        if get_status(headers) == 200:
            if os.path.exists(output):
                print('Skipping {}'.format(filename))
            else:
                print('Fetching {}'.format(filename))
                get(url, output)
                new_files.add(output)

new_files = list(new_files)

if new_files:
    for nf in new_files:
        print('Converting {} to non binary plist'.format(nf))
        convert_plist(nf)


SUPPORTED = dict()

docstring = '"""Contains a basic dictionary for the supported releases of\nApple\'s audio applications, and relevant \'feed\' files."""\n'
import_line = 'import logging\n\nLOG = logging.getLogger(__name__)\n\n\n'
support_method = ('def show_supported_plists():\n'
                  '    """Prints out the supported plists for help."""\n'
                  '    print(\'Supported plist files are:\')\n\n'
                  '    for _plist in sorted(SUPPORTED.values()):\n'
                  '        print(\'  {}\'.format(_plist))\n\n'
                  '    exit(0)')

plists = glob('{}/*.plist'.format(lp10_dir))

for plist in plists:
    basename = os.path.basename(plist)
    key = basename.replace('.plist', '')

    SUPPORTED[key] = basename

with open(supported_file, 'w') as _f:
    _f.write(docstring)
    _f.write(import_line)
    _f.write('SUPPORTED = {\n')

    for key in sorted(SUPPORTED.keys()):
        _f.write("    '{}': '{}',\n".format(key, SUPPORTED[key]))

    _f.write('}\n\n')
    _f.write('LOG.debug(\'Supported: {}\'.format(SUPPORTED))\n\n\n')
    _f.write(support_method)


if 'update_ver' in argv or len(new_files) > 0:
    with open(version_file, 'r') as _f:
        doc = _f.readlines()

    for line in doc:
        if line.startswith('VERSION = '):
            index = doc.index(line)
            break

    ver = doc[index].strip().split('VERSION = ')[-1].strip('\'')
    ver = ''.join(ver.split('.'))
    ver = int(ver)

    if ver < 1000:
        ver += 1
        ver = str(ver)
        ver = '.'.join([n for n in ver])
        print('Incremented version to {}'.format(ver))
        ver = "VERSION = '{}'\n".format(ver)

        now = datetime.now().strftime('%Y-%m-%d')
        doc[index] = ver
        doc[index + 1] = 'VER_DATE = \'{}\'\n'.format(now)

    with open(version_file, 'w') as _f:
        _f.write(''.join(doc))
