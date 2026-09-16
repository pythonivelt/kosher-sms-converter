'use strict';
const {app, BrowserWindow, Menu, shell, dialog, session} = require('electron');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {isTrustedPage, isExternalLink, windowOptions} = require('./policy.cjs');

app.setName('Kosher SMS');
const entry = path.join(__dirname, '..', 'index.html');
const entryUrl = pathToFileURL(entry).href;
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow(windowOptions);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.webContents.setWindowOpenHandler(({url}) => {
    if (isExternalLink(url)) shell.openExternal(url).catch(() => {});
    return {action: 'deny'};
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!isTrustedPage(url, entryUrl)) {
      event.preventDefault();
      if (isExternalLink(url)) shell.openExternal(url).catch(() => {});
    }
  });
  mainWindow.webContents.on('will-attach-webview', event => event.preventDefault());
  mainWindow.webContents.on('render-process-gone', () => {
    dialog.showMessageBox(mainWindow, {type: 'error', title: 'Viewer stopped', message: 'The viewer stopped unexpectedly.', detail: 'Reopen the app and select your backup again. Your original files have not been changed.'});
  });
  mainWindow.loadFile(entry, {query: {desktop: '1'}, hash: 'messages'}).catch(error => {
    dialog.showErrorBox('Could not open Kosher SMS', error.message);
    app.quit();
  });
}

app.whenReady().then(() => {
  // Non-persistent browser session: backup data never needs a saved web profile.
  const localSession = session.fromPartition('kosher-sms');
  localSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  localSession.setPermissionCheckHandler(() => false);
  localSession.webRequest.onBeforeRequest({urls: ['http://*/*', 'https://*/*', 'ws://*/*', 'wss://*/*']}, (_details, callback) => callback({cancel: true}));
  // Inline code belongs to the existing converter. File contents are displayed as text.
  localSession.webRequest.onHeadersReceived((details, callback) => callback({responseHeaders: {
    ...details.responseHeaders,
    'Content-Security-Policy': ["default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'"]
  }}));
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {label: 'File', submenu: [{role: 'quit', label: 'Quit Kosher SMS'}]},
    {label: 'Edit', submenu: [{role: 'undo'}, {role: 'redo'}, {type: 'separator'}, {role: 'cut'}, {role: 'copy'}, {role: 'paste'}, {role: 'selectAll'}]},
    {label: 'View', submenu: [{role: 'resetZoom'}, {role: 'zoomIn'}, {role: 'zoomOut'}, {type: 'separator'}, {role: 'togglefullscreen'}]},
    {label: 'Help', submenu: [{label: 'About Kosher SMS', click: () => dialog.showMessageBox(mainWindow, {title: 'Kosher SMS', message: 'Kosher SMS ' + app.getVersion(), detail: 'Local SMS, MMS and contacts viewer with backup conversion.\n\nOpen a backup in Messages, or switch to Converter. All processing happens on this computer.'})}]}
  ]));
  createWindow();
  app.on('activate', () => {if (BrowserWindow.getAllWindows().length === 0) createWindow();});
});
app.on('window-all-closed', () => {if (process.platform !== 'darwin') app.quit();});
