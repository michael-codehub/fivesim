# Execute an agent's chosen action inside the game.
# MUST run on the simulation (main) thread — called only from the drain alarm.
# Reliability ranking: (1) console cheat -> (2) push interaction -> (3) helpers.
import services
import sims4.commands
import sims4.resources
from interactions.context import InteractionContext
from interactions.priority import Priority
from .ids import INTERACTION_GUIDS, INTERACTION_AFFORDANCE_NAMES, LOT_CATALOG


def _sim_instance(sim_id):
    si = services.sim_info_manager().get(int(sim_id))
    if si is None:
        return None, None
    return si, si.get_sim_instance()


def _running_interactions(sim):
    try:
        return list(sim.get_all_running_and_queued_interactions())
    except Exception:
        return []


def _is_running(sim, affordance):
    want = getattr(affordance, '__name__', None)
    for si in _running_interactions(sim):
        try:
            aff = getattr(si, 'affordance', None)
            if aff is affordance or (want and getattr(aff, '__name__', None) == want):
                return True
        except Exception:
            continue
    return False


def _cancel_running(sim):
    """Interrupt whatever the Sim is doing so a new decision takes over."""
    try:
        from interactions.interaction_finisher import FinishingType
        reason = FinishingType.USER_CANCEL
    except Exception:
        FinishingType = None
        reason = None
    for si in _running_interactions(sim):
        try:
            if reason is not None:
                si.cancel(reason, cancel_reason_msg='fivesim override')
            else:
                si.cancel_user(cancel_reason_msg='fivesim override')
        except Exception:
            continue


def _set_speed(n):
    import clock
    modes = {
        0: clock.ClockSpeedMode.PAUSED,
        1: clock.ClockSpeedMode.NORMAL,
        2: clock.ClockSpeedMode.SPEED2,
        3: clock.ClockSpeedMode.SPEED3,
    }
    services.game_clock_service().set_clock_speed(modes.get(int(n), clock.ClockSpeedMode.NORMAL))


# Remember the last fivesim-pushed affordance per Sim, so we can tell when the Sim
# is STILL performing our action (and must not be interrupted) and report that to
# the host. Keyed by str(sim_id).
_pushed = {}


def _sim_id_str(sim):
    try:
        return str(sim.sim_info.sim_id)
    except Exception:
        try:
            return str(sim.id)
        except Exception:
            return None


def _mark_pushed(sim, aff_name):
    sid = _sim_id_str(sim)
    if sid is not None:
        _pushed[sid] = (aff_name or '').lower()


def running_affordance_names(sim):
    """Lowercased __name__s of the Sim's running + queued interactions."""
    names = []
    for si in _running_interactions(sim):
        try:
            nm = getattr(getattr(si, 'affordance', None), '__name__', '') or ''
            if nm:
                names.append(nm.lower())
        except Exception:
            continue
    return names


def is_fivesim_running(sim):
    """True if the Sim is still performing the LAST fivesim-pushed action — the
    host uses this to avoid re-deciding (which would cancel it mid-animation)."""
    sid = _sim_id_str(sim)
    if sid is None:
        return False
    want = _pushed.get(sid)
    if not want:
        return False
    return want in running_affordance_names(sim)


def _make_context(sim):
    """A forced, user-directed, high-priority push that preempts the queue — the
    robust pattern (matches Sims4CommunityLibrary). Falls back to the basic 3-arg
    context if a kwarg isn't supported on this game build."""
    src = InteractionContext.SOURCE_SCRIPT_WITH_USER_INTENT
    try:
        from interactions.context import QueueInsertStrategy
        return InteractionContext(
            sim, src, Priority.High,
            run_priority=Priority.High,
            insert_strategy=QueueInsertStrategy.NEXT,
        )
    except Exception:
        return InteractionContext(sim, src, Priority.High)


def execute_action(action):
    """
    action = { "type": "console"|"interaction"|"go_to_work"|"modify_funds",
               "sim_id": <int>, ...type-specific... }
    """
    a_type = action.get('type')

    if a_type == 'console':
        cmd = action['command']
        sims4.commands.execute(cmd, None)
        return {'ok': True, 'mode': 'console', 'command': cmd}

    if a_type == 'modify_funds':
        amount = int(action['amount'])
        hh = services.active_household()
        if hh is None:
            return {'ok': False, 'error': 'no_active_household'}
        sims4.commands.execute('sims.modify_funds %d' % amount, None)
        return {'ok': True, 'mode': 'modify_funds', 'amount': amount, 'funds': hh.funds.money}

    if a_type == 'set_speed':
        try:
            _set_speed(action.get('speed', 1))
            return {'ok': True, 'mode': 'set_speed', 'speed': int(action.get('speed', 1))}
        except Exception as e:
            return {'ok': False, 'error': 'set_speed_failed: %s' % e}

    if a_type == 'focus_camera':
        # Point the in-game camera at a Sim, following it. Uses EA's camera module
        # (camera.focus_on_sim(sim, follow, client)). Best-effort — never raises.
        try:
            import camera
            si = services.sim_info_manager().get(int(action['sim_id']))
            sim = si.get_sim_instance() if si is not None else None
            if sim is None:
                return {'ok': False, 'error': 'sim_not_instantiated'}
            try:
                client = services.client_manager().get_first_client()
            except Exception:
                client = None
            camera.focus_on_sim(sim, bool(action.get('follow', True)), client)
            return {'ok': True, 'mode': 'focus_camera'}
        except Exception as e:
            return {'ok': False, 'error': 'focus_camera_failed: %s' % e}

    if a_type == 'go_to_work':
        si, sim = _sim_instance(action['sim_id'])
        if si is None or si.career_tracker is None:
            return {'ok': False, 'error': 'no_career'}
        if sim is not None:
            _cancel_running(sim)
        last = None
        for c in si.career_tracker.careers.values():
            try:
                c.push_go_to_work()
                return {'ok': True, 'mode': 'go_to_work'}
            except Exception as e:
                last = e
                continue
        return {'ok': False, 'error': 'go_to_work_failed: %s' % last if last else 'no_career_entry'}

    if a_type == 'interaction':
        return _push_interaction(action)

    return {'ok': False, 'error': 'unknown_action_type: %s' % a_type}


