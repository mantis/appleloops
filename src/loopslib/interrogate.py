"""Class for interrogating a local property list file for comparison to a
remote property list file."""
import logging
import os

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


class Interrogator(object):
    """Class for interrogating a specific installed application to debug issues
    with deployments."""
    def __init__(self, app):
        return NotImplemented
