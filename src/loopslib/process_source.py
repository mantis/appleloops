"""Contains the class for processing sources."""
import logging
import sys

from datetime import datetime

# pylint: disable=relative-import
try:
    import applications
    import config
    import misc
    import remote_plist
except ImportError:
    from . import applications
    from . import config
    from . import misc
    from . import remote_plist
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


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
                              isinstance(_app, applications.Application) and
                              _app.is_installed]
                _apps_info = ['{} ({})'.format(_a.app_name, _a.version) for _a in self._apps]
                _apps_info = ', '.join(_apps_info).strip(' ')
                _apps_discovered_msg = 'Installed apps found: {}'.format(_apps_info)

                if not config.SILENT and _apps_info:
                    print(_apps_discovered_msg)

                LOG.info(_apps_discovered_msg)
            else:
                self._apps = None

        if plists:
            if isinstance(plists, list):
                self._plists = list()

                for _plist in plists:
                    _pl = remote_plist.RemotePlist(obj=_plist)

                    self._plists.append(_pl)
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
            if not config.SILENT:
                print('Nothing to process. Exiting.')

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Quick redefine 'LOG' to use 'root' namespace for neatness in log.
            _log = logging.getLogger()
            _log.info('------------------ Log closed on {} ------------------'.format(now))
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

        self.total_size_req = self.all_download_size + self.all_install_size
        self.total_size_req_hr = misc.bytes2hr(byte=self.total_size_req)

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
