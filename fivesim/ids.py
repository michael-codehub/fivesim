# Motive commodity GUIDs (resolved via the STATISTIC instance manager at runtime).
MOTIVE_GUIDS = {
    'hunger':  16656,   # motive_Hunger
    'energy':  16654,   # motive_Energy
    'fun':     16655,   # motive_Fun
    'social':  16658,   # motive_Social
    'hygiene': 16657,   # motive_Hygiene
    'bladder': 16652,   # motive_Bladder
}

# Curated, EXPLICIT super-affordance allow-list. Never push an arbitrary
# caller-supplied GUID — only keys in this table are accepted as interactions.
# Extend this as you validate each interaction GUID in-game.
INTERACTION_GUIDS = {
    'use_toilet':     13075,
    'eat_grab_quick': 13393,
    'sleep_in_bed':   13391,
    'shower':         13396,
    'talk_to':        13998,   # social super affordance (needs a target sim)
}

# Console-command recipes for actions that are far more reliable as cheats than
# as pushed interactions. {amount}/{level} are filled by the executor.
CONSOLE_RECIPES = {
    'modify_funds':   'sims.modify_funds {amount}',
    'promote':        'careers.promote {track}',
}
