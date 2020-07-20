"""Handle specific package scenarios that are problematic."""


# This is just a dictionary that contains the instructions necessary
# for handling these 'bad wolf' package scenarios.
# These should in theory only be required if falling back to Apple's
# audiocontentdownload mirrors of the relevant files.

# To use:
#   - The 'root' key for each app must match the same filename as the
#   property list feed file of each app version to override.
#   For example: 'garageband1021.plist' will make changes for any
#   package in any GarageBand release that uses 'garageband1021.plist'
#   as its source file.

#   - The next key is for the actual package name, which must match
#   the package name found for each package in the plist['Packages']
#   dictionary of the source file.

#   - The next key can be used to override any values in the Apple
#   source file as long as that key already exists. Any key that
#   does not exist will be added to the source dictionary.

# See the first entry as a commented example.


BAD_WOLF_PKGS = {
    'garageband1021.plist': {  # This is the source file to apply changes to
        # This is the package name that matches to 'garageband1021.plist['Packages'][<pkg_name>]'
        'MAContent10_AssetPack_0357_EXS_BassAcousticUprightJazz': {
            # This key exists, so this value updates existing value.
            'IsMandatory': True,
            # This is a new key, so gets added. Used to track related GitHub issue.
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0358_EXS_BassElectricFingerStyle': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0482_EXS_OrchWoodwindAltoSax': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0484_EXS_OrchWoodwindClarinetSolo': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0487_EXS_OrchWoodwindFluteSolo': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0491_EXS_OrchBrass': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'MAContent10_AssetPack_0509_EXS_StringsEnsemble': {
            'IsMandatory': True,
            'Comment': 'ghIssue:45'
        },
        'JamPack1InstrumentsPackage': {
            'BadWolfIgnore': True,  # This key is used to disable processing of a package
            'Comment': 'ghIssue:29'
        },
        'JamPackSymphonyOrchestraInstrumentsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPack1AppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackRemixToolsAppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackRhythmSectionAppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackSymphonyOrchestraAppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackVoicesAppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackWorldMusicAppleLoopsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'GarageBand11ExtraContentPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'IRsSurroundPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'Logic9LegacyContentPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackRemixToolsInstrumentsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackRhythmSectionInstrumentsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackVoicesInstrumentsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
        'JamPackWorldMusicInstrumentsPackage': {
            'BadWolfIgnore': True,
            'Comment': 'ghIssue:29'
        },
    },
    'logicpro1050.plist': {  # This is the source file to apply changes to
        # This is the package name that matches to 'garageband1021.plist['Packages'][<pkg_name>]'
        'MAContent10_AssetPack_0357_EXS_BassAcousticUprightJazz': {
            # This key exists, so this value updates existing value.
            'FileCheck': '/Library/Application Support/Logic/Logic Pro X Demosongs/ocean eyes.logicx/Alternatives/001/DisplayState.plist',
            # This is a new key, so gets added. Used to track related GitHub issue.
            'Comment': 'appleloops/3.1.7/ghIssue:22'
        },
        'MAContent10_AssetPack_0755_AppleLoopsPrismatica': {
            # This key exists, so this value updates existing value.
            'DownloadName': 'MAContent10_AssetPack_0801_AppleLoopsPrismaticaB.pkg',
            'PackageID': 'MAContent10_AssetPack_0801_AppleLoopsPrismaticaB',
            # This is a new key, so gets added. Used to track related GitHub issue.
            'Comment': 'appleloops/3.1.8/ghIssue:21'
        },
    }
}
