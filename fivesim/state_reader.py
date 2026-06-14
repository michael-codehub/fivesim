# Build ground-truth Sim state as plain JSON-able dicts.
# MUST run on the simulation (main) thread — call only from the drain alarm.
import services
import sims4.resources
from .ids import MOTIVE_GUIDS


def _stat_cls(guid):
    mgr = services.get_instance_manager(sims4.resources.Types.STATISTIC)
    return mgr.get(guid)


def has_active_household():
    return services.active_household() is not None


def list_sim_ids():
    """All controllable household SimInfos -> stable ids for model mapping."""
    hh = services.active_household()
    if hh is None:
        return []
    return [si.sim_id for si in hh.sim_info_gen()]


def build_sim_state(sim_info):
    state = {
        'sim_id': str(sim_info.sim_id),   # 64-bit id as a string (JS rounds numbers > 2^53)
        'name': '{} {}'.format(sim_info.first_name, sim_info.last_name),
        'instantiated': sim_info.get_sim_instance() is not None,
    }

    # six motives (Commodity stats on the commodity_tracker), normalized 0..100
    ct = sim_info.commodity_tracker
    needs = {}
    for key, guid in MOTIVE_GUIDS.items():
        cls = _stat_cls(guid)
        if cls is None:
            continue
        try:
            raw = ct.get_value(cls)          # ~ -100..+100
            needs[key] = round((raw + 100.0) / 2.0, 1)
        except Exception:
            needs[key] = None
    state['needs'] = needs

    # household funds
    hh = sim_info.household
    state['funds'] = hh.funds.money if hh is not None else None

    # skills (also commodities on the tracker)
    skills = {}
    try:
        for s in ct:
            if getattr(s, 'is_skill', False):
                try:
                    skills[s.__class__.__name__] = s.get_user_value()
                except Exception:
                    pass
    except Exception:
        pass
    state['skills'] = skills

    # careers
    careers = []
    tracker = sim_info.career_tracker
    if tracker is not None:
        try:
            for career in tracker.careers.values():
                lvl = career.current_level_tuning
                careers.append({
                    'track': career.current_track_tuning.__class__.__name__,
                    'level': career.level,
                    'user_level': career.user_level,
                    'title': str(lvl.get_career_name(sim_info)),
                })
        except Exception:
            pass
    state['careers'] = careers

    # relationships
    rels = []
    rt = sim_info.relationship_tracker
    try:
        for rel in rt:
            tid = rel.target_sim_id
            try:
                rels.append({
                    'target_id': tid,
                    'friendship': rt.get_relationship_score(tid),
                    'depth': rt.get_relationship_depth(tid),
                })
            except Exception:
                pass
    except Exception:
        pass
    state['relationships'] = rels

    # current position / lot
    sim = sim_info.get_sim_instance()
    try:
        state['position'] = str(sim.position) if sim is not None else None
    except Exception:
        state['position'] = None

    return state


def build_state_for(sim_id):
    sim_info = services.sim_info_manager().get(int(sim_id))
    if sim_info is None:
        return None
    return build_sim_state(sim_info)
