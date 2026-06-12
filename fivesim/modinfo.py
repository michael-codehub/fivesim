NAME = '5imulites Agent Bridge'
VERSION = '1.0.0'
# loopback-only HTTP bridge the host app talks to
HOST = '127.0.0.1'
PORT = 8123
# optional shared secret; if a token file exists next to the game user folder it
# is required via the X-Bridge-Token header. Loopback binding is the primary guard.
TOKEN_FILENAMES = ['fivesim_token.txt']

# Resource instance id for the bundled logo PNG (see assets/logo.png + the icon
# .package built by build_icon_package.py). Used as the dialog/notification icon.
LOGO_INSTANCE = 0x5130A1A1A1A10001

# ── pie-menu interactions (the real in-game button) ──────────────────────────
# These ids must match the tuning `s=` / DBPF instance ids in the interaction
# .package (built by build_interaction_package.py) and what interactions.py
# returns from interactions_to_add. High bit set to stay out of Maxis ranges.
INTERACTION_PLAY_ID = 0x9F1E511151510001
INTERACTION_SETUP_ID = 0x9F1E511151510002
INTERACTION_STOP_ID = 0x9F1E511151510003

# pie-menu labels + their (arbitrary but matching) STBL string keys.
# NOTE: top-level entries (no PieMenuCategory) — a custom category requires a
# paired SimData resource (every category in S4CL + reference mods ships one);
# without it the UI kills the whole pie menu. Branding lives in the label text.
LABEL_PLAY = '5imulites: Let AI Play'
LABEL_SETUP = '5imulites: Setup'
LABEL_STOP = '5imulites: Stop AI'
KEY_PLAY = 0xA1A1AA01
KEY_SETUP = 0xA1A1AA02
KEY_STOP = 0xA1A1AA03
STBL_INSTANCE = 0x0051305111510001   # high byte 0x00 = English (others fall back)

# the "5imulites" submenu (PieMenuCategory tuning) with our logo as its icon
CATEGORY_ID = 0x9F1E511151510010
KEY_CATEGORY = 0xA1A1AA10
LABEL_CATEGORY = '5imulites'

INTERACTIONS = [
    ('FiveSimPlay', INTERACTION_PLAY_ID, KEY_PLAY, LABEL_PLAY),
    ('FiveSimSetup', INTERACTION_SETUP_ID, KEY_SETUP, LABEL_SETUP),
    ('FiveSimStop', INTERACTION_STOP_ID, KEY_STOP, LABEL_STOP),
]