def _obj_super_affordances(obj):
    try:
        return list(obj.super_affordances())
    except Exception:
        try:
            return list(getattr(obj, '_super_affordances', ()) or ())
        except Exception:
            return []


def _all_objects():
    om = services.object_manager()
    try:
        return list(om.get_all())
    except Exception:
        return list(om.values()) if hasattr(om, 'values') else []


def find_object_affordance(name_sets):
    """Scan every object on the lot for a super-affordance whose (lowercased)
    name contains ALL fragments of any set in name_sets. Returns (obj, affordance,
    affordance_name) — pushing the object's OWN affordance with the object as the
    target is far more robust than a hardcoded GUID pushed onto the Sim."""
    objects = _all_objects()
    for frags in name_sets:
        for obj in objects:
            for aff in _obj_super_affordances(obj):
                nm = getattr(aff, '__name__', '') or ''
                low = nm.lower()
                if all(f in low for f in frags):
                    return obj, aff, nm
    return None, None, None


def _affordance_on(holder, name_sets):
    """Find a super-affordance the given holder (object OR Sim) provides."""
    for frags in name_sets:
        for aff in _obj_super_affordances(holder):
            low = (getattr(aff, '__name__', '') or '').lower()
            if all(f in low for f in frags):
                return aff, getattr(aff, '__name__', '')
    return None, None


def available_on_lot():
    """Human labels for what this lot actually offers — fed to the model so it
    only picks things that exist here. Reuses the same scan; call sparingly."""
    names = []
    for obj in _all_objects():
        for aff in _obj_super_affordances(obj):
            nm = getattr(aff, '__name__', '')
            if nm:
                names.append(nm.lower())
    present = []
    for label, name_sets in LOT_CATALOG:
        # present if ANY single affordance name contains ALL fragments of a set
        if any(any(all(f in n for f in frags) for n in names) for frags in name_sets):
            present.append(label)
    return present


def _resolve_affordance_guid(name):
    guid = INTERACTION_GUIDS.get(name)
    if not guid:
        return None
    key = sims4.resources.get_resource_key(guid, sims4.resources.Types.INTERACTION)
    return services.affordance_manager().get(key)


def _push_interaction(action):
    si, sim = _sim_instance(action['sim_id'])
    if sim is None:
        return {'ok': False, 'error': 'sim_not_instantiated'}
    name = action.get('interaction')

    # explicit target wins (e.g. a social interaction onto another Sim/object)
    explicit_target = None
    if action.get('target_sim_id') is not None:
        tsi = services.sim_info_manager().get(int(action['target_sim_id']))
        explicit_target = tsi.get_sim_instance() if tsi else None
    elif action.get('target_object_id') is not None:
        explicit_target = services.object_manager().get(int(action['target_object_id']))

    # a social interaction with nobody to talk to → clean no-op (never talk to self)
    if name == 'socialize' and explicit_target is None:
        return {'ok': False, 'error': 'no_target_present', 'interaction': name}

    affordance = None
    target = explicit_target
    aff_name = None
    name_sets = INTERACTION_AFFORDANCE_NAMES.get(name)

    if explicit_target is not None:
        # social / targeted: find an affordance the TARGET Sim provides (e.g. a
        # friendly chat) and push it onto them.
        if name_sets:
            affordance, aff_name = _affordance_on(explicit_target, name_sets)
    elif name_sets:
        # primary path: find an object on the lot that PROVIDES a matching
        # affordance, and push it on that object (correct target + real id).
        target, affordance, aff_name = find_object_affordance(name_sets)

    if affordance is None:
        # fallback: hardcoded GUID pushed onto the resolved/own target
        affordance = _resolve_affordance_guid(name)
        if target is None:
            target = sim

    if affordance is None:
        return {'ok': False, 'error': 'affordance_not_found', 'interaction': name}

    # already doing exactly this? let it continue instead of restarting (no thrash)
    if _is_running(sim, affordance):
        _mark_pushed(sim, aff_name)
        return {'ok': True, 'mode': 'interaction', 'affordance': aff_name, 'queued': False, 'note': 'already_running'}

    # ANTI-THRASH: if the Sim is still performing the LAST fivesim-pushed action
    # and this isn't an explicit override (paid directive / busy-cap), let it
    # finish instead of cancelling it mid-animation.
    if not action.get('interrupt') and is_fivesim_running(sim):
        return {'ok': True, 'mode': 'interaction', 'affordance': aff_name, 'queued': False, 'note': 'still_busy'}

    # otherwise interrupt whatever the Sim is doing so this decision takes over
    _cancel_running(sim)

    context = _make_context(sim)
    try:
        result = sim.push_super_affordance(affordance, target, context)
    except Exception as e:
        return {'ok': False, 'error': 'push_failed: %s' % e, 'affordance': aff_name}
    # push_super_affordance returns an EnqueueResult (test + execute); it is FALSEY
    # when the affordance's tuned test failed or it couldn't run — i.e. the Sim
    # would NOT actually perform it. Report that instead of a phantom success.
    ran = bool(result)
    if ran:
        _mark_pushed(sim, aff_name)
    return {'ok': ran, 'mode': 'interaction', 'affordance': aff_name,
            'queued': ran, 'reason': None if ran else 'test_or_execute_failed'}
