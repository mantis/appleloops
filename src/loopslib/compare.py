"""Contains the function for comparing two property lists."""
import logging
import os
import sys
import tempfile

try:
    import config
    import curl_requests
    import misc
    import plist
except ImportError:
    from . import config
    from . import curl_requests
    from . import misc
    from . import plist

LOG = logging.getLogger(__name__)


def differences(file_a, file_b, detailed_info=False):
    """Compares the package details in 'file_a' against 'file_b' to determine
    what files exist in 'file_b' but not in 'file_a'. This will also display
    packages _removed_.
    This function sorts the files into smallest to largest order. So if
    'garageband1021.plist' is compared to 'garageband1011.plist', the
    output will be based on packages that are in 'garageband1021.plist' but
    not in 'garageband1011.plist'. In otherwords, '1021' is the _right_
    file, '1011' is the _left_ file."""
    sorted_files = sorted([f for f in [file_a, file_b]])
    file_a = sorted_files[0]
    base_a = os.path.basename(file_a)
    file_b = sorted_files[1]
    base_b = os.path.basename(file_b)

    _supported = config.SUPPORTED_PLISTS.values()
    _supported.sort()

    if not all(_file.endswith('.plist') for _file in [file_a, file_b]):
        print('Files must both be property list files.')
        sys.exit(1)

    if not all(_file in _supported for _file in [base_a, base_b]):
        print('Files must be from {}'.format(_supported))
        sys.exit(1)

    # Sort the two files so if the order of 'file_a' 'file_b' is
    # 'garageband1021.plist' 'garageband1011.plist' it becomes
    # 'garageband1011.plist' 'garageband1021.plist'
    _tmp_dir = os.path.join(tempfile.gettempdir(), config.BUNDLE_ID)

    if not os.path.exists(file_a):
        _fa_fallback = os.path.join(config.AUDIOCONTENT_FAILOVER_URL, 'lp10_ms3_content_2016', base_a)
        _fa_url = misc.plist_url_path(base_a)
        file_a = os.path.join(_tmp_dir, base_a)

        _req = curl_requests.CURL(url=_fa_url)

        if _req.status in config.HTTP_OK_STATUS:
            _req.get(url=_fa_url, output=file_a)
        else:
            _req.get(url=_fa_fallback, output=file_a)

        file_a_plist = plist.readPlist(plist_path=file_a)['Packages']
        misc.clean_up(file_a)
    elif os.path.exists(file_a):
        file_a_plist = plist.readPlist(plist_path=file_a)['Packages']

    if not os.path.exists(file_b):
        _fb_fallback = os.path.join(config.AUDIOCONTENT_FAILOVER_URL, 'lp10_ms3_content_2016', base_b)
        _fb_url = misc.plist_url_path(base_b)
        file_b = os.path.join(_tmp_dir, base_b)

        _req = curl_requests.CURL(url=_fb_url)

        if _req.status in config.HTTP_OK_STATUS:
            _req.get(url=_fb_url, output=file_b)
        else:
            _req.get(url=_fb_fallback, output=file_b)

        file_b_plist = plist.readPlist(plist_path=file_b)['Packages']
        misc.clean_up(file_b)
    elif os.path.exists(file_b):
        file_a_plist = plist.readPlist(plist_path=file_a)['Packages']

    # Build a set of package names.
    file_a_packages = set([os.path.basename(file_a_plist[_pkg]['DownloadName'])
                           for _pkg in file_a_plist])
    file_b_packages = set([os.path.basename(file_b_plist[_pkg]['DownloadName'])
                           for _pkg in file_b_plist])

    # Get the new/removed files by using 'set_b.difference(set_a)'
    new_files = file_b_packages.difference(file_a_packages)
    rem_files = file_a_packages.difference(file_b_packages)
    cmn_files = file_b_packages.intersection(file_a_packages)

    if not detailed_info:
        if new_files:
            print('{} new packages in {} when compared to {}'.format(len(new_files),
                                                                     base_b, base_a))

        if rem_files:
            print('{} packages removed from {} compared to {}'.format(len(rem_files),
                                                                      base_a, base_b))

        if cmn_files:
            print('{} packages common between {} and {}'.format(len(cmn_files),
                                                                base_a, base_b))

    # Exit success because nothing else to do.
    sys.exit(0)
