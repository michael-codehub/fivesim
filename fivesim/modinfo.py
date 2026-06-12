NAME = '5imulites Agent Bridge'
VERSION = '1.0.0'
# loopback-only HTTP bridge the host app talks to
HOST = '127.0.0.1'
PORT = 8123
# optional shared secret; if a token file exists next to the game user folder it
# is required via the X-Bridge-Token header. Loopback binding is the primary guard.
TOKEN_FILENAMES = ['fivesim_token.txt']
