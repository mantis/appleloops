"""Deployement."""
import logging
import os
import subprocess  # NOQA

from distutils.version import StrictVersion
from time import sleep

# pylint: disable=relative-import
try:
    import config
    import curl_requests
    import misc
    import package
    import version
except ImportError:
    from . import config
    from . import curl_requests
    from . import misc
    from . import package
    from . import version
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)
OS_VER = version.os_vers()


class LoopDeployment(object):
    """Contains attributes relating to deployment of packages locally."""
    def __init__(self):
        # These are used for statistics. Initialise them with '0' (int).
        self._download_size = 0
        self._downloaded_size = 0

        self._install_size = 0

    def _upd_download_size(self, size):
        """Updates the 'download_size' attribute by the specified size."""
        if isinstance(size, int):
            self._download_size += size

    def _upd_downloaded_size(self, size):
        """Updates the 'downloaded_size' attribute by the specified size."""
        if isinstance(size, int):
            self._downloaded_size += size

    def _upd_install_size(self, size):
        """Updates the 'install_size' attribute by the specified size."""
        if isinstance(size, int):
            self._install_size += size

    # pylint: disable=no-self-use
    # pylint: disable=inconsistent-return-statements
    def _download(self, pkg, counter_msg):
        """Downloads a package from the specified URL."""
        if isinstance(pkg, package.LoopPackage):
            _url = pkg.DownloadURL
            _cache_race = False  # Presume all caching server packages are completely downloaded
            _debug_msg = 'Fell back {} to {}'.format(_url, pkg.DownloadURL)

            curl = curl_requests.CURL()

            if pkg.LocalDownloadURL:
                _url = pkg.LocalDownloadURL
            elif pkg.CacheDownloadURL:
                _url = pkg.CacheDownloadURL

            # Get the status of the URL to see if it exists
            req = curl_requests.CURL(url=_url)

            # Check if a caching server package is less than the expected size,
            # if this is true, then it's likely the caching server hasn't completely
            # downloaded the file yet, and will cause problems, so fall back.
            if config.CACHING_SERVER:
                try:
                    if config.REAL_DOWNLOAD_SIZE:
                        _cache_race = req.headers['Content-Length'] < pkg.RealDownloadSize
                    else:
                        _cache_race = req.headers['Content-Length'] < pkg.DownloadSize
                except KeyError:
                    if config.REAL_DOWNLOAD_SIZE:
                        _cache_race = req.headers['content-length'] < pkg.RealDownloadSize
                    else:
                        _cache_race = req.headers['content-length'] < pkg.DownloadSize

                if _cache_race:
                    _debug_msg = '{} (Possible Caching Server race condition when downloading package)'.format(_debug_msg)

            if req.status:
                if req.status in config.HTTP_OK_STATUS:
                    curl.get(url=_url, output=pkg.DownloadPath, counter_msg=counter_msg)
                elif req.status not in config.HTTP_OK_STATUS:
                    # Fallback only if the url is either a cache or pkg server
                    if _url in [pkg.LocalDownloadURL, pkg.CacheDownloadURL] or _cache_race:
                        LOG.debug(_debug_msg)

                        _url = pkg.DownloadURL

                        curl.get(url=_url, output=pkg.DownloadPath, counter_msg=counter_msg)
            elif not req.status or req.curl_error:
                # Fallback only if the url is either a cache or pkg server
                if _url in [pkg.LocalDownloadURL, pkg.CacheDownloadURL] or _cache_race:
                    LOG.debug(_debug_msg)

                    _url = pkg.DownloadURL

                    curl.get(url=_url, output=pkg.DownloadPath, counter_msg=counter_msg)
        else:
            LOG.debug('{} is {}'.format(pkg, pkg.__class__))
            return NotImplemented
    # pylint: enable=inconsistent-return-statements

    def _installer(self, cmd):
        """'installer' command execution."""
        result = None
        msg = None

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_result, p_error = process.communicate()

        if process.returncode == 0:
            msg = '  Installed _PKG_'
            LOG.info('{}: {}'.format(' '.join(cmd), p_result))

            # Debug log installer '-dumplog' value.
            try:
                _installer_dumplog_msg = p_error.decode('utf-8')
            except Exception:
                _installer_dumplog_msg = p_error

            LOG.debug(_installer_dumplog_msg)
        else:
            msg = (' Error installing _PKG_. \'/var/log/install.log\' may include additional'
                   ' information.')
            LOG.debug('{}: {}'.format(' '.join(cmd), p_error))

        result = (process.returncode, msg)

        return result

    def _install(self, pkg, counter_msg):
        """Installs a package."""
        result = None
        filename = os.path.join(config.DESTINATION_PATH, pkg.DownloadPath)

        cmd = ['/usr/sbin/installer', '-dumplog', '-pkg', filename, '-target', config.TARGET]

        if config.ALLOW_UNSECURE_PKGS:
            cmd.insert(1, '-allowUntrusted')  # Insert at index 1, shifts right

        if config.DRY_RUN:
            _msg = ' '.join(cmd)
            print('  {}'.format(_msg))
            LOG.info(_msg)
        else:
            if os.path.exists(filename):
                if not config.SILENT:
                    print('Installing {} - {}'.format(counter_msg, pkg.DownloadName))

                install_result = self._installer(cmd=cmd)
                msg = '{}'.format(install_result[1]).replace('_PKG_', pkg.DownloadName)
                result = True if install_result[0] == 0 else False

                if not config.SILENT:
                    print(msg)
            else:
                LOG.info('File not found: {}'.format(filename))
                if not config.SILENT:
                    print('File not found: {}'.format(filename))

        return result
    # pylint: enable=no-self-use

    def process(self, pkg, counter_msg):
        """Processes the download/install of packages."""
        if not config.HTTP_DMG:
            try:
                self._download(pkg=pkg, counter_msg=counter_msg)
            except Exception as e:
                LOG.info('Exception downloading: {}'.format(e.strip()))
                pass

        if config.DEPLOY_PKGS or config.FORCED_DEPLOYMENT:
            try:
                self._install(pkg=pkg, counter_msg=counter_msg)
            except Exception as e:
                LOG.info('Exception installing: {}'.format(e.strip()))
                pass

            # Installer can hang on the 'Preparing for install'
            # in macOS 11.0.1, so delay the install for a few seconds
            # to allow things to settle.
            # if StrictVersion(OS_VER) > StrictVersion('10.15.99') or config.INST_SLEEP:
            if not config.DRY_RUN and config.INST_SLEEP:
                sleep(int(config.INST_SLEEP))

            if not config.DRY_RUN:
                # Don't try and delete from DMG.
                if not config.HTTP_DMG:
                    misc.clean_up(file_path=pkg.DownloadPath)
