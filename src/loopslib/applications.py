"""Contains the class for Application attributes."""
import logging
import os
import re
import sys
import tempfile

from datetime import datetime
from distutils.version import LooseVersion
from glob import glob

try:
    import bad_wolf
    import config
    import curl_requests
    import misc
    import package
    import plist
except ImportError:
    from . import bad_wolf
    from . import config
    from . import curl_requests
    from . import misc
    from . import package
    from . import plist

LOG = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Application(object):
    """Class for attributes about an application."""
    def __init__(self, app):
        if app not in config.APPS.keys():
            print('Please specify an app from: \'{}\''.format(', '.join(config.APPS.keys())))
            exit(1)

        # Set some essential internal attrs to populate if app exists
        self._app = app
        self._file_path = os.path.join(config.APPLICATIONS_PATH, config.APPS[self._app])

        # Set attr used to determine app installed state
        self.is_installed = self._is_app_installed()

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

            LOG.debug('Object created: {}'.format(self.__dict__))

    def _is_app_installed(self):
        """Determines if the app is installed."""
        result = False  # Default to 'False'

        if self._file_path:
            result = os.path.exists(self._file_path)

        if not result and (config.DEPLOY_PKGS or config.FORCED_DEPLOY):
            _app_name = os.path.basename(self._file_path).replace('.app', '')
            LOG.info('{} is not installed. Skipping.'.format(_app_name))

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

            result = matching_files[-1]

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

                    if _bad_wolf_fixes:
                        _bwd = _bad_wolf_fixes.get(_pkg, None)  # A dictionary from '_bad_wolf_fixes'

                    # Merge new/existing keys from matching '_bwd'
                    if _bwd:
                        _new_pkg.update(_bwd)

                    _pkg_obj = package.LoopPackage(**_new_pkg)

                    # Only add/process packages that are _not_ 'BadWolfIgnore = True'
                    if not _pkg_obj.BadWolfIgnore:
                        result.add(_pkg_obj)

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


