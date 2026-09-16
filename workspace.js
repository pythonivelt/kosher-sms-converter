/* One shared app: tabs switch views without unloading backups or converter state. */
(() => {
  'use strict';
  const about = document.createElement('section');
  about.id = 'aboutPanel';
  document.querySelectorAll('.hero,.compat-section,.site-section,.faq-section,.contact-cta,.site-footer').forEach(el => about.append(el));
  document.getElementById('converter').after(about);
  const panels = {messages: document.getElementById('backupViewer'), converter: document.getElementById('converter'), about};
  const buttons = [...document.querySelectorAll('[data-workspace-tab]')];
  for (const [name, panel] of Object.entries(panels)) {
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', 'tab-' + name);
    panel.tabIndex = 0;
  }
  function select(name, updateHash = true) {
    if (!panels[name]) name = 'messages';
    document.body.dataset.workspace = name;
    for (const [id, panel] of Object.entries(panels)) panel.hidden = id !== name;
    for (const button of buttons) {
      const active = button.dataset.workspaceTab === name;
      button.setAttribute('aria-selected', String(active)); button.tabIndex = active ? 0 : -1;
    }
    if (updateHash) history.replaceState(null, '', '#' + name);
  }
  const fromHash = () => select(location.hash === '#backupViewer' ? 'messages' : location.hash.slice(1), false);
  buttons.forEach((button, index) => {
    button.onclick = () => select(button.dataset.workspaceTab);
    button.onkeydown = e => {
      const next = e.key === 'ArrowRight' ? (index + 1) % buttons.length : e.key === 'ArrowLeft' ? (index + buttons.length - 1) % buttons.length : e.key === 'Home' ? 0 : e.key === 'End' ? buttons.length - 1 : -1;
      if (next >= 0) {e.preventDefault(); buttons[next].focus(); buttons[next].click();}
    };
  });
  window.addEventListener('hashchange', fromHash);
  if (new URLSearchParams(location.search).has('desktop')) document.body.classList.add('desktop-app');
  fromHash();
})();
