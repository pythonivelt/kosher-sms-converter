/* Run with: electron tests/electron-smoke.cjs. Uses fictional data only. */
'use strict';
const {app} = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const output = path.resolve(__dirname, '..', 'dist', 'electron-smoke');
fs.mkdirSync(output, {recursive:true});
app.setPath('userData', path.join(output, 'profile'));
let finished = false;
function finish(result) {
  if (finished) return; finished = true;
  fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result, null, 2));
  app.exit(result.ok ? 0 : 1);
}
setTimeout(() => finish({ok:false, error:'Electron smoke test timed out'}), 45000);
app.on('browser-window-created', (_event, win) => {
  win.on('show', () => win.hide());
  win.webContents.on('did-fail-load', (_e, code, description) => finish({ok:false, error:description, code}));
  win.webContents.once('did-finish-load', async () => {
    try {
      const result = await win.webContents.executeJavaScript(`(async () => {
        const $ = id => document.getElementById(id);
        if (typeof require !== 'undefined' || typeof process !== 'undefined') throw Error('Node is exposed to the renderer');
        if ($('converter').hidden !== true) throw Error('Default tab is not Messages');
        const png = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
        const xml = '<smses><sms address="2125550100" date="1700000000000" type="1" body="Electron test"/><mms address="2125550100" date="1700000001" msg_box="1"><parts><part ct="image/png" data="'+png+'"/></parts></mms></smses>';
        BackupConverter.open(new File([xml], 'smoke.xml'));
        const wait = async test => {for (let i=0;i<500;i++){if(test())return;await new Promise(r=>setTimeout(r,20));}throw Error('Timed out waiting for UI');};
        await wait(()=>$('bv-status').textContent.startsWith('2 messages'));
        await wait(()=>document.querySelector('.bv-attachment img')?.naturalWidth>0);
        $('tab-converter').click();
        if (!$('backupViewer').hidden || $('converter').hidden) throw Error('Converter tab failed');
        $('tab-messages').click();
        if (document.querySelectorAll('.bv-bubble').length!==2) throw Error('Backup lost on tab switch');
        return {ok:true, checks:['Electron startup','sandboxed renderer','local file assets','XML import','inline image','tab state preservation']};
      })()`);
      finish(result);
    } catch (error) {finish({ok:false,error:error.stack});}
  });
});
require('../desktop/main.cjs');
