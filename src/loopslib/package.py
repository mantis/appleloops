"""Contains the class for creating package objects."""
import logging
import subprocess

from datetime import datetime
from distutils.version import LooseVersion
from os import path

try:
    from urlparse import urlparse  # Python 2 package
except ImportError:
    from urllib.parse import urlparse  # Python 3 package

# pylint: disable=relative-import
try:
    import config
    import curl_requests
    import misc
    import plist
except ImportError:
    from . import config
    from . import curl_requests
    from . import misc
    from . import plist
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
# pylint: disable=no-member
class LoopPackage(object):
    """Attributes for Packages to be installed."""
    VALID_KWARGS = {'ContainsAlchemyFiles': False,
                    'ContainsAppleLoops': False,
                    'ContainsGarageBandLegacyInstruments': False,
                    'DownloadName': None,
                    'DownloadSize': None,
                    'FileCheck': None,
                    'InstalledSize': None,
                    'IsMandatory': False,
                    'MissingContentOnly': False,
                    'MissingDownloadOnly': False,
                    'NeverUpdateLegacy': False,
                    'PackageID': None,
                    'PackageVersion': '0.0.0',
                    'DownloadURL': None,
                    'LocalDownloadURL': None,
                    'CacheDownloadURL': None,
                    'UpgradePackage': None,
                    'InstalledVersion': None,
                    'InstalledDate': None,
                    'RealDownloadSize': None,
                    'HumanInstalledSize': None,
                    'HumanDownloadSize': None,
                    'HumanRealDownloadSize': None,
                    'DownloadPath': None,
                    'BadWolfIgnore': None}

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def __init__(self, **kwargs):
        # Set attributes based on 'VALID_KWARGS'
        for kwarg, value in self.VALID_KWARGS.items():
            if kwarg in kwargs.keys():
                setattr(self, kwarg, kwargs.get(kwarg, None))
            else:
                setattr(self, kwarg, value)

        # pylint: disable=access-member-before-definition
        # Fix any instances where the 'PackageID' contains spaces.
        if hasattr(self, 'PackageID'):
            self.PackageID = self.PackageID.replace('. ', '.')

        # Fix the Apple 'PackageVersion' attribute to a 'LooseVersion' type.
        if hasattr(self, 'PackageVersion'):
            if isinstance(self.PackageVersion, (float, int)):
                self.PackageVersion = u'{}'.format(self.PackageVersion)

            self.PackageVersion = LooseVersion(self.PackageVersion)

        # Convert 'DownloadSize' and 'InstalledSize' to int
        if hasattr(self, 'DownloadSize'):
            # if self.DownloadSize:
            self.DownloadSize = int(self.DownloadSize)
            self.HumanDownloadSize = misc.bytes2hr(byte=self.DownloadSize)

        if hasattr(self, 'InstalledSize'):
            # if self.InstalledSize:
            self.InstalledSize = int(self.InstalledSize)
            self.HumanInstalledSize = misc.bytes2hr(byte=self.InstalledSize)

        # Now handle some of the appleloops specific attributes.
        if hasattr(self, 'DownloadName'):
            basename = path.basename(self.DownloadName)
            self.DownloadURL = '{}/{}/{}'.format(config.AUDIOCONTENT_URL,
                                                 config.LP10_MS3_CONTENT,
                                                 basename)

            lp10_str = 'lp10_ms3_content_2016'
            if '../lp10_ms3_content_2013/' in self.DownloadName:
                lp10_str = 'lp10_ms3_content_2013'
                self.DownloadURL = self.DownloadURL.replace('lp10_ms3_content_2016', lp10_str)

                # Can probably get away with removing the '2013' path from the 'DownloadName' attr.
                self.DownloadName = self.DownloadName.replace('../{}/'.format(lp10_str), '')

            # Handle if there's a DMG to build/deploy from
            if config.DMG_FILE or config.HTTP_DMG:
                _dest_path = config.DMG_VOLUME_MOUNTPATH
            else:
                _dest_path = config.DESTINATION_PATH if config.DESTINATION_PATH else config.DEFAULT_DEST

            self.DownloadPath = path.join(_dest_path, lp10_str, self.DownloadName)

        if hasattr(self, 'DownloadURL'):
            if config.LOCAL_HTTP_SERVER:
                # If this isn't a HTTP DMG being mounted, set the download url
                if not config.HTTP_DMG:
                    self.LocalDownloadURL = self.DownloadURL.replace(config.AUDIOCONTENT_URL,
                                                                     config.LOCAL_HTTP_SERVER)

            if config.CACHING_SERVER:
                parsed_url = urlparse(self.DownloadURL)
                self.CacheDownloadURL = '{}{}?source={}'.format(config.CACHING_SERVER,
                                                                parsed_url.path,
                                                                parsed_url.netloc)
        # pylint: enable=access-member-before-definition

        # CURL requests for actual download sizes but only if specified.
        if config.REAL_DOWNLOAD_SIZE:
            if self.LocalDownloadURL:
                req = curl_requests.CURL(url=self.LocalDownloadURL)
            elif not self.LocalDownloadURL:
                req = curl_requests.CURL(url=self.DownloadURL)

            if req.status == 200:
                try:
                    self.RealDownloadSize = req.headers['Content-Length']
                except KeyError:
                    try:
                        self.RealDownloadSize = req.headers['content-length']
                    except KeyError:
                        pass

            if self.RealDownloadSize:
                self.HumanRealDownloadSize = misc.bytes2hr(byte=self.RealDownloadSize)
    # pylint: enable=too-many-statements
    # pylint: enable=too-many-branches

    # pylint: disable=no-else-return
    def __hash__(self):
        """Hash a tuple (immutable) containing the package 'DownloadName' attribute."""
        if isinstance(self, LoopPackage):
            return hash(('DownloadName', self.DownloadName))
        else:
            return NotImplemented

    def __eq__(self, other):
        """Used for testing equality of a package instance based on the package 'DownloadName'
        attribute."""
        if isinstance(self, LoopPackage):
            return self.DownloadName == other.DownloadName
        else:
            return NotImplemented

    def __ne__(self, other):
        """Used for testing 'not' equality of a package instance based on the package
        'DownloadName' attribute. Implemented for Python 2.7 compatibility."""
        if isinstance(self, LoopPackage):
            return not self.DownloadName == other.DownloadName
        else:
            return NotImplemented
    # pylint: enable=no-else-return

    # pylint: disable=attribute-defined-outside-init
    def _is_pkg_installed(self):
        """Determines if the specified package is installed."""
        result = None

        # Only test if the package is installed if this is a deployment run.
        # Presume not installed for all other circumstances.
        if config.DEPLOY_PKGS:
            files_installed = None
            pkginfo = None
            # missing_content_only = None

            if hasattr(self, 'PackageID'):
                pkginfo = InstalledPackageInfo(obj=self.PackageID)
                pkg_bundle = self.PackageID == pkginfo.pkgid

                # Set some other package attributes that might be useful
                self.InstalledVersion = pkginfo.pkg_version
                self.InstalledDate = pkginfo.install_time

            if hasattr(self, 'FileCheck'):
                if isinstance(self.FileCheck, list):
                    files_installed = all(path.exists(f) for f in self.FileCheck)
                elif isinstance(self.FileCheck, str):
                    files_installed = path.exists(self.FileCheck)

            # if hasattr(self, 'MissingContentOnly'):
            #     if all([check is True for check in [files_installed, pkg_bundle]]):
            #         if self.MissingContentOnly:
            #             # Set this to 'False' so that the all() below trips.
            #             missing_content_only = False
            #         elif not self.MissingContentOnly:
            #             missing_content_only = True

            # result = all([check is True for check in [files_installed, pkg_bundle, missing_content_only]])
            result = all([check is True for check in [files_installed, pkg_bundle]])
        elif not config.DEPLOY_PKGS:
            result = False

        return result
    # pylint: enable=attribute-defined-outside-init

    def _upgrade_package(self):
        """Determines if an installed package should be upgraded on the basis of version numbers."""
        result = None

        if self._is_pkg_installed():
            if hasattr(self, 'PackageVersion') and hasattr(self, 'InstalledVersion'):
                result = self.InstalledVersion < self.PackageVersion

        return result

    @property
    def IsInstalled(self):
        """Attribute returning True/False if the package is installed."""
        result = None

        if not config.FORCED_DEPLOYMENT:
            result = self._is_pkg_installed()
        elif config.FORCED_DEPLOYMENT:
            # When forcing a deployment, ignore all install states.
            result = False

        return result


