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


def list_present_sims():
    """Every Sim instantiated on the ACTIVE LOT right now — household members who
    are home PLUS visiting non-household Sims (neighbors, walk-bys, townies). This
    is what lets the agent actually socialize with whoever is physically around
    instead of being stuck with the household roster. Best-effort + never raises."""
    out = []
    seen = set()
    hh = services.active_household()
    hh_ids = set(si.sim_id for si in hh.sim_info_gen()) if hh is not None else set()
    try:
        mgr = services.sim_info_manager()
        for sim in mgr.instanced_sims_gen():
            try:
                # only those actually on the active lot (skip Sims off elsewhere)
                if not sim.is_on_active_lot():
                    continue
            except Exception:
                pass
            try:
                si = sim.sim_info
                sid = si.sim_id
                if sid in seen:
                    continue
                seen.add(sid)
                out.append({
                    'sim_id': str(sid),
                    'name': '{} {}'.format(si.first_name, si.last_name),
                    'is_household': sid in hh_ids,
                })
            except Exception:
                continue
    except Exception:
        pass
    return out


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

    # relationships — resolve each target's NAME so the model can address real
    # people by name (and never a placeholder that isn't in this game).
    rels = []
    rt = sim_info.relationship_tracker
    try:
        for rel in rt:
            tid = rel.target_sim_id
            try:
                tinfo = services.sim_info_manager().get(tid)
                tname = '{} {}'.format(tinfo.first_name, tinfo.last_name) if tinfo is not None else None
                rels.append({
                    'target_id': str(tid),   # 64-bit id as a string (JS rounds > 2^53)
                    'name': tname,
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

    # what the Sim is doing RIGHT NOW + whether it's still our last pushed action.
    # The host uses running_fivesim to avoid re-deciding (which would cancel the
    # action mid-animation — the "thinks but never acts" bug).
    try:
        from . import action_executor as _ae
        if sim is not None:
            state['running'] = _ae.running_affordance_names(sim)
            state['running_fivesim'] = bool(_ae.is_fivesim_running(sim))
        else:
            state['running'] = []
            state['running_fivesim'] = False
    except Exception:
        state['running'] = []
        state['running_fivesim'] = False

    return state


def build_state_for(sim_id):
    sim_info = services.sim_info_manager().get(int(sim_id))
    if sim_info is None:
        return None
    return build_sim_state(sim_info)
