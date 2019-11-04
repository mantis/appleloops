"""Contains the class for constructing the arguments for command line use."""
import argparse
import logging
import os
import re
import sys

try:
    from urlparse import urlparse  # Python 2 package
except ImportError:
    from urllib.parse import urlparse  # Python 3 package

from operator import attrgetter

# pylint: disable=relative-import
try:
    import arguments_config
    import compare
    import config
    import misc
    import supported
except ImportError:
    from . import arguments_config
    from . import compare
    from . import config
    from . import misc
    from . import supported
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)

# pylint: disable=too-many-locals


class SaneUsageFormat(argparse.HelpFormatter):
    """Makes the help output somewhat more sane. Code used was from Matt Wilkie.
    http://stackoverflow.com/questions/9642692/argparse-help-without-duplicate-allcaps/9643162#9643162
    """
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))

        super(SaneUsageFormat, self).add_arguments(actions)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)

            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)

                for option_string in action.option_strings:
                    parts.append(option_string)

                return '{} {}'.format(', '.join(parts), args_string)

            return ', '.join(parts)

    @classmethod
    def _get_default_metavar_for_optional(cls, action):
        return action.dest.upper()

    @classmethod
    def _get_default_metavar_for_positional(cls, action):
        return action.dest.upper()


class LoopsArguments(object):
    """Handles argument construction and parsing."""
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=SaneUsageFormat)
        self._verbose_args = self.parser.add_mutually_exclusive_group()
        self._deploy_args = self.parser.add_mutually_exclusive_group()
        self._plist_args = self.parser.add_mutually_exclusive_group()

        self._valid_url_schemes = ['http', 'https']

        self._construct_args()

    def _construct_args(self):
        """Constructs arguments (internal)."""
        for _value in arguments_config.CL_ARGUMENTS.values():
            args = _value['args']
            kwargs = _value['kwargs']

            self.parser.add_argument(*args, **kwargs)

        for _value in arguments_config.CL_EXCL_GRP_ARGS_01.values():
            args = _value['args']
            kwargs = _value['kwargs']

            self._verbose_args.add_argument(*args, **kwargs)

        for _value in arguments_config.CL_EXCL_GRP_ARGS_02.values():
            args = _value['args']
            kwargs = _value['kwargs']

            self._deploy_args.add_argument(*args, **kwargs)

        for _value in arguments_config.CL_EXCL_GRP_ARGS_03.values():
            args = _value['args']
            kwargs = _value['kwargs']

            self._plist_args.add_argument(*args, **kwargs)

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def parse_args(self):
        """Parses arguments."""
        result = None
        _name = sys.argv[0]
        _err_msg = '{}: error: argument'.format(_name)

        if len(sys.argv) == 1:
            self.parser.print_help(sys.stderr)
            sys.exit(1)

        result = self.parser.parse_args()

        # Manual argument checks that can't be done by argparse.
        if result.apfs_dmg:
            _arg = '--APFS'

            if not result.build_dmg:
                self.parser.print_usage(sys.stderr)
                _msg = '{} {}: --APFS: not allowed with argument -b/--build-dmg'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        # Check that at least on of the three apps is provided for download flag '-a/--apps'
        if result.apps == 'allpkgs' or 'allpkgs' in result.apps:
            result.apps = config.ALL_LATEST_APPS
        elif result.apps:
            _arg = '-a/--apps'
            _apps = [_app for _app, _value in config.APPS.items()]
            _apps.extend(['allpkgs'])
            _apps.sort()
            _choices = ', '.join(["'{}'".format(_app) for _app in _apps])

            if not any([app in result.apps for app in _apps]):
                self.parser.print_usage(sys.stderr)
                _msg = '{} {}: expected one argument: (choose from {})'.format(_err_msg, _arg, _choices)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        # Handle plist argument exceptions
        if result.plists:
            _arg = '-p/--plists'
            # Make sure all items passed end with plist
            _supported = config.SUPPORTED_PLISTS.keys()
            _choices = ["'{}'".format(_plist) for _plist in _supported]
            _choices.sort()
            _choices = ', '.join(_choices)
            _choices = '\'allpkgs\', {}'.format(_choices)

            if result.plists == 'allpkgs' or 'allpkgs' in result.plists:
                result.plists = [config.SUPPORTED_PLISTS.get(_plist) for _plist in config.ALL_LATEST_PLISTS]
            elif not any([_plist in _supported for _plist in result.plists]):
                _msg = '{} {}: excpected one argument: (choose from {})'.format(_err_msg, _arg, _choices)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)
            else:
                result.plists = [config.SUPPORTED_PLISTS.get(_plist) for _plist in result.plists]

            if not (result.mandatory or result.optional):
                self.parser.print_usage(sys.stderr)
                _msg = '{} {}: must provide at least -m/--mandatory or -o/--optional or both'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

            if result.deployment or result.force_deployment:
                self.parser.print_usage(sys.stderr)
                _msg = '{}: {}: not allowed with argument --deploy/--force-deploy'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

            if not (result.build_dmg or result.download or result.force_download):
                self.parser.print_usage(sys.stderr)
                _msg = ('{}: {}: not allowed without argument -b/--build-dmg or -d/--destination '
                        'or -f/--force-destination'.format(_err_msg, _arg))
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        # Test if user is root for deploy/force deploy modes
        if not result.dry_run:
            if result.deployment:
                _arg = '--deploy'
            elif result.force_deployment:
                _arg = '--force-deploy'

            if not misc.is_root() and (result.deployment or result.force_deployment):
                _msg = '{} {}: you must be root to install packages'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        # Handle some checking for more specific circumstances.
        if (result.download or result.force_download or result.deployment or result.force_deployment):
            if result.download:
                _arg = '-d/--destination'

            if result.force_download:
                _arg = '-f/--force-destination'

            if result.deployment:
                _arg = '--deploy'

            if result.force_deployment:
                _arg = '--force-deploy'

            if not (result.mandatory or result.optional):
                _msg = '{} {}: must provide at least -m/--mandatory or -o/--optional or both'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        if result.cache_server:
            _arg = '--cache-server'
            _cs = result.cache_server[0]
            _url = urlparse(_cs)

            if _url.scheme not in self._valid_url_schemes or not re.search(r'(?::\d+)', _url.netloc):  # and _url.path is not None:
                _msg = '{} {}: cache server url format expected is https://example.org:1234'.format(_err_msg, _arg)
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        if result.pkg_server:
            _arg = '--pkg-server'
            _ps = result.pkg_server[0]
            _url = urlparse(_ps)

            if _url.scheme not in self._valid_url_schemes or not _url.path:
                _msg = ('{} {}: mirror server url format expected is https://example.org/<path> '
                        'or https://example.org/file.dmg'.format(_err_msg, _arg))
                print(_msg)
                LOG.info(_msg)
                sys.exit(1)

        if result.show_plists:
            supported.show_supported_plists()

        if result.compare:
            compare.differences(file_a=result.compare[0], file_b=result.compare[1])

        # Set "globals" here rather than in '__main__.py'
        if not result.plists:
            config.APPS_TO_PROCESS = result.apps if result.apps else misc.find_installed_apps()

        if not result.apps:
            config.PLISTS_TO_PROCESS = result.plists

        config.ALLOW_INSECURE_CURL = result.insecure
        config.ALLOW_UNSECURE_PKGS = result.unsecure
        config.APFS_DMG = result.apfs_dmg
        config.CACHING_SERVER = result.cache_server[0].rstrip('/') if result.cache_server else None
        config.DEBUG = getattr(logging, result.log_level, None)
        config.DEPLOY_PKGS = result.deployment
        config.FORCED_DEPLOYMENT = result.force_deployment
        config.DMG_FILE = result.build_dmg[0] if result.build_dmg else None
        config.DRY_RUN = result.dry_run
        config.LOCAL_HTTP_SERVER = result.pkg_server[0].rstrip('/') if result.pkg_server else None
        config.MANDATORY = result.mandatory
        config.OPTIONAL = result.optional
        config.QUIET = result.quiet
        config.SILENT = result.silent
        config.TARGET = result.install_target[0] if result.install_target else '/'

        # Handle result.download/result.force_download
        if result.download or result.force_download:
            if result.download:
                config.DESTINATION_PATH = result.download[0]
            elif result.force_download:
                config.FORCE_DOWNLOAD = True
                config.DESTINATION_PATH = result.force_download[0]
            else:
                config.DESTINATION_PATH = config.DEFAULT_DEST

        if config.DEPLOY_PKGS or config.FORCED_DEPLOYMENT:
            config.DESTINATION_PATH = config.DEFAULT_DEST

        # Handle HTTP based DMG
        if config.LOCAL_HTTP_SERVER:
            if config.LOCAL_HTTP_SERVER.endswith('.dmg'):
                config.HTTP_DMG = True
                config.HTTP_DMG_PATH = result.pkg_server[0]
                config.LOCAL_HTTP_SERVER = None

        # Handle building a DMG
        if result.build_dmg:
            _dmg_path = os.path.splitext(config.DMG_FILE)[0]
            config.DESTINATION_PATH = '{}.sparseimage'.format(_dmg_path)

            # Set a psuedo 'config.DMG_VOLUME_MOUNTPATH' for dry-run use.
            if config.DRY_RUN:
                config.DMG_VOLUME_MOUNTPATH = '/Volumes/appleloops'

        return result
    # pylint: enable=too-many-statements
    # pylint: enable=too-many-branches
# pylint: enable=too-many-locals
