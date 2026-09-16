/* Local viewer: consumes converter records; never parses phone backups itself. */
(() => {
  'use strict';
  const root = document.getElementById('backupViewer');
  const api = window.BackupConverter;
  const PAGE = 60;
  root.innerHTML = `
    <header class="bv-toolbar"><div><h2>Backup viewer</h2><p>SMS, pictures & contacts · Files stay on this device</p></div>
      <div class="bv-actions"><label class="bv-button">Open backup<input id="bv-backup" type="file" accept=".xml,.zip"></label>
      <label class="bv-button">Add contacts<input id="bv-vcard" type="file" accept=".vcf,.vcard" multiple></label>
      <button id="bv-clear" type="button">Close files</button></div></header>
    <p id="bv-status" role="status">Open a ZIP/XML backup, or a vCard (.vcf) contacts file. Switch to the Converter tab to convert backups.</p>
    <div id="bv-progress" class="bv-progress" hidden><progress id="bv-progress-bar" max="100" value="0" aria-label="Backup progress"></progress><button id="bv-cancel" type="button">Cancel</button></div>
    <div class="bv-layout"><aside aria-label="Conversations and contacts">
      <label class="bv-search-label" for="bv-search">Search messages, names or numbers</label>
      <input id="bv-search" type="search" placeholder="Search this backup…">
      <div class="bv-tabs"><button id="bv-messages-tab" aria-pressed="true">Conversations</button><button id="bv-contacts-tab" aria-pressed="false">Contacts</button></div>
      <div id="bv-list" aria-label="Search results"></div>
      <nav class="bv-pager" aria-label="Conversation pages"><button id="bv-list-prev">Previous</button><span id="bv-list-page"></span><button id="bv-list-next">Next</button></nav>
    </aside><section class="bv-thread" aria-label="Selected conversation">
      <header><h3 id="bv-title">Your conversations, together</h3><p id="bv-number"></p></header>
      <div id="bv-messages" tabindex="0"><p class="bv-empty">Choose a backup to read messages here. Nothing is uploaded or saved to browser storage.</p></div>
      <nav class="bv-pager" aria-label="Message pages"><button id="bv-older">Older</button><span id="bv-page"></span><button id="bv-newer">Newer</button></nav>
    </section></div>`;
  const $ = id => document.getElementById('bv-' + id);
  const node = (tag, text, cls) => {const el = document.createElement(tag); if (text != null) el.textContent = text; if (cls) el.className = cls; return el;};
  const pause = () => new Promise(resolve => setTimeout(resolve, 0));
  const cleanName = name => /^(null|undefined|\(unknown\)|unknown)$/i.test(String(name || '').trim()) ? '' : String(name || '').trim();
  // Match common US local/international spellings, preserving international codes elsewhere.
  const key = raw => {const s = String(raw || '').trim(); if (/[a-z@]/i.test(s)) return s.toLowerCase(); const n = s.replace(/\D/g, ''); return n.length === 11 && n[0] === '1' ? n.slice(1) : n || s;};
  const date = m => {const n = Number(m.date); return Number.isFinite(n) && n > 0 ? (n < 1e12 ? n * 1000 : n) : 0;};
  const body = m => m.type === 'sms' ? m.body || '' : (m.parts || []).filter(p => !api.hasAttach(p)).map(p => p.text || '').join('\n');
  let messages = [], threads = [], contacts = new Map(), imported = new Map(), results = [];
  let selected = null, listPage = 0, messagePage = 0, mode = 'messages';
  let renderRun = 0, searchRun = 0, loadRun = 0, urls = [], observer, debounce, previousStatus = '', progressMessage = '';
  function disposeMedia() {
    renderRun++; observer?.disconnect();
    urls.forEach(url => URL.revokeObjectURL(url)); urls = [];
  }
  function reset(clearContacts = false) {
    loadRun++; searchRun++; clearTimeout(debounce); disposeMedia();
    $('progress').hidden = true;
    messages = []; threads = []; results = []; selected = null; listPage = 0;
    if (clearContacts) imported.clear();
    contacts = new Map(imported);
    $('search').value = ''; $('backup').value = ''; $('vcard').value = '';
    $('title').textContent = 'Your conversations, together'; $('number').textContent = '';
    $('messages').replaceChildren(node('p', 'Open a backup or select a contact.', 'bv-empty'));
    $('status').textContent = 'Files closed. Open a backup or add contacts.';
    renderList(); updateMessagePager(0);
  }
  async function load(records, own) {
    const run = ++loadRun; messages = records;
    mode = 'messages'; setTabs();
    contacts = new Map(imported);
    const groups = new Map();
    $('status').textContent = 'Organizing conversations…';
    for (let i = 0; i < records.length; i++) {
      const m = records[i];
      let numbers = m.isGroup ? (m.addrs || []).map(a => a.address).filter(a => api.normNum(a) && api.normNum(a) !== own) : [m.address];
      numbers = [...new Map(numbers.filter(a => a && a !== 'insert-address-token').map(a => [key(a), a])).values()];
      if (!numbers.length) numbers = ['Unknown number'];
      const id = JSON.stringify(numbers.map(key).sort());
      if (!groups.has(id)) groups.set(id, {id, numbers, ids: [], latest: 0});
      const thread = groups.get(id); thread.ids.push(i); thread.latest = Math.max(thread.latest, date(m));
      const name = cleanName(m.contactName);
      if (name && numbers.length === 1 && !contacts.has(key(numbers[0]))) contacts.set(key(numbers[0]), {name, number: numbers[0]});
      if (i % 2000 === 0) {await pause(); if (run !== loadRun) return;}
    }
    threads = [...groups.values()];
    for (let i = 0; i < threads.length; i++) {
      threads[i].ids.sort((a, b) => date(records[a]) - date(records[b]) || a - b);
      if (i % 500 === 0) {await pause(); if (run !== loadRun) return;}
    }
    threads.sort((a, b) => b.latest - a.latest);
    selected = null; await search();
  }
  function title(row) {return row.numbers.map(n => contacts.get(key(n))?.name || n).join(', ');}
  function contactRows() {
    return [...contacts.entries()].map(([id, c]) => ({id: 'contact:' + id, numbers: [c.number], ids: [], contact: true})).sort((a, b) => title(a).localeCompare(title(b)));
  }
  async function search() {
    const run = ++searchRun, q = $('search').value.trim().toLocaleLowerCase();
    const source = mode === 'contacts' ? contactRows() : threads, found = [];
    let checked = 0;
    $('status').textContent = 'Searching…';
    for (const row of source) {
      const nameMatch = (title(row) + ' ' + row.numbers.join(' ') + ' ' + row.numbers.map(key).join(' ')).toLocaleLowerCase().includes(q);
      if (!q || nameMatch) found.push(row);
      else if (!row.contact) {
        const ids = [];
        for (const id of row.ids) {
          if (body(messages[id]).toLocaleLowerCase().includes(q)) ids.push(id);
          if (++checked % 2000 === 0) {await pause(); if (run !== searchRun) return;}
        }
        if (ids.length) found.push({...row, ids, filtered: true});
      }
      if (++checked % 2000 === 0) {await pause(); if (run !== searchRun) return;}
    }
    if (run !== searchRun) return;
    results = found; listPage = 0;
    $('status').textContent = `${messages.length.toLocaleString()} messages · ${threads.length.toLocaleString()} conversations · ${contacts.size.toLocaleString()} contact numbers${q ? ' · ' + found.length.toLocaleString() + ' results' : ''}`;
    const next = found.find(row => row.id === selected?.id) || found[0];
    selected = next || null; renderList();
    if (next) select(next);
    else {disposeMedia(); $('title').textContent = 'No results'; $('number').textContent = ''; $('messages').replaceChildren(node('p', q ? 'Try another name, number or phrase.' : 'Open a backup or add contacts to begin.', 'bv-empty')); updateMessagePager(0);}
  }
  function renderList() {
    const fragment = document.createDocumentFragment();
    for (const row of results.slice(listPage * PAGE, (listPage + 1) * PAGE)) {
      const button = node('button', null, 'bv-conversation'); button.type = 'button';
      button.setAttribute('aria-pressed', String(selected?.id === row.id));
      button.append(node('strong', title(row)), node('span', row.numbers.join(', ')));
      if (!row.contact) button.append(node('small', `${row.ids.length.toLocaleString()} ${row.filtered ? 'matching ' : ''}messages`));
      button.onclick = () => select(row); fragment.append(button);
    }
    $('list').replaceChildren(fragment);
    $('list-page').textContent = results.length ? `${listPage + 1} / ${Math.ceil(results.length / PAGE)}` : '0 results';
    $('list-prev').disabled = listPage === 0; $('list-next').disabled = (listPage + 1) * PAGE >= results.length;
  }
  function select(row) {
    selected = row; messagePage = Math.max(0, Math.ceil(row.ids.length / PAGE) - 1);
    renderList(); renderMessages();
  }
  function updateMessagePager(total) {
    $('older').disabled = messagePage === 0 || !total;
    $('newer').disabled = (messagePage + 1) * PAGE >= total;
    $('page').textContent = total ? `${messagePage * PAGE + 1}–${Math.min(total, (messagePage + 1) * PAGE)} of ${total.toLocaleString()}${selected?.filtered ? ' matches' : ''}` : '';
  }
  function renderMessages() {
    disposeMedia(); const run = renderRun;
    $('title').textContent = title(selected); $('number').textContent = selected.numbers.join(', ');
    const fragment = document.createDocumentFragment(), media = [];
    if (selected.contact) {
      fragment.append(node('p', title(selected), 'bv-empty'));
      const matching = threads.filter(t => t.numbers.some(n => key(n) === key(selected.numbers[0])));
      for (const t of matching) {const b = node('button', 'Read conversation: ' + title(t), 'bv-button'); b.onclick = () => {mode = 'messages'; setTabs(); $('search').value = ''; selected = t; search();}; fragment.append(b);}
      if (!matching.length) fragment.append(node('p', 'No messages with this number in the loaded backup.', 'bv-empty'));
    }
    for (const id of selected.ids.slice(messagePage * PAGE, (messagePage + 1) * PAGE)) {
      const m = messages[id], bubble = node('article', null, 'bv-bubble ' + (m.direction === 'out' ? 'bv-out' : 'bv-in'));
      bubble.append(node('small', m.direction === 'out' ? 'You · ' + m.type.toUpperCase() : (contacts.get(key(m.address))?.name || m.address || 'Unknown sender') + ' · ' + m.type.toUpperCase()));
      const text = body(m); if (text) {const p = node('p', text); p.dir = 'auto'; bubble.append(p);}
      for (const part of m.parts || []) {
        if (!api.hasAttach(part)) continue;
        const holder = node('div', null, 'bv-attachment');
        const raster = /^image\/(jpeg|jpg|png|gif|webp|bmp|avif)$/i.test(part.ct || '');
        const size = part._dataSource?.length * .75 || part._entry?.uncompressedSize || part.data?.byteLength || part._dataBlob?.size || 0;
        const button = node('button', raster ? 'Load image' : 'Download ' + (part.cl || part.ct || 'attachment'));
        holder.append(button); bubble.append(holder);
        let busy = false, loaded = false, visible = true, mediaRun = 0, mediaUrl;
        const show = async () => {
          if (busy || loaded || !visible || run !== renderRun) return;
          const request = ++mediaRun;
          busy = true; button.disabled = true; button.textContent = 'Loading attachment…';
          try {
            const data = await api.readAttachment(part);
            if (run !== renderRun || request !== mediaRun || !visible) return;
            if (!data) throw new Error('Attachment is missing or unreadable');
            const url = URL.createObjectURL(new Blob([data], {type: part.ct || 'application/octet-stream'})); urls.push(url); mediaUrl = url;
            if (raster) {
              const img = node('img'); img.alt = part.cl || 'MMS image'; img.decoding = 'async';
              img.onload = () => {if (run === renderRun && request === mediaRun) button.hidden = true;};
              img.onerror = () => {if (run === renderRun && request === mediaRun) {img.remove(); button.textContent = 'Image could not be displayed';}};
              img.src = url; holder.append(img); loaded = true;
            } else {const a = node('a', 'Download attachment'); a.href = url; a.download = String(part.cl || 'attachment').replace(/[\\/\x00-\x1f]/g, '_'); holder.replaceChildren(a); a.click(); loaded = true;}
          } catch (e) {if (run === renderRun) button.textContent = 'Could not load attachment. Retry';}
          finally {busy = false; if (run === renderRun) {button.disabled = loaded; if (visible && request !== mediaRun) show();}}
        };
        button.onclick = show;
        if (raster && size <= 20 * 1024 * 1024) media.push({holder, show, visibility(value) {
          visible = value;
          if (!value) {
            if (holder.querySelector('img')) holder.style.minHeight = holder.getBoundingClientRect().height + 'px';
            mediaRun++; holder.querySelector('img')?.remove();
            if (mediaUrl) {URL.revokeObjectURL(mediaUrl); urls = urls.filter(u => u !== mediaUrl); mediaUrl = null;}
            loaded = false; button.hidden = false; button.disabled = false; button.textContent = 'Load image';
          }
        }});
        else if (raster) button.textContent = 'Load large image (' + Math.ceil(size / 1048576) + ' MB)';
      }
      const stamp = date(m), time = node('time', stamp && Number.isFinite(new Date(stamp).getTime()) ? new Date(stamp).toLocaleString() : 'Unknown timestamp');
      if (stamp && Number.isFinite(new Date(stamp).getTime())) time.dateTime = new Date(stamp).toISOString();
      bubble.append(time); fragment.append(bubble);
    }
    $('messages').replaceChildren(fragment); $('messages').scrollTop = 0;
    updateMessagePager(selected.ids.length);
    // A bounded queue prevents an image-rich page from decoding all pictures together.
    const queue = []; let active = 0;
    const pump = () => {while (active < 2 && queue.length && run === renderRun) {active++; queue.shift()().finally(() => {active--; pump();});}};
    const jobs = new Map(media.map(m => [m.holder, m]));
    observer = new IntersectionObserver(entries => {for (const entry of entries) {const job = jobs.get(entry.target); job.visibility(entry.isIntersecting); if (entry.isIntersecting) queue.push(job.show);} pump();}, {root: $('messages'), rootMargin: '100px'});
    media.forEach(m => observer.observe(m.holder));
  }
  function setTabs() { $('messages-tab').setAttribute('aria-pressed', String(mode === 'messages')); $('contacts-tab').setAttribute('aria-pressed', String(mode === 'contacts')); }
  $('messages-tab').onclick = () => {mode = 'messages'; setTabs(); search();};
  $('contacts-tab').onclick = () => {mode = 'contacts'; setTabs(); search();};
  $('search').oninput = () => {searchRun++; clearTimeout(debounce); debounce = setTimeout(search, 180);};
  $('list-prev').onclick = () => {listPage--; renderList(); $('list').scrollTop = 0;};
  $('list-next').onclick = () => {listPage++; renderList(); $('list').scrollTop = 0;};
  $('older').onclick = () => {messagePage--; renderMessages();};
  $('newer').onclick = () => {messagePage++; renderMessages();};
  $('backup').onchange = () => {const file = $('backup').files[0]; if (file) {if (api.open(file)) {$('status').textContent = 'Scanning backup… Progress and cancellation are available below.';} else $('status').textContent = 'Wait for the current scan or conversion to finish.';}};
  $('cancel').onclick = () => {if(api.cancel()){$('status').textContent='Cancelling?';$('cancel').disabled=true;}};
  $('clear').onclick = () => {if (api.close()) reset(true); else $('status').textContent = 'Cancel the current scan or conversion before closing files.';};
  $('vcard').onchange = async () => {
    const files = [...$('vcard').files], run = loadRun;
    try {
      const pending = [];
      for (const file of files) {
        if (file.size > 20 * 1024 * 1024) throw new Error('Contacts files are limited to 20 MB. Split the contacts export into smaller files.');
        for (const contact of parseVcards(await file.text())) pending.push(contact);
      }
      if (run !== loadRun) return;
      if (!pending.length) throw new Error('No contacts with phone numbers found. Use a vCard 3.0 or 4.0 export.');
      for (const c of pending) {imported.set(key(c.number), c); contacts.set(key(c.number), c);}
      if (!messages.length) {mode = 'contacts'; setTabs();}
      await search();
    } catch (e) {if (run === loadRun) $('status').textContent = e.message;}
    finally {$('vcard').value = '';}
  };
  function parseVcards(text) {
    const result = []; let card = null;
    const unescape = s => s.replace(/\\([nN,;\\])/g, (_, c) => /n/i.test(c) ? '\n' : c);
    for (const line of text.replace(/\r\n/g, '\n').replace(/\n[ \t]/g, '').split('\n')) {
      if (/^BEGIN:VCARD$/i.test(line.trim())) {card = {name: '', fallback: '', numbers: []}; continue;}
      if (!card) continue;
      if (/^END:VCARD$/i.test(line.trim())) {for (const number of card.numbers) result.push({name: card.name || card.fallback || number, number}); card = null; continue;}
      const colon = line.indexOf(':'); if (colon < 0) continue;
      const header = line.slice(0, colon), property = header.split(';')[0].split('.').pop().toUpperCase();
      const value = unescape(line.slice(colon + 1)).trim();
      if (property === 'VERSION' && !['3.0', '4.0'].includes(value)) throw new Error('Please export contacts as vCard 3.0 or 4.0.');
      if (/ENCODING=/i.test(header)) throw new Error('Encoded vCard 2.1 contacts are not supported. Export as UTF-8 vCard 3.0 or 4.0.');
      if (property === 'FN') card.name = value;
      if (property === 'N') card.fallback = value.split(';').filter(Boolean).reverse().join(' ');
      if (property === 'TEL') {const number = value.replace(/^tel:/i, ''); if (number) card.numbers.push(number);}
    }
    if (card) throw new Error('Incomplete vCard: missing END:VCARD.');
    return result;
  }
  window.backupViewer = {load, reset,
    progress(message,percent){if($('progress').hidden)previousStatus=$('status').textContent;progressMessage=message;$('status').textContent=message;$('progress').hidden=false;$('progress-bar').value=percent;$('cancel').disabled=false;},
    finish(){if($('status').textContent===progressMessage)$('status').textContent=previousStatus;$('progress').hidden=true;},
    failed(message){$('status').textContent=message;}
  };
  reset();
})();
