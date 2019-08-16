"""Deployement."""
import logging
import os
import shutil
import subprocess  # NOQA

try:
    import config
    import curl_requests
    import misc
    import package
except ImportError:
    from . import config
    from . import curl_requests
    from . import misc
    from . import package

LOG = logging.getLogger(__name__)


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

    # pylint: disable=inconsistent-return-statements
    def _download(self, pkg):
        """Downloads a package from the specified URL."""
        if isinstance(pkg, package.LoopPackage):
            _url = pkg.DownloadURL

            curl = curl_requests.CURL()

            if pkg.LocalDownloadURL:
                _url = pkg.LocalDownloadURL
            elif pkg.CacheDownloadURL:
                _url = pkg.CacheDownloadURL

            # Get the status of the URL to see if it exists
            req = curl_requests.CURL(url=_url)

            if req.status:
                if req.status in config.HTTP_OK_STATUS:
                    curl.get(url=_url, output=pkg.DownloadPath)
                elif req.status not in config.HTTP_OK_STATUS:
                    # Fallback only if the url is either a cache or pkg server
                    if _url in [pkg.LocalDownloadURL, pkg.CacheDownloadURL]:
                        LOG.debug('Fell back {} to {}'.format(_url, pkg.DownloadURL))
                        _url = pkg.DownloadURL
                        curl.get(url=_url, output=pkg.DownloadPath)
            elif not req.status or req.curl_error:
                # Fallback only if the url is either a cache or pkg server
                if _url in [pkg.LocalDownloadURL, pkg.CacheDownloadURL]:
                    LOG.debug('Fell back {} to {}'.format(_url, pkg.DownloadURL))
                    _url = pkg.DownloadURL
                    curl.get(url=_url, output=pkg.DownloadPath)
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

        if process.returncode is 0:
            msg = '  Installed _PKG_'
            LOG.info('{}: {}'.format(' '.join(cmd), p_result))
        else:
            msg = (' Error installing _PKG_. \'/var/log/install.log\' may include additional'
                   ' information.')
            LOG.debug('{}: {}'.format(' '.join(cmd), p_error))

        result = (process.returncode, msg)

        return result

    # pylint: disable=no-self-use
    def _install(self, pkg):
        """Installs a package."""
        result = None
        filename = os.path.join(config.DESTINATION_PATH, pkg.DownloadPath)

        cmd = ['/usr/sbin/installer', '-pkg', filename, '-target', config.TARGET]

        if config.ALLOW_UNSECURE_PKGS:
            cmd.insert(1, '--allowUntrusted')  # Insert at index 1, shifts right

        if config.DRY_RUN:
            _msg = ' '.join(cmd)
            print(_msg)
            LOG.info(_msg)
        else:
            if os.path.exists(filename):
                print('Installing {}'.format(pkg.DownloadName))

                install_result = self._installer(cmd=cmd)
                msg = '{}'.format(install_result[1]).replace('_PKG_', pkg.DownloadName)
                result = True if install_result[0] is 0 else False

                if not config.SILENT:
                    print(msg)
            else:
                print('File not found: {}'.format(filename))
                LOG.info('File not found: {}'.format(filename))

        return result
    # pylint: enable=no-self-use

    def tidy_up(self):
        """Tidy's up working directories."""
        if not config.DRY_RUN:
            # Don't need to tidy up if building a DMG because sparseimage.
            if not config.DMG_FILE and not config.DMG_VOLUME_MOUNTPATH:
                try:
                    shutil.rmtree(config.DESTINATION_PATH)
                except OSError as e:
                    LOG.debug('Error removing: {} - {}'.format(config.DESTINATION_PATH, e))
                    raise

    def process(self, pkg):
        """Processes the download/install of packages."""
        if not config.HTTP_DMG:
            self._download(pkg=pkg)

        if config.DEPLOY_PKGS or config.FORCED_DEPLOYMENT:
            self._install(pkg=pkg)
            misc.clean_up(file_path=pkg)
