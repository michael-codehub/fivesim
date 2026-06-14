// 5imulites Host — Electron desktop app.
// Boots the bundled NestJS host (on 127.0.0.1:4000, the port the in-game mod
// talks to) inside this process, then shows the control panel in a native window.
const { app, BrowserWindow, shell, Menu } = require('electron');
const path = require('path');
const http = require('http');

const PORT = 4000;
const URL = `http://127.0.0.1:${PORT}/host`;

// keep all runtime config (API key, model + Sim mapping) under the OS user-data
// dir so it persists between launches and survives app updates.
try { app.setPath('userData', app.getPath('userData')); process.chdir(app.getPath('userData')); } catch (e) {}

// the bundled server has an "open the browser when packaged" path — suppress it,
// we render in-app instead.
process.env.FIVESIM_OPEN = '0';
process.env.PORT = String(PORT);
process.env.NODE_ENV = process.env.NODE_ENV || 'production';

let win = null;
let serverStarted = false;

function startServer() {
  if (serverStarted) return;
  serverStarted = true;
  try {
    // requiring the ncc bundle runs bootstrap() -> app.listen(PORT)
    require(path.join(__dirname, 'server', 'index.js'));
  } catch (e) {
    console.error('host server failed to start:', e);
  }
}

function ping(cb) {
  const req = http.get(URL, (res) => { res.resume(); cb(res.statusCode > 0); });
  req.on('error', () => cb(false));
  req.setTimeout(1200, () => { req.destroy(); cb(false); });
}

function waitForServer(done, tries = 0) {
  ping((ok) => {
    if (ok) return done();
    if (tries > 120) return done(); // ~30s; load anyway so the user sees an error
    setTimeout(() => waitForServer(done, tries + 1), 250);
  });
}

function createWindow() {
  win = new BrowserWindow({
    width: 1080,
    height: 860,
    minWidth: 760,
    minHeight: 600,
    backgroundColor: '#0a0c10',
    title: '5imulites Host',
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'build', 'icon.png'),
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  Menu.setApplicationMenu(null);

  // external links (openrouter.ai) open in the real browser, not a child window
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  win.loadFile(path.join(__dirname, 'loading.html'));
  startServer();
  waitForServer(() => { if (win && !win.isDestroyed()) win.loadURL(URL); });
}

// single instance — a second launch just focuses the existing window
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
  app.whenReady().then(createWindow);
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  app.on('window-all-closed', () => app.quit());
}