class InstalledPackageInfo(object):
    """Attributes of packages installed."""
    VALID_PKG_INFO_KEYS = {'install_location': None,
                           'install_time': None,
                           'pkg_version': False,
                           'pkgid': None,
                           'receipt_plist_version': None,
                           'volume': None}

    def __init__(self, obj):
        # Set up all attributes, they get updated later with relevant values.
        for key, value in self.VALID_PKG_INFO_KEYS.items():
            setattr(self, key, value)

        # Now query with the macOS 'pkgutil' binary.
        pkginfo = self._pkginfo(package_id=obj)

        if pkginfo:
            for key, value in pkginfo.items():
                setattr(self, key, value)

    # pylint: disable=no-else-return
    def __hash__(self):
        """Hash a tuple (immutable) containing the 'pkgid' attribute."""
        if isinstance(self, InstalledPackageInfo):
            return hash(('pkgid', self.pkgid))
        else:
            return NotImplemented

    def __eq__(self, other):
        """Used for testing equality of a package instance based on the 'pkginfo' attribute."""
        if isinstance(self, InstalledPackageInfo):
            return self.pkgid == other.pkgid
        else:
            return NotImplemented

    def __ne__(self, other):
        """Used for testing 'not' equality  'pkginfo' attribute.
        Implemented for Python 2.7 compatibility."""
        if isinstance(self, InstalledPackageInfo):
            return not self.pkgid == other.pkgid
        else:
            return NotImplemented
    # pylint: enable=no-else-return

    # pylint: disable=no-self-use
    def _pkginfo(self, package_id):
        """Retrieves package information for a specific Package ID using the macOS 'pkgutil' binary."""
        result = None

        cmd = ['/usr/sbin/pkgutil', '--pkg-info-plist', package_id]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_result, p_error = process.communicate()

        if process.returncode is 0:
            _result = plist.readPlistFromString(p_result)
            LOG.debug(p_result)

            if _result:
                result = dict()
                for key, value in _result.items():
                    if key == 'install-time':
                        value = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                    elif key == 'pkg-version':
                        value = LooseVersion(value)

                    result[key.replace('-', '_')] = value
            else:
                result = False
        else:
            LOG.debug(p_error)
            result = False

        LOG.debug('{}: {}'.format(' '.join(cmd), result))
        return result
    # pylint: enable=no-self-use
# pylint: enable=no-member
# pylint: enable=too-many-instance-attributes
# pylint: enable=invalid-name
