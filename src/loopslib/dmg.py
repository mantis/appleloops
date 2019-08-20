"""Contains class relating to building DMG files."""
import logging
import subprocess
import sys

from os import path, remove

# pylint: disable=relative-import
try:
    import config
    import plist
except ImportError:
    from . import config
    from . import plist
# pylint: enable=relative-import

LOG = logging.getLogger(__name__)

# pylint: disable=too-many-nested-blocks


class BuildDMG(object):
    """Class for handling DMG files."""
    def __init__(self, filename=None):
        self._hdiutil = '/usr/bin/hdiutil'
        self._valid_fs = ['HFS+J' 'HFS+', 'APFS']
        self._volume_kind = {'HFS+': 'hfs',
                             'HFS+J': 'hfs',
                             'APFS': 'apfs'}

        self.filename = filename
        self.sparse_image = '{}.sparseimage'.format(path.splitext(filename)[0]) if filename else None
        self.volume_name = config.DMG_VOLUME_NAME

        if config.APFS_DMG:
            self.filesystem = 'APFS'
        else:
            self.filesystem = 'HFS+'

        LOG.debug('DMG file system set to: {}'.format(self.filesystem))

    def _eject(self, sparseimage, action):
        """Unmounts the specified DMG to the local filesystem."""
        if action in ['detach', 'eject']:
            cmd = [self._hdiutil,
                   action,
                   '-quiet',
                   sparseimage]

            # Have to umount DMG if '--pkg-server' is a DMG
            if not config.DRY_RUN:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p_result, p_error = process.communicate()

                if process.returncode == 0:
                    LOG.info('Unmounted {}'.format(sparseimage))
                    LOG.debug(p_result)
                else:
                    LOG.debug('{}: {} - {}'.format(' '.join(cmd), process.returncode, p_error))

                    print(p_error)
                    sys.exit(process.returncode)

                # Log success/fail with short message.
                LOG.debug('{}: {}'.format(' '.join(cmd), process.returncode))
        else:
            raise Exception('Unexpected \'hdiutil\' action: {}'.format(action))

    # pylint: disable=no-self-use
    def _get_devicepath(self, output):
        """Gets the '/dev/disk' device path from the output of the 'hdiutil' command."""
        # Use the PLIST output to set 'config.DMG_VOLUME_MOUNTPATH'
        result = None

        # This method is used to read buffer input and dict input.
        if isinstance(output, dict):
            _result = output['system-entities']
        else:
            _result = plist.readPlistFromString(output)['system-entities']

        for item in _result:
            _ch = item.get('content-hint', None)

            # This is required for APFS because it seems to not properly eject
            # the volume, so an eject on the device is required.
            # if self.filesystem == 'APFS' and _ch == 'GUID_partition_scheme':
            if _ch == 'GUID_partition_scheme':
                # config.DMG_DISK_DEV = item.get('dev-entry', None)
                result = item.get('dev-entry', None)
                break

        return result
    # pylint: enable=no-self-use

    def _sparse_exists(self):
        """Gets information about any potential attached sparse images to avoid
        volume and image entangling."""
        result = None

        cmd = [self._hdiutil, 'info', '-plist']

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_result, p_error = process.communicate()

        if process.returncode == 0:
            _result = plist.readPlistFromString(p_result).get('images', None)

            if _result:
                for image in _result:
                    _image_path = image.get('image-path', None)
                    _image_type = image.get('image-type', None)
                    _sys_entity = image.get('system-entities')

                    if _image_path and _image_type:
                        if _image_path == self.sparse_image:
                            if _image_type == 'sparse disk image' and _sys_entity:
                                _de = self._get_devicepath(output=image)
                                _mp = self._get_mountpath(output=image)

                                result = dict()
                                result['mount-point'] = _mp
                                result['dev-entry'] = _de
                                break
        else:
            LOG.debug('{}: {} - {}'.format(' '.join(cmd), process.returncode, p_error))

            print(p_error)
            sys.exit(process.returncode)

        # Log success/fail with short message.
        LOG.debug('{}: {}'.format(' '.join(cmd), process.returncode))

        return result

    def _get_mountpath(self, output):
        """Gets the mount path of a sparseimage/dmg file from the output of the 'hdiutil' command."""
        # Use the PLIST output to set 'config.DMG_VOLUME_MOUNTPATH'
        result = None

        # This method is used to read buffer input and dict input.
        if isinstance(output, dict):
            _result = output['system-entities']

            for item in _result:
                result = item.get('mount-point', None)

                if result:
                    break
        else:
            _result = plist.readPlistFromString(output)['system-entities']

            for item in _result:
                _vk = item.get('volume-kind', None)

                if _vk and _vk == self._volume_kind[self.filesystem]:
                    result = item.get('mount-point', None)
                    break

        return result

    def convert_sparseimage(self, sparseimage):
        """Converts the temporary DMG into the final DMG file."""
        # Unmount sparseimage first.
        self.eject(dmg=config.DMG_VOLUME_MOUNTPATH)

        cmd = [self._hdiutil,
               'convert',
               '-ov',
               '-quiet',
               sparseimage,
               '-format',
               'UDZO',
               '-o',
               self.filename]

        if not config.DRY_RUN:
            LOG.info('Converting {}'.format(sparseimage))

            if not (config.QUIET or config.SILENT):
                print('Converting {}'.format(sparseimage))

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p_result, p_error = process.communicate()

            if process.returncode == 0:
                LOG.info('Created {}'.format(self.filename))
                LOG.debug(p_result)

                if not (config.QUIET or config.SILENT):
                    print('Created {}'.format(self.filename))

                # Clean up in Aisle DMG
                try:
                    remove(sparseimage)

                    LOG.info('Cleaned up {}'.format(sparseimage))
                except OSError:
                    pass
            else:
                LOG.debug('{}: {} - {}'.format(' '.join(cmd), process.returncode, p_error))

                print(p_error)
                sys.exit(process.returncode)

            # Log success/fail with short message.
            LOG.debug('{}: {}'.format(' '.join(cmd), process.returncode))

    def eject(self, dmg):
        """Detaches and ejects an DMG/Sparse Image"""
        # For some reason, APFS requires the _device_ to be detached, not the Volume name.
        if self.filesystem == 'APFS':
            self._eject(sparseimage=config.DMG_DISK_DEV, action='detach')
        else:
            self._eject(sparseimage=dmg, action='detach')

    def make_sparseimage(self):
        """Creates a thin 'sparseimage' for temporary file storage when making a DMG."""
        # Do not specify a filesize here, otherwise the image will not thin provision space.
        cmd = [self._hdiutil,
               'create',
               '-ov',
               '-plist',
               '-volname',
               self.volume_name,
               '-fs',
               self.filesystem,
               '-attach',
               '-type',
               'SPARSE',
               self.sparse_image]

        if not config.DRY_RUN:
            _sparse_exists = self._sparse_exists()

            if _sparse_exists:
                config.DMG_VOLUME_MOUNTPATH = _sparse_exists['mount-point']
                config.DMG_DISK_DEV = _sparse_exists['dev-entry']
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p_result, p_error = process.communicate()

                if process.returncode == 0:
                    LOG.info('Created temporary sparseimage {}'.format(self.sparse_image))

                    if not (config.QUIET or config.SILENT):
                        print('Created temporary sparseimage')

                    config.DMG_VOLUME_MOUNTPATH = self._get_mountpath(output=p_result)
                    config.DMG_DISK_DEV = self._get_devicepath(output=p_result)
                else:
                    LOG.debug('{}: {} - {}'.format(' '.join(cmd), process.returncode, p_error))

                    print(p_error)
                    sys.exit(process.returncode)

                # Log success/fail with short message.
                LOG.debug('{}: {}'.format(' '.join(cmd), process.returncode))

    def mount(self, dmg, read_only=False):
        """Mounts the specified 'dmg' file."""
        cmd = [self._hdiutil,
               'attach',
               '-plist',
               dmg]

        if read_only and isinstance(read_only, bool):
            cmd.insert(2, '-readonly')

        # Have to mount DMG if '--pkg-server' is a DMG
        if not config.DRY_RUN:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p_result, p_error = process.communicate()

            if process.returncode == 0:
                LOG.info('Mounted {}'.format(dmg))

                if not (config.QUIET or config.SILENT):
                    print('Mounted {}'.format(dmg))

                config.DMG_VOLUME_MOUNTPATH = self._get_mountpath(output=p_result)
                config.DMG_DISK_DEV = self._get_devicepath(output=p_result)
            else:
                LOG.debug('{}: {} - {}'.format(' '.join(cmd), process.returncode, p_error))

                print(p_error)
                sys.exit(process.returncode)

            # Log success/fail with short message.
            LOG.debug('{}: {}'.format(' '.join(cmd), process.returncode))

        if config.DRY_RUN and config.HTTP_DMG:
            config.DMG_VOLUME_MOUNTPATH = config.DRY_RUN_VOLUME_MOUNTPATH
# pylint: enable=too-many-nested-blocks
