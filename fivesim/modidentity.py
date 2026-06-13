# Mod identity for Sims4CommunityLibrary (only used by the optional setup dialog).
# v3.x CommonModIdentity takes 5 positional args (name, author, base_namespace,
# file_path, version); older S4CL used property overrides. Handle both.
from sims4communitylib.mod_support.common_mod_info import CommonModIdentity

_NAME = '5imulites'
_AUTHOR = 'akrosmoke'
_NAMESPACE = 'fivesim'
_VERSION = '1.0.0'


class _LegacyIdentity(CommonModIdentity):
    @property
    def _name(self):
        return _NAME

    @property
    def _author(self):
        return _AUTHOR

    @property
    def _base_namespace(self):
        return _NAMESPACE

    @property
    def _file_path(self):
        return str(__file__)

    @property
    def _version(self):
        return _VERSION


class ModInfo:
    _IDENTITY = None

    @classmethod
    def get_identity(cls):
        if cls._IDENTITY is None:
            try:
                # current S4CL (v3.x): construct directly with the 5 fields
                cls._IDENTITY = CommonModIdentity(_NAME, _AUTHOR, _NAMESPACE, str(__file__), _VERSION)
            except Exception:
                # older S4CL: abstract property subclass with a no-arg __init__
                cls._IDENTITY = _LegacyIdentity()
        return cls._IDENTITY
