const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    icon: path.join(__dirname, 'public/img/FAVICON.png'), 
    webPreferences: {
      preload: path.join(__dirname, 'renderer.js'),
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

app.whenReady().then(createWindow);

ipcMain.handle('save-consent', async (event, consentData) => {
  const file_path = path.join(app.getPath('userData'), 'consent.json');

  fs.writeFileSync(file_path, JSON.stringify(consentData, null, 2));
  return {success: true, path: file_path};
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});