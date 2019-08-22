#!/usr/bin/env python
"""Interrogate local property list and remote property list to determin
which packages 'IsMandatory' state differs."""
from __future__ import print_function


import plistlib

local = ''
remote = ''


_local_root = plistlib.readPlist(local)
_remote_root = plistlib.readPlist(remote)


_local_pkgs = _local_root.get('Packages', None)
_remote_pkgs = _remote_root.get('Packages', None)


local_packages = set()
remote_packages = set()

local_not_in_remote = set()
remote_not_in_local = set()


for _pkg in _local_pkgs:
    _mandatory = _local_pkgs[_pkg].get('IsMandatory', False)

    if _mandatory:
        _name = '{} - Mandatory'.format(_pkg)
        local_packages.add(_name)

for _pkg in _remote_pkgs:
    _mandatory = _remote_pkgs[_pkg].get('IsMandatory', False)

    if _mandatory:
        _name = '{} - Mandatory'.format(_pkg)
        remote_packages.add(_name)


for _info in local_packages:
    if _info not in remote_packages:
        local_not_in_remote.add(_info)

for _info in remote_packages:
    if _info not in local_packages:
        remote_not_in_local.add(_info)

if local_not_in_remote:
    print('Local Mandatory that is not in Remote Mandatory ({})'.format(len(list(local_not_in_remote))))
    for _p in local_not_in_remote:
        print(_p)

if local_not_in_remote and remote_not_in_local:
    print('\n')

if remote_not_in_local:
    print('Remote Mandatory that is not in Local Mandatory ({})'.format(len(list(remote_not_in_local))))
    for _p in remote_not_in_local:
        print(_p)