class RemotePlist(object):
    """Class for remote plist as a source."""
    def __init__(self, plist):
        self._plist = plist
        self._tmp_dir = os.path.join(tempfile.gettempdir(), config.BUNDLE_ID)  # Use a temporary file as the destination. This is a tuple.
        self._plist_url_path = misc.plist_url_path(self._plist)
        self._plist_failover_url_path = os.path.join(config.AUDIOCONTENT_FAILOVER_URL, 'lp10_ms3_content_2016', self._plist)

        self._all_packages = self._read_remote_plist()

    def _read_remote_plist(self):
        """Gets the property list."""
        result = None

        _basename = os.path.basename(self._plist_url_path)
        _tmp_file = os.path.join(self._tmp_dir, _basename)

        _bad_wolf_fixes = bad_wolf.BAD_WOLF_PKGS.get(_basename, None)
        _bwd = None

        _req = curl_requests.CURL(url=self._plist_url_path)

        if _req.status in config.HTTP_OK_STATUS:
            _req.get(url=self._plist_url_path, output=_tmp_file)
        else:
            _req.get(url=self._plist_failover_url_path, output=_tmp_file)

        _root = plist.readPlist(_tmp_file)

        if _root:
            result = set()

            # Apply 'Bad Wolf' pathches
            for _pkg in _root['Packages']:
                _new_pkg = _root['Packages'][_pkg].copy()  # Work on copy

                if _bad_wolf_fixes:
                    _bwd = _bad_wolf_fixes.get(_pkg, None)  # A dictionary from '_bad_wolf_fixes'

                # Merge new/existing keys from matching '_bwd'
                if _bwd:
                    _new_pkg.update(_bwd)

                _pkg_obj = package.LoopPackage(**_new_pkg)

                # Only add/process packages that are _not_ 'BadWolfIgnore = True'
                if not _pkg_obj.BadWolfIgnore:
                    result.add(_pkg_obj)

        misc.clean_up(file_path=_tmp_file)

        return result

    @property
    def mandatory_pkgs(self):
        """Returns the mandatory packages as objects in a set."""
        result = None

        result = set([_pkg for _pkg in self._all_packages if _pkg.IsMandatory])

        return result

    @property
    def optional_pkgs(self):
        """Returns the optional packages as objects in a set."""
        result = None

        result = set([_pkg for _pkg in self._all_packages if not _pkg.IsMandatory])

        return result


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
class ProcessedSource(object):
    """Class for processing a source and setting attributes about all packages.
    Takes object instances as arguments."""
    def __init__(self, apps=None, plists=None):
        self._apps = None
        self._plists = None

        if apps:
            if isinstance(apps, list):
                self._apps = [_app for _app in apps
                              if _app is not None and
                              isinstance(_app, Application) and
                              _app.is_installed]
            else:
                self._apps = None

        if plists:
            if isinstance(plists, list):
                self._plists = list()

                for _plist in plists:
                    plist = RemotePlist(plist=_plist)

                    self._plists.append(plist)
            else:
                self._plists = None

        self._valid_pkg_types = ['mandatory', 'optional']
        self._valid_sze_types = ['DownloadSize', 'InstalledSize']

        # NOTE: Some of the loops in these sets do actually
        # overlap each other, so there might be 700 when
        # combining the 'mandatory' and 'optional' sets in a pure
        # 1:1 combination, but when a 'set().union()' is done
        # this number could reduce down, to say, 682. Or other
        # such numbers depending on how packages are configured by
        # Apple.
        # So, leave these two sets as they are.
        if config.MANDATORY:
            self.mandatory = self._get_pkgs(pkg_type='mandatory')

            if self.mandatory:
                self.mandatory = sorted(self.mandatory, key=lambda pkg: pkg.DownloadName)
            else:
                self.mandatory = set()
        else:
            self.mandatory = set()

        if config.OPTIONAL:
            self.optional = self._get_pkgs(pkg_type='optional')

            if self.optional:
                self.optional = sorted(self.optional, key=lambda pkg: pkg.DownloadName)
            else:
                self.optional = set()
        else:
            self.optional = set()

        # Clean up any optional packages that are also in 'self.mandatory'
        self._clean_optionals_in_mandatory()

        # De duplicate _everything_ and create a set of all packages to wrangle..
        if self.mandatory and self.optional:
            self.all = set(self.mandatory).union(self.optional)
        elif self.mandatory and not self.optional:
            self.all = set(self.mandatory)
        elif not self.mandatory and self.optional:
            self.all = set(self.optional)
        else:
            self.all = None

        if not self.all:
            print('Nothing to process. Exiting.')
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Quick redefine 'LOG' to use 'root' namespace for neatness in log.
            LOG = logging.getLogger()
            LOG.info('------------------ Log closed on {} ------------------'.format(now))
            sys.exit(0)
        else:
            self.all = sorted(self.all, key=lambda pkg: pkg.DownloadName)

        # Quantities of each
        self.all_qty = len(self.all)
        self.mandatory_qty = len(self.mandatory)
        self.optional_qty = len(self.optional)

        self.mandatory_download_size = self._mandatory_download_size()
        self.optional_download_size = self._optional_download_size()

        self.mandatory_download_size_hr = self._mandatory_download_size_hr()
        self.optional_download_size_hr = self._optional_download_size_hr()

        self.mandatory_install_size = self._mandatory_install_size()
        self.optional_install_size = self._optional_install_size()

        self.mandatory_install_size_hr = self._mandatory_install_size_hr()
        self.optional_install_size_hr = self._optional_install_size_hr()

        self.all_download_size = self._all_download_size()
        self.all_install_size = self._all_install_size()

        self.all_download_size_hr = self._all_download_size_hr()
        self.all_install_size_hr = self._all_install_size_hr()

        # Messages
        self.mandatory_download_msg = 'Mandatory packages download size: {} ({} packages)'.format(
            self.mandatory_download_size_hr, self.mandatory_qty
        )
        self.optional_download_msg = 'Optional packages download size: {} ({} packages)'.format(
            self.optional_download_size_hr, self.optional_qty
        )

        self.mandatory_install_msg = 'Mandatory packages installation size: {}'.format(
            self.mandatory_install_size_hr
        )
        self.optional_install_msg = 'Optional packages installation size: {}'.format(
            self.optional_install_size_hr
        )

        self.all_download_msg = 'All packages download size: {} ({}) packages'.format(
            self.all_download_size_hr, self.all_qty
        )
        self.all_install_msg = 'All packages installation size: {}'.format(
            self.all_install_size_hr
        )

        self.mandatory_dld_ins_msg = 'Mandatory packages download/install size: {}/{} ({} packages)'.format(
            self.mandatory_download_size_hr, self.mandatory_install_size_hr, self.mandatory_qty
        )

        self.optional_dld_ins_msg = 'Optional packages download/install size: {}/{} ({} packages)'.format(
            self.optional_download_size_hr, self.optional_install_size_hr, self.optional_qty
        )

        self.all_dld_ins_msg = 'All packages download/install size: {}/{} ({}) packages'.format(
            self.all_download_size_hr, self.all_install_size_hr, self.all_qty
        )

        self.stats_message = '{}'.format(self.all_dld_ins_msg)

        if config.OPTIONAL:
            self.stats_message = '{}\n{}'.format(self.optional_dld_ins_msg,
                                                 self.stats_message)

        if config.MANDATORY:
            self.stats_message = '{}\n{}'.format(self.mandatory_dld_ins_msg,
                                                 self.stats_message)

    def _get_pkgs(self, pkg_type):
        """Returns a set of all mandatory or optional packages not installed.
        When 'config.DEPLOY_PKGS' is 'False', packages are considered not installed
        by default."""
        result = None

        _source = None
        _result = set()

        if pkg_type in self._valid_pkg_types:
            if self._apps:
                _source = self._apps

            if self._plists:
                _source = self._plists

            if _source:
                for _src in _source:
                    _packages = getattr(_src, '{}_pkgs'.format(pkg_type))

                    for _pkg in _packages:
                        if not _pkg.IsInstalled:
                            _result.add(_pkg)

        if _result:
            result = _result

        return result

    def _clean_optionals_in_mandatory(self):
        """Removes any optional packages that exist in the 'self.mandatory' set."""
        if self.mandatory and self.optional:
            _opt = list(self.optional)

            for _pkg in _opt:  # Iterate over a copy to avoid size change
                if _pkg in self.mandatory:
                    self.optional.remove(_pkg)

    def _all_download_size(self):
        """Returns the download size in bytes for all packages not installed."""
        result = 0
        _mandatory = 0
        _optional = 0

        _mandatory = sum([_pkg.DownloadSize for _pkg in self.mandatory])
        _optional = sum([_pkg.DownloadSize for _pkg in self.optional])

        result = _mandatory + _optional

        return result

    def _all_download_size_hr(self):
        """Returns the download size in human readable format for all packages not installed."""
        result = None

        result = misc.bytes2hr(byte=self._all_download_size())

        return result

    def _all_install_size(self):
        """Returns the install size in bytes for all packages not installed."""
        result = None

        result = sum([_pkg.InstalledSize for _pkg in self.all if not _pkg.IsInstalled])

        return result

    def _all_install_size_hr(self):
        """Returns the install size in human readable format for all packages not installed."""
        result = None

        result = misc.bytes2hr(byte=self.all_install_size)

        return result

    def _mandatory_download_size(self):
        """Returns the downlod size in bytes for all mandatory packages not installed."""
        result = 0

        result = sum([_pkg.DownloadSize for _pkg in self.mandatory if not _pkg.IsInstalled])

        return result

    def _optional_download_size(self):
        """Returns the downlod size in bytes for all optional packages not installed."""
        result = None

        result = sum([_pkg.DownloadSize for _pkg in self.optional if not _pkg.IsInstalled])

        return result

    def _mandatory_download_size_hr(self):
        """Returns the downlod size in human readable format for all mandatory packages not installed."""
        result = None

        result = misc.bytes2hr(byte=self.mandatory_download_size)

        return result

    def _optional_download_size_hr(self):
        """Returns the downlod size in human readable format for all optionalpackages not installed."""
        result = None

        result = misc.bytes2hr(byte=self.optional_download_size)

        return result

    def _mandatory_install_size(self):
        """Returns the downlod size in bytes for all mandatorypackages not installed."""
        result = None

        result = sum([_pkg.InstalledSize for _pkg in self.mandatory if not _pkg.IsInstalled])

        return result

    def _optional_install_size(self):
        """Returns the downlod size in bytes for all optional packages not installed."""
        result = None

        result = sum([_pkg.InstalledSize for _pkg in self.optional if not _pkg.IsInstalled])

        return result

    def _mandatory_install_size_hr(self):
        """Returns the downlod size in human readable format for all mandatorypackages not installed."""
        result = None

        result = misc.bytes2hr(byte=self.mandatory_install_size)

        return result

    def _optional_install_size_hr(self):
        """Returns the downlod size in human readable format for all optionalpackages not installed."""
        result = None

        result = misc.bytes2hr(byte=self.optional_install_size)

        return result
# pylint: enable=too-many-statements
# pylint: enable=too-many-branches
# pylint: enable=too-many-instance-attributes
