"""Contains all the core configuration variables.
These must not be modified or behaviour could break."""
import logging

from distutils.version import StrictVersion
from os import path

# pylint: disable=relative-import
try:
    import misc
    import supported
    import version
except ImportError:
    from . import misc
    from . import supported
    from . import version
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)

# Ignore invalid certs when downloading packages
ALLOW_INSECURE_CURL = False

# Ignore invalid certs when installing packages
ALLOW_UNSECURE_PKGS = False

# Just part of the app bundle path.
# Do not override.
APPLICATIONS_PATH = '/Applications'

# Just part of the app bundle path.
# Do not override.
APPS = {'garageband': 'GarageBand.app',
        'logicpro': 'Logic Pro X.app',
        'mainstage': 'MainStage 3.app'}

# Apps to process, passed in from args
APPS_TO_PROCESS = None

# This needs to be unblocked/whitelisted by your firewall/proxy.
AUDIOCONTENT_URL = 'https://audiocontentdownload.apple.com'

# This needs to be unblocked/whitelisted by your firewall/proxy.
AUDIOCONTENT_FAILOVER_URL = 'https://raw.githubusercontent.com/carlashley/appleloops/master'

# "Bundle ID"
BUNDLE_ID = 'com.github.carlashley.appleloops'

# When set via command line, should be in the form of 'https://example.org:12345'
CACHING_SERVER = None

# Just part of the app bundle path.
# Do not override.
CONTENTS_PATH = 'Contents'

# CURL args/opts
CURL_HTTP1 = True
CURL_HTTP_ARG = '--http1.1'
CURL_RETRIES = '5'

# Debug on/off
DEBUG = False

# Deployment of packages
DEPLOY_PKGS = False
FORCED_DEPLOYMENT = False

# Destination path (a default value is provided)
# NOTE: '/tmp' is used because in some circumstances, the
# destination needs to be human friendly, and the
# python 'tempfile' packageg uses the unfriendly `/var/db`
# based temp folders.
DEFAULT_DEST = '/tmp/appleloops'
DESTINATION_PATH = None
FORCE_DOWNLOAD = False

# DMG File stuff
APFS_DMG = False
DMG_DEPLOY_FILE = None
DMG_FILE = None
DMG_DISK_DEV = None  # Required because APFS is a bit funky when ejecting.
DMG_VOLUME_MOUNTPATH = None
DMG_VOLUME_NAME = 'appleloops'  # Consistent name to target
HTTP_DMG = None
HTTP_DMG_PATH = None
DRY_RUN_VOLUME_MOUNTPATH = '/Volumes/{}'.format(DMG_VOLUME_NAME)

# Dry Run
DRY_RUN = False

# HTTP Status's that are OK
HTTP_OK_STATUS = [200, 301, 302, 303, 307, 308]

# When set via command line, should be in the form of 'https://example.org/path/appleloops'
# Best practice is to use the relevant argument to mirror the folder paths from Apple.
LOCAL_HTTP_SERVER = None

# Log level
LOGGER_NAME = 'appleloops'
LOG_FILE = 'appleloops.log'
LOG_LEVEL = 'INFO'

# If the user is root, change the log path so not to blat on user log folder.
if misc.is_root():
    LOG_PATH = '/var/log'
else:
    LOG_PATH = path.expanduser(path.expandvars('~/Library/Logs'))

LOG_FILE_PATH = path.join(LOG_PATH, LOG_FILE)

# Default 'path' is '2016'. Use '.replace()' when '2013' is required.
LP10_MS3_CONTENT = 'lp10_ms3_content_2016'

# Used to determine if processing mandatory packages
MANDATORY = False

# Used for overall name of app based on '__name__'
NAME = None

# Used to determine if processing optional packages
OPTIONAL = False

# Property Lists to use for processing if provided.
PLISTS_TO_PROCESS = None

# Print help message
PRINT_HELP = False

# If you use a proxy. CURL will expect whatever format it requires.
PROXY = None

# Minimal output.
QUIET = False

# Checks for the 'Content-Length' header for each package.
# This adds time and doesn't achieve much. Leave this as 'False'.
REAL_DOWNLOAD_SIZE = False

# Just part of the app bundle path.
# Do not override.
RESOURCES_PATH = path.join(CONTENTS_PATH, 'Resources')

# No output.
SILENT = False

# Sleep for five seconds between installs.
INST_SLEEP = None

# All supported plists
SUPPORTED_PLISTS = supported.SUPPORTED.copy()

# Capture OS Version
OS_VER = StrictVersion(version.os_vers())
OS_BUILD = version.os_vers(arg='buildVersion')

# Post Catalina, the disk containers and volumes change a bit
CATALINA = OS_VER > StrictVersion('10.14.9')

# Target (this is for the 'installer' command.)
# Using a different target for Catalina doesn't appear necessary.
TARGET = '/'

# User Agent string to use for all requests to Apple.
USERAGENT = 'appleloops/{}'.format(version.VERSION)

# Latest package 'feed' files.
GB_LATEST_PLIST = ['{}/{}/{}'.format(AUDIOCONTENT_URL, LP10_MS3_CONTENT, x)
                   for x in sorted(supported.SUPPORTED.values(), reverse=True)
                   if x.startswith('garageband')][0]
LP_LATEST_PLIST = ['{}/{}/{}'.format(AUDIOCONTENT_URL, LP10_MS3_CONTENT, x)
                   for x in sorted(supported.SUPPORTED.values(), reverse=True)
                   if x.startswith('logicpro')][0]
MS_LATEST_PLIST = ['{}/{}/{}'.format(AUDIOCONTENT_URL, LP10_MS3_CONTENT, x)
                   for x in sorted(supported.SUPPORTED.values(), reverse=True)
                   if x.startswith('mainstage')][0]

ALL_LATEST_PLISTS = [path.basename(GB_LATEST_PLIST).replace('.plist', ''),
                     path.basename(LP_LATEST_PLIST).replace('.plist', ''),
                     path.basename(MS_LATEST_PLIST).replace('.plist', '')]

ALL_LATEST_APPS = [_key for _key, _val in APPS.items()]
