# Execute an agent's chosen action inside the game.
# MUST run on the simulation (main) thread — called only from the drain alarm.
# Reliability ranking: (1) console cheat -> (2) push interaction -> (3) helpers.
import services
import sims4.commands
import sims4.resources
from interactions.context import InteractionContext
from interactions.priority import Priority
from .ids import INTERACTION_GUIDS, INTERACTION_AFFORDANCE_NAMES


def _sim_instance(sim_id):
    si = services.sim_info_manager().get(int(sim_id))
    if si is None:
        return None, None
    return si, si.get_sim_instance()


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

    if a_type == 'go_to_work':
        si, _ = _sim_instance(action['sim_id'])
        if si is None or si.career_tracker is None:
            return {'ok': False, 'error': 'no_career'}
        for c in si.career_tracker.careers.values():
            try:
                c.push_go_to_work()
                return {'ok': True, 'mode': 'go_to_work'}
            except Exception as e:
                return {'ok': False, 'error': 'go_to_work_failed: %s' % e}
        return {'ok': False, 'error': 'no_career_entry'}

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


def find_object_affordance(name_sets):
    """Scan every object on the lot for a super-affordance whose (lowercased)
    name contains ALL fragments of any set in name_sets. Returns (obj, affordance,
    affordance_name) — pushing the object's OWN affordance with the object as the
    target is far more robust than a hardcoded GUID pushed onto the Sim."""
    om = services.object_manager()
    try:
        objects = list(om.get_all())
    except Exception:
        objects = list(om.values()) if hasattr(om, 'values') else []
    for frags in name_sets:
        for obj in objects:
            for aff in _obj_super_affordances(obj):
                nm = getattr(aff, '__name__', '') or ''
                low = nm.lower()
                if all(f in low for f in frags):
                    return obj, aff, nm
    return None, None, None


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

    affordance = None
    target = explicit_target
    aff_name = None

    if explicit_target is None:
        # primary path: find an object on the lot that PROVIDES a matching
        # affordance, and push it on that object (correct target + real id).
        name_sets = INTERACTION_AFFORDANCE_NAMES.get(name)
        if name_sets:
            target, affordance, aff_name = find_object_affordance(name_sets)

    if affordance is None:
        # fallback: hardcoded GUID pushed onto the resolved/own target
        affordance = _resolve_affordance_guid(name)
        if target is None:
            target = sim

    if affordance is None:
        return {'ok': False, 'error': 'affordance_not_found', 'interaction': name}

    context = InteractionContext(
        sim,
        InteractionContext.SOURCE_SCRIPT_WITH_USER_INTENT,
        Priority.High,
    )
    try:
        result = sim.push_super_affordance(affordance, target, context)
    except Exception as e:
        return {'ok': False, 'error': 'push_failed: %s' % e, 'affordance': aff_name}
    return {'ok': bool(result), 'mode': 'interaction', 'affordance': aff_name, 'queued': bool(result)}
