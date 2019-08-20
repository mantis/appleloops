"""Used to determine which optional packages belong to which 'pack' per release."""


class OptionPack(object):
    """Attributes for the 'collection packs' of packages in an Application."""
    def __init__(self, source, release):
        self._source = source
        self._release = release

        self._content = self._source.get('Content', None)
        self._packages = self._source.get('Packages', None)

        self._optional_packages = set()

        # Only need packages that are truly optional.
        # Mandatory packages in these option packs _must_ be installed
        # anyway.
        for _pkg in self._packages:
            if not self._packages[_pkg].get('IsMandatory', False):
                self._optional_packages.add(_pkg)

        # Public attr.
        self.option_packs = self._process_packs()

        # In Logic Pro X & MainStage source files, the 'Content' key is a dict.
        # In the 'Content' dict, there's typically 'localised' versions, so pull
        # the 'en' one.
        if any(self._release.startswith(x) for x in ['logicpro', 'mainstage']):
            self._content = self._content.get('en')

    def _process_packs(self):
        """Processes the option packs."""
        result = list()

        if self._content:
            _rp = None

            for _opt_pack in self._content:
                _description = None
                _locale = None

                _name = _opt_pack.get('Name', None)  # Option Pack 'name'.
                _packages = _opt_pack.get('Packages', None)  # Pkgs in the opt. pack.
                _sub_content = _opt_pack.get('SubContent', None)  # Some are broken up into sub opt. packs.

                if _sub_content:
                    _pack = dict()

                    for _sp in _sub_content:
                        _sp_desc = None
                        _sp_name = _sp.get('Name', None)
                        _sp_pkgs = _sp.get('Packages', None)
                        _sp_locl = _sp.get('_LOCALIZABLE_', None)
                        _packages = set()

                        if _sp_pkgs:
                            _packages = {_pkg for _pkg in _sp_pkgs if _pkg in self._optional_packages}

                        if _sp_locl:
                            for _i in _sp_locl:
                                for _k, _v in _i.items():
                                    if _k == 'Description':
                                        _sp_desc = _v.strip()
                                        break

                        if len(_packages) != 0:
                            _pack['Name'] = _sp_name
                            _pack['Description'] = _sp_desc
                            _pack['Packages'] = _packages

                            _rp = Pack(**_pack)

                    if _rp:
                        result.append(_rp)
                elif not _sub_content and _packages:
                    _pack = dict()
                    _locale = _opt_pack.get('_LOCALIZABLE_', None)

                    if _packages:
                        _pkgs = {_pkg for _pkg in _packages if _pkg in self._optional_packages}

                    if _locale:
                        for _item in _locale:
                            for _k, _v in _item.items():
                                if _k == 'Description':
                                    _description = _v.strip()
                                    break

                    if len(_pkgs) != 0:
                        _pack['Description'] = _description
                        _pack['Name'] = _name
                        _pack['Packages'] = _pkgs

                        _rp = Pack(**_pack)

                    if _rp:
                        result.append(_rp)

        return result


class Pack(object):
    """Attributes for a specific option pack."""
    def __init__(self, **kwargs):
        _valid_kwargs = {'Name': None,
                         'Description': None,
                         'Packages': None}

        for kwarg, value in _valid_kwargs.items():
            if kwarg in kwargs.keys():
                setattr(self, kwarg, kwargs.get(kwarg, None))
            else:
                setattr(self, kwarg, value)

    def __hash__(self):
        """Hash a tuple (immutable) containing the pack 'Name' attribute."""
        if isinstance(self, Pack):
            return hash(('Name', self.Name))
        else:
            return NotImplemented

    def __eq__(self, other):
        """Used for testing equality of a pack instance based on the 'Name' attribute."""
        if isinstance(self, Pack):
            return self.Name == other.Name
        else:
            return NotImplemented

    def __ne__(self, other):
        """Used for testing 'not' equality of a pack instance based on the 'Name' attribute.
        Implemented for Python 2.7 compatability."""
        if isinstance(self, Pack):
            return not self.Name == other.Name
        else:
            return NotImplemented
