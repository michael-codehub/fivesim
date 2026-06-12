# Optional rich in-game UI via Sims4CommunityLibrary (S4CL). Imported lazily from
# `fivesim.setup` — if S4CL isn't installed this module simply fails to import and
# the console commands remain the fallback. All calls are wrapped defensively
# because S4CL signatures vary slightly across versions.
# module is named common_input_text_dialog in current S4CL (verified v3.21)
try:
    from sims4communitylib.dialogs.common_input_text_dialog import CommonInputTextDialog
except ImportError:
    from sims4communitylib.dialogs.input_text_dialog import CommonInputTextDialog
from sims4communitylib.dialogs.choose_object_dialog import CommonChooseObjectDialog
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from ui.ui_dialog_picker import ObjectPickerRow

from .modidentity import ModInfo
from .modinfo import LOGO_INSTANCE, HOST, PORT
from . import host_client

BRIDGE_URL = 'http://%s:%d' % (HOST, PORT)

MODELS = [
    'openai/gpt-5.4-nano', 'openai/gpt-5.5',
    'anthropic/claude-haiku-4.5', 'anthropic/claude-sonnet-4.6',
    'google/gemini-2.5-flash', 'google/gemini-2.5-pro',
    'deepseek/deepseek-v3.2', 'qwen/qwen3.6-flash', 'qwen/qwen3.7-max',
]


def _logo_icon():
    try:
        from sims4communitylib.utils.common_resource_utils import CommonResourceUtils
        from sims4.resources import Types
        from distributor.shared_messages import IconInfoData
        key = CommonResourceUtils.get_resource_key(Types.PNG, LOGO_INSTANCE)
        return IconInfoData(icon_resource=key)
    except Exception:
        return None


def notify(title, text):
    try:
        n = CommonBasicNotification(title, text)
        icon = _logo_icon()
        if icon is not None:
            n.show(icon=icon)
        else:
            n.show()
    except Exception:
        pass


def open_setup():
    def _on_key(value, outcome):
        try:
            if not value:
                return
            host_client.set_key(value)
            host_client.connect_bridge(BRIDGE_URL)
            notify('5imulites connected',
                   'API key saved. Next: open the cheat console and type '
                   '"fivesim.sims", then "fivesim.map <agent> <sim_id>", then "fivesim.start".')
        except Exception:
            pass

    dialog = CommonInputTextDialog(
        ModInfo.get_identity(),
        '5imulites — OpenRouter API key',
        'Paste your OpenRouter key. It is sent to your local host, never bundled.',
        '',
    )
    dialog.show(on_submit=_on_key)


def choose_model(agent, on_done=None):
    def _on_chosen(chosen, outcome):
        if not chosen:
            return
        host_client.set_model(agent, chosen)
        notify('5imulites', '%s now plays with %s' % (agent, chosen))
        if on_done:
            try:
                on_done(chosen)
            except Exception:
                pass

    rows = []
    for i, name in enumerate(MODELS):
        rows.append(ObjectPickerRow(option_id=i, name=name, row_description=None,
                                    row_tooltip=None, icon=None, tag=name))
    dialog = CommonChooseObjectDialog(
        'Choose a model for %s' % agent,
        'Pick which model drives this mind',
        tuple(rows),
        per_page=12,
    )
    dialog.show(on_chosen=_on_chosen)
