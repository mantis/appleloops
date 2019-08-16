"""Initialises package with imports."""
# pylint: disable=multiple-statements
import sys; sys.dont_write_bytecode = True  # NOQA
import logging
# pylint: enable=multiple-statements

from . import applications
from . import arguments
from . import compare
from . import config
from . import curl_requests
from . import deployment
from . import diskusage
from . import dmg
from . import misc
from . import package
from . import plist
from . import supported
from . import version

logging.getLogger(__name__).addHandler(logging.NullHandler())
