"""Miscellaneous functions."""
import logging
import os
import shutil
import subprocess
import sys

from time import sleep

# pylint: disable=relative-import
try:
    import arguments
    import config
    import version
except ImportError:
    from . import arguments
    from . import config
    from . import version
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)


def bytes2hr(byte):
    """Converts the supplied file size into a human readable number, and adds a suffix."""
    result = None

    _s = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if not isinstance(byte, int):
        try:
            byte = int(byte)
        except TypeError:
            raise

    _si = 0
    while byte > 1024 and _si < 4:
        _si += 1
        byte = byte / 1024.0

    _result = '{0:.2f}'.format(byte)

    if _result.endswith('.00'):
        _result = _result.replace('.00', '')
    elif _result.endswith('0'):
        _result = _result.rstrip('0')

    result = '{} {}'.format(_result, _s[_si])

    return result


def find_installed_apps():
    """Generates a list of apps that are installed for use in the main processing."""
    result = None
    _result = set()

    for key, value in config.APPS.items():
        app_path = os.path.join(config.APPLICATIONS_PATH, value)
        if os.path.exists(app_path):
            _result.add(key)

    if _result:
        result = [x for x in _result]

    # If there are no installed apps, need to print out appropriate usage.
    if not result:
        arguments.LoopsArguments().parser.print_usage(sys.stderr)
        msg = ('{}: error: unable to find GarageBand, Logic Pro X, or MainStage,'
               ' please use the \'-a/--app\' or \'-p/--plist\' flag'.format(config.NAME))

        LOG.debug(msg)
        if not config.SILENT:
            print(msg)

        sys.exit(1)

    return result


def is_root():
    """Returns 'True' or 'False' if user is or is not root."""
    result = None

    result = os.geteuid() == 0
    LOG.debug('Is Root User: {}'.format(result))

    return result


def plist_url_path(plist):
    """Returns a constructed URL."""
    result = None

    result = '{}/{}/{}'.format(config.AUDIOCONTENT_URL,
                               config.LP10_MS3_CONTENT,
                               plist)

    return result


def clean_up(file_path):
    """Removes a file."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            LOG.debug('Removed: {}'.format(file_path))
        except OSError as _e:
            # Sometimes might need a few seconds to finish IO
            sleep(2)
            try:
                os.remove(file_path)
            except Exception as _e:
                LOG.debug('Error removing: {} - {}'.format(file_path, _e))
                pass  # Keep calm and carry on.
    else:
        pass


def tidy_up():
    """Tidy's up working directories."""
    if not config.DRY_RUN:
        # Don't need to tidy up if building a DMG because sparseimage.
        if not config.DMG_FILE and not config.DMG_VOLUME_MOUNTPATH:
            if os.path.exists(config.DESTINATION_PATH):
                try:
                    shutil.rmtree(config.DESTINATION_PATH)
                    LOG.debug('Removed: {}'.format(config.DESTINATION_PATH))
                except OSError as _e:
                    LOG.debug('Error removing: {} - {}'.format(config.DESTINATION_PATH, _e))
                    raise
            else:
                pass


def os_build():
    """Fetch OS build number."""
    result = None
    cmd = ['/usr/bin/sw_vers', '-buildVersion']

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_result, p_error = process.communicate()

    if process.returncode == 0:
        result = p_result.strip().decode('utf-8')

    return result


def debug_log_stats():
    """Drops a few configuration variables into the LOG."""
    # This is the very first point anything is logged.
    LOG.debug('Arguments: {}'.format(sys.argv))

    LOG.debug('Python {} on macOS {} ({})'.format(version.PYTHON_VER, config.OS_VER, os_build()))
    LOG.debug('{}'.format(version.VERSION_STR))

    if config.APPS_TO_PROCESS:
        LOG.debug('Processing apps: {}'.format(', '.join(config.APPS_TO_PROCESS)))

    if config.PLISTS_TO_PROCESS:
        LOG.debug('Processing property lists: {}'.format(', '.join(config.PLISTS_TO_PROCESS)))

    LOG.debug('Processing package sets: Mandatory: {}, Optional: {}'.format(config.MANDATORY,
                                                                            config.OPTIONAL))
    LOG.debug('Log File: {}'.format(config.LOG_FILE_PATH))
    LOG.debug('Dry Run: {}'.format(config.DRY_RUN))
    LOG.debug('Caching Server: {}'.format(config.CACHING_SERVER))
    LOG.debug('Local HTTP Server: {}'.format(config.LOCAL_HTTP_SERVER))
    LOG.debug('Destination: {}, Default Destination: {}'.format(config.DESTINATION_PATH,
                                                                config.DEFAULT_DEST))
    LOG.debug('Noise level: Quiet: {}, Silent: {}'.format(config.QUIET, config.SILENT))
    LOG.debug('GarageBand Latest Plist: {}'.format(config.GB_LATEST_PLIST))
    LOG.debug('Logic Pro X Latest Plist: {}'.format(config.LP_LATEST_PLIST))
    LOG.debug('MainStage Latest Plist: {}'.format(config.MS_LATEST_PLIST))

    if config.DEPLOY_PKGS:
        LOG.debug('Deployment mode: {}'.format(config.DEPLOY_PKGS))
        LOG.debug('Forced Deployment mode: {}'.format(config.FORCED_DEPLOYMENT))
        LOG.debug('Installation target: \'{}\''.format(config.TARGET))
