const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  saveConsent: (data) => ipcRenderer.invoke('save-consent', data),
});
