'use strict';
const frame = document.getElementById('app'), result = document.getElementById('result');
const wait = async (test, label) => {const start = Date.now(); while (!test()) {if (Date.now() - start > 60000) throw Error('Timeout: ' + label); await new Promise(r => setTimeout(r, 20));}};
const assert = (ok, label) => {if (!ok) throw Error(label); result.textContent += '\nPASS ' + label;};
const png = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
const xml = `<smses><sms address="2125550100" date="1700000000000" type="1" body="Hello &amp;lt;img&amp;gt; שלום" contact_name="Alice"/>
<sms address="+12125550100" date="1700000001000" type="2" body="Reply needle" contact_name="Alice"/>
<mms address="2125550100" date="1700000002" msg_box="1" contact_name="Alice"><parts><part ct="text/plain" text="Photo > today"/><part ct="image/png" cl="pixel.png" data="${png}"/></parts><addrs><addr address="2125550100" type="137"/><addr address="2125550199" type="151"/></addrs></mms>
<sms address="2125550101" date="1700000003000" type="1" body="Second thread" contact_name="Bob"/></smses>`;
async function open(w, file, count) {
  if (!w.BackupConverter.open(file)) throw Error('Converter busy');
  await wait(() => w.document.getElementById('bv-status').textContent.startsWith(count.toLocaleString() + ' messages ·'), 'scan ' + file.name);
  await wait(() => w.document.getElementById('themeToggle').style.pointerEvents !== 'none', 'scan completion');
}
async function run(stress) {
  document.querySelectorAll('button').forEach(b => b.disabled = true);
  result.textContent = 'Running…';
  try {
    const w = frame.contentWindow, d = w.document, $ = id => d.getElementById(id);
    $('tab-messages').click();
    assert(!$('backupViewer').hidden && $('converter').hidden && $('aboutPanel').hidden, 'Messages is a separate workspace');
    $('tab-converter').click();
    assert($('backupViewer').hidden && !$('converter').hidden, 'Converter tab switches workspace');
    $('tab-about').click();
    assert(!$('aboutPanel').hidden && $('converter').hidden, 'About content stays out of the working views');
    $('tab-messages').click();
    let external = 0; w.fetch = () => {external++; return Promise.reject(Error('Network forbidden in viewer tests'));};
    if (stress) {
      const rows = ['<smses>'];
      for (let i = 0; i < 100000; i++) rows.push(`<sms address="${2125550100 + i % 100}" date="${1700000000000 + i}" type="${i % 2 + 1}" body="${i === 123 ? 'unique-needle' : 'message ' + i}"/>`);
      rows.push('</smses>');
      const start = performance.now();
      await open(w, new w.File(rows, 'large.xml'), 100000);
      assert(d.querySelectorAll('.bv-conversation').length <= 60 && d.querySelectorAll('.bv-bubble').length <= 60, 'bounded DOM for 100,000 messages');
      $('bv-older').click(); assert(d.querySelectorAll('.bv-bubble').length === 60, 'older message page');
      $('bv-newer').click(); assert(d.querySelectorAll('.bv-bubble').length === 40, 'newer message page');
      $('bv-list-next').click(); assert(d.querySelectorAll('.bv-conversation').length === 40, 'next conversation page');
      $('bv-list-prev').click(); assert(d.querySelectorAll('.bv-conversation').length === 60, 'previous conversation page');
      $('bv-search').value = 'unique-needle'; $('bv-search').dispatchEvent(new w.Event('input'));
      await wait(() => $('bv-page').textContent === '1–1 of 1 matches', 'large search');
      assert($('bv-messages').textContent.includes('unique-needle'), 'search finds message outside rendered page');
      result.textContent += '\nImport + search: ' + ((performance.now() - start) / 1000).toFixed(2) + ' seconds';
    } else {
      await open(w, new w.File([xml], 'sample.xml'), 4);
      assert(d.querySelectorAll('.bv-conversation').length === 2, 'phone normalization groups SMS and MMS');
      $('tab-converter').click(); $('tab-messages').click();
      assert(d.querySelectorAll('.bv-conversation').length === 2, 'switching tabs preserves loaded backup');
      [...d.querySelectorAll('.bv-conversation')].find(b => b.textContent.includes('Alice')).click();
      assert(d.querySelectorAll('.bv-in').length === 2 && d.querySelectorAll('.bv-out').length === 1, 'incoming and outgoing bubbles');
      assert($('bv-messages').textContent.includes('Hello &lt;img&gt; שלום'), 'Unicode and escaped text remain literal');
      await wait(() => [...d.querySelectorAll('.bv-attachment img')].some(i => i.complete && i.naturalWidth), 'inline XML image');
      assert(true, 'inline XML image decoded');
      $('bv-search').value = 'needle'; $('bv-search').dispatchEvent(new w.Event('input'));
      await wait(() => $('bv-page').textContent === '1–1 of 1 matches', 'message search');
      assert(d.querySelectorAll('.bv-bubble').length === 1, 'search filters messages');
      const dt = new w.DataTransfer();
      dt.items.add(new w.File(['BEGIN:VCARD\nVERSION:3.0\nFN:Alice Contact\nTEL:+1 (212) 555-0100\nEND:VCARD\nBEGIN:VCARD\nVERSION:4.0\nFN:Standalone Contact\nTEL;VALUE=uri:tel:+12125550102\nEND:VCARD'], 'contacts.vcf'));
      $('bv-vcard').files = dt.files; $('bv-vcard').dispatchEvent(new w.Event('change'));
      await wait(() => $('bv-status').textContent.includes('3 contact numbers'), 'contact import');
      $('bv-search').value = ''; $('bv-search').dispatchEvent(new w.Event('input')); $('bv-contacts-tab').click();
      await wait(() => $('bv-list').textContent.includes('Standalone Contact'), 'standalone contacts');
      assert($('bv-list').textContent.includes('Alice Contact'), 'vCard overrides embedded contact name');
      $('bv-messages-tab').click();
      // Regression: conversion still exports media after previews and filtered searches.
      $('tab-converter').click(); $('optFig').click(); $('optAll').click(); $('buildBtn').click();
      await wait(() => $('downloadBtn').style.display === 'block', 'converter export');
      const zip = w.zip;
      const exported = await (await window.fetch($('downloadBtn').href)).blob();
      const exportReader = new zip.ZipReader(new zip.BlobReader(exported));
      const exportedEntries = await exportReader.getEntries();
      const ndjson = await exportedEntries.find(e => e.filename.endsWith('.ndjson')).getData(new zip.TextWriter());
      const imageEntry = exportedEntries.find(e => e.filename.includes('PART_'));
      const exportedImage = new Uint8Array(await (await imageEntry.getData(new zip.BlobWriter())).arrayBuffer());
      assert(ndjson.trim().split('\n').length === 4 && btoa(String.fromCharCode(...exportedImage)) === png, 'converter preserves all messages and media after viewing');
      await exportReader.close();
      $('tab-messages').click();
      const zipFile = async (name, entries) => {const writer = new zip.ZipWriter(new zip.BlobWriter()); for (const [path, data] of entries) await writer.add(path, new zip.BlobReader(new w.Blob([data]))); return new w.File([await writer.close()], name);};
      const imageBytes = Uint8Array.from(atob(png), c => c.charCodeAt(0));
      const fig = [{type:1,address:'2125550100',body:'Fig SMS',date:'1700000000000'}, {m_type:132,msg_box:1,date:'1700000001',__sender_address:{address:'2125550100',type:137},__recipient_addresses:[{address:'2125550199',type:151}],__parts:[{ct:'image/png',cl:'pixel.png',_data:'data/PART_1'}]}];
      await open(w, await zipFile('fig.zip', [['messages.ndjson', fig.map(JSON.stringify).join('\n')], ['data/PART_1', imageBytes]]), 2);
      await wait(() => [...d.querySelectorAll('.bv-attachment img')].some(i => i.complete && i.naturalWidth), 'Fig ZIP image');
      assert(true, 'Fig/TAK final MMS record without newline and lazy ZIP image');
      await open(w, await zipFile('wonder.zip', [['messages.xml', xml.replace(`data="${png}"`, 'file="pixel.png"')], ['mms_attachments/pixel.png', imageBytes]]), 4);
      [...d.querySelectorAll('.bv-conversation')].find(b => b.textContent.includes('Alice')).click();
      await wait(() => [...d.querySelectorAll('.bv-attachment img')].some(i => i.complete && i.naturalWidth), 'Wonder ZIP image');
      assert(true, 'Wonder reuses streaming XML and ZIP attachments');
      await open(w, await zipFile('buggy.zip', [['conversations/conv_1', JSON.stringify({h:1,q:'2125550100',r:'Buggy SMS',m:1700000000000})]]), 1);
      assert($('bv-messages').textContent.includes('Buggy SMS'), 'Buggy format remains readable');
      $('bv-clear').click(); assert(!d.querySelector('.bv-bubble') && !$('bv-list').textContent, 'close clears messages and contacts');
    }
    assert(external === 0, 'no external fetches during import, viewing, search or conversion');
    result.textContent += '\nALL CHECKS PASSED';
  } catch (e) {result.textContent += '\nFAIL ' + e.stack;}
  finally {document.querySelectorAll('button').forEach(b => b.disabled = false);}
}
document.getElementById('smoke').onclick = () => run(false);
document.getElementById('stress').onclick = () => run(true);
