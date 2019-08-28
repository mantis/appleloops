"""
Downloads required audio loops for GarageBand, Logic Pro X, and MainStage 3.

------------------------------------------------------------------------------
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------

Tested on Python 2.7.10 (as shipped in macOS X) and Python 3.7.0
"""
# pylint: disable=multiple-statements
import sys; sys.dont_write_bytecode = True  # NOQA
import logging
import logging.handlers
import os
# pylint: enable=multiple-statements
from datetime import datetime
from pprint import pprint  # NOQA

# import loopslib  # NOQA
from loopslib import applications
from loopslib import arguments
from loopslib import config
from loopslib import diskusage
from loopslib import deployment
from loopslib import dmg
from loopslib import misc
from loopslib import process_source


# pylint: disable=invalid-name
def config_logging(log_level=None):
    """Configures logging for the utility."""
    log = logging.getLogger()
    log_level = log_level if log_level else config.LOG_LEVEL
    log.setLevel(getattr(logging, log_level.upper(), None))
    fh = logging.handlers.RotatingFileHandler(config.LOG_FILE_PATH, maxBytes=(1048576 * 10), backupCount=7)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fmt = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(fmt)
    log.addHandler(fh)

    if os.path.isfile(config.LOG_FILE_PATH):
        fh.doRollover()

    return logging.getLogger(__name__)
# pylint: enable=invalid-name


# pylint: disable=missing-docstring
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def main():
    # Set global value of '__name__'
    config.NAME = __name__

    # Arguments and argument parsing
    _args = arguments.LoopsArguments()
    args = _args.parse_args()

    # Logging
    config_logging(log_level=args.log_level)

    # Disk
    disk = diskusage.DiskStats()

    # Open log file
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info('------------------ Log opened on {} ------------------'.format(now))

    # Create sparse image if building DMG
    if args.build_dmg:
        sparse = dmg.BuildDMG(filename=config.DMG_FILE)
        sparse.make_sparseimage()

    # Debug log stats
    misc.debug_log_stats()

    # Continue on if there are apps/plists to process.
    apps_as_source = None
    plists_as_source = None

    # Some output indicating work is underway
    if not (config.QUIET or config.SILENT):
        print('Analysing...')

    # Mount a HTTP DMG if exists (deployment only)
    if config.HTTP_DMG:
        sparse = dmg.BuildDMG()
        sparse.mount(dmg=config.HTTP_DMG_PATH, read_only=True)  # Force read only so no delete!

    if config.APPS_TO_PROCESS:
        garageband = applications.Application('garageband') if 'garageband' in config.APPS_TO_PROCESS else None
        logicpro = applications.Application('logicpro') if 'logicpro' in config.APPS_TO_PROCESS else None
        mainstage = applications.Application('mainstage') if 'mainstage' in config.APPS_TO_PROCESS else None

        apps_as_source = [garageband, logicpro, mainstage]
    elif config.PLISTS_TO_PROCESS:
        plists_as_source = config.PLISTS_TO_PROCESS

    # Processed apps go into single instance of 'ProcessedApplications'.
    if apps_as_source:
        packages = process_source.ProcessedSource(apps=apps_as_source)
    elif plists_as_source:
        packages = process_source.ProcessedSource(plists=plists_as_source)

    if not config.SILENT:
        print('{}\n'.format(packages.stats_message))

    # Process packages
    if packages.all:
        if config.DEPLOY_PKGS or config.FORCED_DEPLOYMENT:
            if not disk.has_space(space_requested=packages.total_size_req):
                _msg = ('Insufficient space to install packages. Free up more space to continue. '
                        'Download and install size is {}.'.format(packages.total_size_req_hr))
                _dbg = ('Insufficient space. {} download total and {} install total.'.format(packages.all_download_size_hr,
                                                                                             packages.all_install_size_hr))
                logging.info(_msg)
                logging.debug(_dbg)
                print(_msg)
                sys.exit(1)

        package = deployment.LoopDeployment()

        # Do the stuff.
        _l = len(packages.all)
        for pkg in packages.all:
            _i = packages.all.index(pkg) + 1
            _i = '{i:0{width}d}'.format(width=len(str(_l)), i=_i)
            _ctr_msg = '{} of {}'.format(_i, _l)
            package.process(pkg, counter_msg=_ctr_msg)

        # Tidy up any temp items, only if this is not a download!
        if args.deployment or args.force_deployment:
            misc.tidy_up()

    # Unmount HTTP DMG
    if config.HTTP_DMG:
        sparse.eject(dmg=config.DMG_VOLUME_MOUNTPATH)

    # Convert sparse image to DMG
    if args.build_dmg:
        sparse.convert_sparseimage(sparseimage=config.DESTINATION_PATH)

    # The last thing logged.
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info('------------------ Log closed on {} ------------------'.format(now))
# pylint: enable=too-many-statements
# pylint: enable=too-many-branches
# pylint: enable=missing-docstring


if __name__ == '__main__':
    main()
