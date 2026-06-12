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
