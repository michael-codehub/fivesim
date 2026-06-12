# Pie-menu button registration. Requires Sims4CommunityLibrary.
#
# Architecture note (the result of painful debugging): the interactions
# themselves are PURE EA tuning — c="ImmediateSuperInteraction" with a
# basic_extras do_command that invokes our console commands (fivesim.btn_*),
# passing the clicked Sim as an int id. No custom Python class sits in the
# pie-menu path at all; this mirrors how large shipping mods do user-facing
# Sim buttons (custom S4CL classes are only proven in cheat/debug menus).
# S4CL is used solely to ATTACH the affordance ids to Sims, which is its
# documented happy path (the docs' own example attaches EA interaction ids).
from typing import Tuple

from sims.sim import Sim

from sims4communitylib.services.interactions.interaction_registration_service import (
    CommonInteractionRegistry,
    CommonScriptObjectInteractionHandler,
)
try:
    from sims4communitylib.services.interactions.interaction_registration_service import CommonInteractionType
except ImportError:  # very old S4CL kept it in enums
    from sims4communitylib.enums.common_interaction_type import CommonInteractionType

from .modinfo import INTERACTION_PLAY_ID, INTERACTION_SETUP_ID, INTERACTION_STOP_ID


@CommonInteractionRegistry.register_interaction_handler(CommonInteractionType.ON_SCRIPT_OBJECT_LOAD)
class _FiveSimInteractionHandler(CommonScriptObjectInteractionHandler):
    @property
    def interactions_to_add(self) -> Tuple[int]:
        return (INTERACTION_PLAY_ID, INTERACTION_SETUP_ID, INTERACTION_STOP_ID)

    def should_add(self, script_object, *args, **kwargs) -> bool:
        return isinstance(script_object, Sim)
