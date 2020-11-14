"""Contains a basic dictionary for the supported releases of
Apple's audio applications, and relevant 'feed' files."""
import logging

LOG = logging.getLogger(__name__)


SUPPORTED = {
    'garageband1011': 'garageband1011.plist',
    'garageband1012': 'garageband1012.plist',
    'garageband1015': 'garageband1015.plist',
    'garageband1016': 'garageband1016.plist',
    'garageband1020': 'garageband1020.plist',
    'garageband1021': 'garageband1021.plist',
    'garageband1040': 'garageband1040.plist',
    'logicpro1021': 'logicpro1021.plist',
    'logicpro1022': 'logicpro1022.plist',
    'logicpro1023': 'logicpro1023.plist',
    'logicpro1030': 'logicpro1030.plist',
    'logicpro1032': 'logicpro1032.plist',
    'logicpro1040': 'logicpro1040.plist',
    'logicpro1042': 'logicpro1042.plist',
    'logicpro1050': 'logicpro1050.plist',
    'mainstage323': 'mainstage323.plist',
    'mainstage324': 'mainstage324.plist',
    'mainstage330': 'mainstage330.plist',
    'mainstage340': 'mainstage340.plist',
    'mainstage350': 'mainstage350.plist',
}

LOG.debug('Supported: {}'.format(SUPPORTED))


def show_supported_plists():
    """Prints out the supported plists for help."""
    print('Supported plist files are:')

    for _plist in sorted(SUPPORTED.values()):
        print('  {}'.format(_plist))

    exit(0)
