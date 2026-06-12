# Mod identity for Sims4CommunityLibrary (only imported when S4CL is present).
from sims4communitylib.mod_support.common_mod_info import CommonModIdentity


class ModInfo(CommonModIdentity):
    _FILE_PATH = str(__file__)
    _IDENTITY = None

    @classmethod
    def get_identity(cls):
        if cls._IDENTITY is None:
            cls._IDENTITY = ModInfo()
        return cls._IDENTITY

    @property
    def _name(self):
        return '5imulites'

    @property
    def _author(self):
        return 'mariwatts'

    @property
    def _base_namespace(self):
        return 'fivesim'

    @property
    def _file_path(self):
        return ModInfo._FILE_PATH

    @property
    def _version(self):
        return '1.0.0'
