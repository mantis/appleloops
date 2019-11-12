"""Contains the class for Application attributes."""
import logging
import os
import re
import sys
import tempfile

from distutils.version import LooseVersion
from glob import glob

# pylint: disable=relative-import
try:
    import bad_wolf
    import config
    import curl_requests
    import option_packs
    import package
    import plist
    import supported
except ImportError:
    from . import bad_wolf
    from . import config
    from . import curl_requests
    from . import option_packs
    from . import package
    from . import plist
    from . import supported
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Application(object):
    """Class for attributes about an application."""
    def __init__(self, app):
        if app not in [_key for _key, _value in config.APPS.items()]:
            print('Please specify an app from: \'{}\''.format(', '.join([_key for _key, _value in config.APPS.items()])))
            exit(1)

        # Set some essential internal attrs to populate if app exists
        self._app = app
        self._file_path = os.path.join(config.APPLICATIONS_PATH, config.APPS[self._app])

        # Set attr used to determine app installed state
        self.is_installed = self._is_app_installed()

        # Empty attr for option packs.
        self.option_packs = None

        if self.is_installed:
            self._resource_file_path = os.path.join(self._file_path, config.RESOURCES_PATH)
            self._app_info = self._get_app_info()

            self.plist_file_path = self._get_plist_file_path()
            self.plist_url_path = self._get_plist_url_path()
            self.plist_failover_url_path = self.plist_url_path.replace(config.AUDIOCONTENT_URL,
                                                                       config.AUDIOCONTENT_FAILOVER_URL)

            self.app_name = self._app_info.get('CFBundleName', None)
            self.bundle_id = self._app_info.get('CFBundleIdentifier', None)
            self.minimum_os_req = LooseVersion(self._app_info.get('LSMinimumSystemVersion', None))
            self.version = LooseVersion(self._app_info.get('CFBundleShortVersionString', None))

    def _is_app_installed(self):
        """Determines if the app is installed."""
        result = False  # Default to 'False'

        if self._file_path:
            result = os.path.exists(self._file_path)

        if not result and (config.DEPLOY_PKGS or config.FORCED_DEPLOYMENT):
            _app_name = os.path.basename(self._file_path).replace('.app', '')
            _msg = '{} is not installed. Skipping.'.format(_app_name)

            if not config.SILENT:
                print(_msg)

            LOG.info(_msg)

        return result

    def _get_app_info(self):
        """Returns the contents of the 'Contents/Info.plist' of the app."""
        result = None
        _info_file_path = os.path.join(self._file_path, config.CONTENTS_PATH, 'Info.plist')

        if os.path.exists(_info_file_path):
            result = plist.readPlist(_info_file_path)

        return result

    def _get_plist_file_path(self):
        """Determines the local PLIST file if the app is installed."""
        result = None

        if self._is_app_installed():
            files = glob('{}/*.plist'.format(self._resource_file_path))
            matching_files = [x for x in files if re.search(r'{}\d+.plist'.format(self._app), x)]

            # Return the last matching file as this should be the most recent
            matching_files.sort(reverse=False)

            if isinstance(matching_files, list):
                try:
                    result = matching_files[-1]
                except IndexError:  # Oh-oh! The resource might not exist, so fall back to Apple
                    LOG.debug('Resource file excpected in {} app folder not found. Falling back to Apple source.'.format(self._app))

                    _url = None
                    _failover_url = None
                    _tmp_dir = os.path.join(tempfile.gettempdir(), config.BUNDLE_ID)
                    _file = None
                    _app_ver = self._app_info.get('CFBundleShortVersionString', None).replace('.', '')
                    _supported_plists = [_value for _key, _value in supported.SUPPORTED.items() if self._app in _value]
                    _supported_plists.sort()

                    _i = 0  # Index the while loop from here.

                    while _i < len(_supported_plists):
                        _first = int(_supported_plists[_i].replace(self._app, '').replace('.plist', ''))
                        _second = None

                        try:
                            _ii = _i + 1
                            _second = int(_supported_plists[_ii].replace(self._app, '').replace('.plist', ''))
                        except KeyError:
                            _second = int(_first) + 1

                        if _first and _second:
                            if int(_app_ver) in range(_first, _second):
                                _file = _supported_plists[_i]
                                break
                        else:
                            LOG.debug('Uh oh, could not find a second file in the supported files to check version range')
                            result = None
                            break
                        _i += 1

                    if _file:
                        _url = '{}/{}/{}'.format(config.AUDIOCONTENT_URL, config.LP10_MS3_CONTENT, _file)
                        _failover_url = '{}/{}/{}'.format(config.AUDIOCONTENT_FAILOVER_URL, config.LP10_MS3_CONTENT, _file)
                        _tmp_file = os.path.join(_tmp_dir, _file)
                        _req = curl_requests.CURL(url=_url)

                        # NOTE 2019-11-04: Seems that using the 'resume' capability in cURL does not
                        # work here now for some reason, so don't resume.
                        if _req.status in config.HTTP_OK_STATUS:
                            _req.get(url=_url, output=_tmp_file, resume=False)
                        else:
                            _req.get(url=_failover_url, output=_tmp_file, resume=False)

                        if os.path.exists(_tmp_file):
                            result = _tmp_file
                        else:
                            LOG.debug('File {} not found.'.format(_tmp_file))
                            LOG.debug('URL for replacement file: {}'.format(_url))
                            LOG.debug('Failover URL for replacement file: {}'.format(_failover_url))

        return result

    def _get_plist_url_path(self):
        """Determines the Apple URL the PLIST for the specified app is found at."""
        result = None

        basename = os.path.basename(self._get_plist_file_path())

        if basename:
            result = '{}/{}/{}'.format(config.AUDIOCONTENT_URL, config.LP10_MS3_CONTENT, basename)

        return result

    def _get_packages(self):
        """Returns a set of all packages (as object instances). Also patches any 'issues'
        that resolve known issues with Apple's audiocontentdownload mirrored files."""
        result = None

        if self.plist_file_path:
            _basename = os.path.basename(self.plist_file_path)

            _bad_wolf_fixes = bad_wolf.BAD_WOLF_PKGS.get(_basename, None)
            _bwd = None

            _root = plist.readPlist(self.plist_file_path)

            if _root:
                result = set()

                # Apply 'Bad Wolf' pathches
                for _pkg in _root['Packages']:
                    _new_pkg = _root['Packages'][_pkg].copy()  # Work on copy

                    # Create a new key called 'PackageName' that
                    # contains the value '_pkg' for use with content packs.
                    _new_pkg['PackageName'] = _pkg

                    if _bad_wolf_fixes:
                        _bwd = _bad_wolf_fixes.get(_pkg, None)  # A dictionary from '_bad_wolf_fixes'

                    # Merge new/existing keys from matching '_bwd'
                    if _bwd:
                        _new_pkg.update(_bwd)

                    _pkg_obj = package.LoopPackage(**_new_pkg)

                    # pylint: disable=no-member
                    # Only add/process packages that are _not_ 'BadWolfIgnore = True'
                    if not _pkg_obj.BadWolfIgnore:
                        result.add(_pkg_obj)
                    # pylint: enable=no-member

                # Now process option packs
                self.option_packs = option_packs.OptionPack(source=_root, release=_basename).option_packs

        return result

    @property
    def mandatory_pkgs(self):
        """Returns the mandatory packages as objects in a set."""
        result = None

        result = set([_pkg for _pkg in self._get_packages() if _pkg.IsMandatory])

        return result

    @property
    def optional_pkgs(self):
        """Returns the optional packages as objects in a set."""
        result = None

        result = set([_pkg for _pkg in self._get_packages() if not _pkg.IsMandatory])

        return result
# pylint: enable=too-many-instance-attributes
