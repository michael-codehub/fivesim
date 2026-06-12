# Real pie-menu interactions (the in-game button). Requires Sims4CommunityLibrary
# AND the 5imulites_interactions.package (the interaction tuning). This module is
# imported at boot ONLY if S4CL is present (see main_loop); if S4CL is missing it
# fails to import and the console commands remain the fallback.
from typing import Any, Tuple

from sims.sim import Sim
from interactions.context import InteractionContext

from sims4communitylib.classes.interactions.common_immediate_super_interaction import CommonImmediateSuperInteraction
from sims4communitylib.classes.testing.common_test_result import CommonTestResult
from sims4communitylib.classes.testing.common_execution_result import CommonExecutionResult
from sims4communitylib.services.interactions.interaction_registration_service import (
    CommonInteractionRegistry,
    CommonScriptObjectInteractionHandler,
)
from sims4communitylib.enums.common_interaction_type import CommonInteractionType

from .modidentity import ModInfo
from .modinfo import (
    INTERACTION_PLAY_ID, INTERACTION_SETUP_ID, INTERACTION_STOP_ID, HOST, PORT,
)
from . import host_client
from . import ui

AGENTS = ['gpt', 'claude', 'gemini', 'deepseek', 'qwen']
BRIDGE_URL = 'http://%s:%d' % (HOST, PORT)


def _sim_id(interaction_sim, interaction_target):
    for obj in (interaction_target, interaction_sim):
        sid = getattr(obj, 'sim_id', None)
        if sid:
            return sid
    return None


class _Base(CommonImmediateSuperInteraction):
    @classmethod
    def get_mod_identity(cls):
        return ModInfo.get_identity()

    @classmethod
    def on_test(cls, interaction_sim: Sim, interaction_target: Any,
                interaction_context: InteractionContext, **kwargs) -> CommonTestResult:
        return CommonTestResult.TRUE


class FiveSimPlay(_Base):
    def on_started(self, interaction_sim: Sim, interaction_target: Any) -> CommonExecutionResult:
        sid = _sim_id(interaction_sim, interaction_target)
        if not sid:
            return CommonExecutionResult.TRUE
        try:
            # pick the first agent not already mapped to a Sim
            agent = AGENTS[0]
            ok, st = host_client.status()
            if ok:
                used = (st.get('config') or {}).get('simMap') or {}
                agent = next((a for a in AGENTS if not used.get(a)), AGENTS[0])
            host_client.set_sim(agent, sid)
            host_client.connect_bridge(BRIDGE_URL)
            ok, _ = host_client.start()
            if ok:
                ui.notify('5imulites', '%s is now playing this Sim. It will live on its own.' % agent.upper())
            else:
                ui.notify('5imulites', 'Mapped this Sim, but the host is not running. Start it (npm run dev).')
        except Exception:
            pass
        return CommonExecutionResult.TRUE


class FiveSimSetup(_Base):
    def on_started(self, interaction_sim: Sim, interaction_target: Any) -> CommonExecutionResult:
        try:
            ui.open_setup()
        except Exception:
            pass
        return CommonExecutionResult.TRUE


class FiveSimStop(_Base):
    def on_started(self, interaction_sim: Sim, interaction_target: Any) -> CommonExecutionResult:
        try:
            host_client.stop()
            ui.notify('5imulites', 'AI stopped — you have control again.')
        except Exception:
            pass
        return CommonExecutionResult.TRUE


@CommonInteractionRegistry.register_interaction_handler(CommonInteractionType.ON_SCRIPT_OBJECT_LOAD)
class _FiveSimInteractionHandler(CommonScriptObjectInteractionHandler):
    @property
    def interactions_to_add(self) -> Tuple[int]:
        return (INTERACTION_PLAY_ID, INTERACTION_SETUP_ID, INTERACTION_STOP_ID)

    def should_add(self, script_object, *args, **kwargs) -> bool:
        return isinstance(script_object, Sim)
