"""Contains the class for Remote PLIST attributes."""
import logging
import os
import tempfile

try:
    import bad_wolf
    import config
    import curl_requests
    import misc
    import option_packs
    import package
    import plist
except ImportError:
    from . import bad_wolf
    from . import config
    from . import curl_requests
    from . import misc
    from . import option_packs
    from . import package
    from . import plist

LOG = logging.getLogger(__name__)


class RemotePlist(object):
    """Class for remote plist as a source."""
    def __init__(self, plist):
        self._plist = plist
        self._tmp_dir = os.path.join(tempfile.gettempdir(), config.BUNDLE_ID)  # Use a temporary file as the destination. This is a tuple.
        self._plist_url_path = misc.plist_url_path(self._plist)
        self._plist_failover_url_path = os.path.join(config.AUDIOCONTENT_FAILOVER_URL, 'lp10_ms3_content_2016', self._plist)

        self._all_packages = self._read_remote_plist()

        # Empty attr for option packs.
        self.option_packs = None

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

            # Now process option packs
            self.option_packs = option_packs.OptionPack(source=_root, release=_basename).option_packs

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
