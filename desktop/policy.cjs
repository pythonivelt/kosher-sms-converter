'use strict';
function isTrustedPage(candidate, entry) {
  try {const url = new URL(candidate), expected = new URL(entry); return url.protocol === 'file:' && url.host === expected.host && url.pathname === expected.pathname;} catch {return false;}
}
function isExternalLink(candidate) {
  try {const url = new URL(candidate); return url.protocol === 'https:' && !url.username && !url.password && ['github.com', 'play.google.com', 'drive.google.com'].includes(url.hostname);} catch {return false;}
}
const windowOptions = {
  title: 'Kosher SMS', width: 1240, height: 860, minWidth: 640, minHeight: 540,
  show: false, backgroundColor: '#f3f4fb', autoHideMenuBar: true,
  webPreferences: {
    partition: 'kosher-sms', nodeIntegration: false, contextIsolation: true,
    sandbox: true, webSecurity: true, webviewTag: false, spellcheck: false
  }
};
module.exports = {isTrustedPage, isExternalLink, windowOptions};
