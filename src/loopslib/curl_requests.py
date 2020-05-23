"""Contains the class for using CURL."""
import logging
import os
import subprocess

# pylint: disable=relative-import
try:
    import config
    import curl_errors
    import misc
except ImportError:
    from . import config
    from . import curl_errors
    from . import misc
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


class CURL(object):
    """Class for using CURL."""
    def __init__(self, url=None, silent_override=False):
        self._url = url
        self._silent_override = silent_override
        self._curl_path = '/usr/bin/curl'

        self.headers = None
        self.status = None
        self.curl_error = None

        if self._url:
            self.headers = self._get_headers(obj=self._url)
            self.status = self._get_status()

    def _get_headers(self, obj):
        """Gets the headers of the provided URL, and returns the result as a dictionary.
        Does not follow redirects."""
        result = None
        redirect_statuses = ['301 Moved Permanently',
                             '302 Found',
                             '302 Moved Temporarily',
                             '303 See Other',
                             '307 Temporary Redirect',
                             '308 Permanent Redirect']

        cmd = [self._curl_path,
               config.CURL_HTTP_ARG,
               '--user-agent',
               config.USERAGENT,
               '--silent',  # Getting headers/status should always be silent.
               '-I',
               '-L',
               obj]

        if config.PROXY:
            cmd.extend(['--proxy', config.PROXY])

        if config.ALLOW_INSECURE_CURL:
            cmd.extend(['--insecure'])

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_result, p_error = process.communicate()

        # pylint: disable=too-many-nested-blocks
        if process.returncode == 0:
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
                    if (line.startswith('HTTP/1.1 ') or line.startswith('HTTP/2 ')) and ':' not in line:
                        result['Status'] = line

                        # Set the status code as a seperate value so we can minimise curl usage.
                    else:
                        if ':' in line:
                            key = line.split(': ')[0]
                            value = ''.join(line.split(': ')[1:])

                            if 'content-length' in key.lower():
                                value = int(value)

                            result[key] = value
                LOG.debug('{}: {}'.format(' '.join(cmd), result))
        elif process.returncode in [_key for _key, _value in curl_errors.CURL_ERRORS.items()]:
            _err_msg = curl_errors.CURL_ERRORS.get(process.returncode, None)

            # Set the 'self.curl_error' attribute to the error received.
            self.curl_error = {'cURL_Error': process.returncode,
                               'Error_Msg': _err_msg}

            LOG.debug('{}: {} - {}'.format(' '.join(cmd),
                                           self.curl_error.get('cURL_Error'),
                                           self.curl_error.get('Error_Msg')))
        else:
            LOG.debug('{}: {}'.format(' '.join(cmd), p_error))
            # May need to not print the error out in certain circumstances
            if not config.SILENT:
                print('Error:\n{}'.format(p_error))
        # pylint: enable=too-many-nested-blocks

        return result

    def _get_status(self):
        """Returns the HTTP status code as its own attribute."""
        result = None

        if self.headers:
            status = self.headers.get('Status', None)

            # HTTP status codes after the 'HTTP/X' part
            if status:
                result = status.split(' ')[1]

        if result:
            try:
                result = int(result)
            except Exception:
                raise

        return result

    def get(self, url, output=None, counter_msg=None, resume=True):
        """Retrieves the specified URL. Saves it to path specified in 'output' if present."""
        # NOTE: Must ignore 'dry run' state for any '.plist' file downloads.
        _fetching_plist = url.endswith('.plist')

        # Now the command.
        cmd = [self._curl_path,
               config.CURL_HTTP_ARG,
               '--user-agent',
               config.USERAGENT]

        if resume:
            cmd.extend(['-L', '-C', '-'])

        cmd.extend([url])

        if config.FORCE_DOWNLOAD and os.path.exists(output):
            if not config.DRY_RUN:
                LOG.debug('Forced download - removing: {}'.format(output))
                misc.clean_up(file_path=output)

        if config.PROXY:
            cmd.extend(['--proxy', config.PROXY])

        if config.ALLOW_INSECURE_CURL:
            cmd.extend(['--insecure'])

        if not (config.QUIET or config.SILENT or self._silent_override or _fetching_plist):
            cmd.extend(['--progress-bar'])
        elif (config.QUIET or config.SILENT or self._silent_override or _fetching_plist):
            cmd.extend(['--silent'])

        if output:
            cmd.extend(['--create-dirs', '-o', output])

        LOG.debug('CURL get: {}'.format(' '.join(cmd)))

        if not config.DRY_RUN or _fetching_plist:
            if counter_msg:
                _msg = 'Downloading {} - {}'.format(counter_msg, url)
            else:
                _msg = 'Downloading {}'.format(url)

            if config.FORCE_DOWNLOAD:
                _msg = _msg.replace('Downloading', 'Re-downloading')

            try:
                LOG.info(_msg)

                if not (config.SILENT or self._silent_override or _fetching_plist):
                    print(_msg)

                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as _e:
                LOG.debug('{}: {}'.format(' '.join(cmd), _e))
                raise _e
        elif config.DRY_RUN:
            if not config.SILENT:
                _msg = 'Download {} - {}'.format(counter_msg, url)

                print(_msg)
                LOG.info(_msg)
