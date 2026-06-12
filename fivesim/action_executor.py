# Execute an agent's chosen action inside the game.
# MUST run on the simulation (main) thread — called only from the drain alarm.
# Reliability ranking: (1) console cheat -> (2) push interaction -> (3) helpers.
import services
import sims4.commands
import sims4.resources
from interactions.context import InteractionContext
from interactions.priority import Priority
from .ids import INTERACTION_GUIDS


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


def _resolve_affordance(action):
    name = action.get('interaction')
    guid = INTERACTION_GUIDS.get(name) if name else None
    if guid is None:
        return None
    key = sims4.resources.get_resource_key(guid, sims4.resources.Types.INTERACTION)
    return services.affordance_manager().get(key)


def _resolve_target(action, sim):
    tgt_sim_id = action.get('target_sim_id')
    if tgt_sim_id is not None:
        tsi = services.sim_info_manager().get(int(tgt_sim_id))
        return tsi.get_sim_instance() if tsi else None
    obj_id = action.get('target_object_id')
    if obj_id is not None:
        return services.object_manager().get(int(obj_id))
    return sim


def _push_interaction(action):
    si, sim = _sim_instance(action['sim_id'])
    if sim is None:
        return {'ok': False, 'error': 'sim_not_instantiated'}
    affordance = _resolve_affordance(action)
    if affordance is None:
        return {'ok': False, 'error': 'affordance_not_found'}
    target = _resolve_target(action, sim)
    context = InteractionContext(
        sim,
        InteractionContext.SOURCE_SCRIPT_WITH_USER_INTENT,
        Priority.High,
    )
    try:
        result = sim.push_super_affordance(affordance, target, context)
    except Exception as e:
        return {'ok': False, 'error': 'push_failed: %s' % e}
    return {'ok': bool(result), 'mode': 'interaction', 'queued': bool(result)}
