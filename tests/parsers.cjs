/* Run with Node 20+: node tests/parsers.cjs. Exercises the actual converter source. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const zip = require('../vendor/zip.js/zip.min.js'); zip.configure({useWebWorkers: false});
const ctx = vm.createContext({Blob, TextDecoder, TextEncoder, Uint8Array, ArrayBuffer, ReadableStream, Response, CompressionStream, DecompressionStream,
  atob, btoa, zip, console, cancelled: false, showProgress() {}, log() {}, tick: async () => {}, formatSize: String});
ctx.window = ctx;
vm.runInContext(fs.readFileSync(path.join(root, 'xml-attachments.js'), 'utf8'), ctx);
const range = (a, b) => html.slice(html.indexOf(a), html.indexOf(b, html.indexOf(a)));
vm.runInContext(range('async function parseFigZip', '// ===== WRITERS =====') +
  range('function normNum', 'function extFromCt') +
  html.split('\n').filter(s => /^function (escXml|ab2b64|b642ab|fmtDate|extFromCt|hasAttach)\(/.test(s)).join('\n') +
  range('async function resolveData', 'function formatSize') +
  range('async function writeToSmsBackup', 'async function buildFigZip'), ctx);
const mms = (data, quote = '"', prefix = '') => `<smses>${prefix}<mms address="2125550100" date="1700000000" msg_box="1"><parts><part ct="text/plain" text="hello > world &amp;lt;b&amp;gt;"/><part ct="image/png" data=${quote}${data}${quote}/></parts></mms></smses>`;
function chunked(text, size) {
  const blob = new Blob([text]), bytes = new TextEncoder().encode(text);
  return {size: blob.size, slice: (...args) => blob.slice(...args), stream() {let i = 0; return new ReadableStream({pull(controller) {if (i === bytes.length) return controller.close(); controller.enqueue(bytes.slice(i, i + size)); i = Math.min(bytes.length, i + size);}});}};
}
(async () => {
  const payload = btoa('binary-image-content');
  for (const quote of ['"', "'"]) for (const size of [1, 2, 7, 31, 65536]) {
    const text = '\ufeff' + mms(payload, quote, '<sms address="1" date="1" type="1" body="שלום 😀 &amp;quot;"/>');
    const {messages} = await ctx.parseSmsBackupXmlStream(chunked(text, size));
    assert.equal(messages.length, 2);
    assert.equal(messages[0].body, 'שלום 😀 &quot;');
    assert.equal(messages[1].parts[0].text, 'hello > world &lt;b&gt;');
    const part = messages[1].parts[1];
    assert.ok(part._dataSource && !part.data && !part._dataBlob);
    assert.equal(Buffer.from(await ctx.resolveData(part)).toString(), 'binary-image-content');
  }
  console.log('PASS XML offsets, UTF-8/BOM, quote styles, entities and arbitrary chunk boundaries');
  const big = 'YQ=='.repeat(500000);
  let max = 0;
  for await (const c of ctx.BackupXml.chunks(chunked(mms(big), 4096))) max = Math.max(max, c.text.length);
  assert.ok(max < 1000, 'attachment data must not accumulate in parser output');
  console.log('PASS multi-megabyte attachment scan stays bounded');
  await assert.rejects(() => ctx.parseSmsBackupXmlStream(new Blob(['<smses><mms><part data="abc'])), /Incomplete XML/);
  await assert.rejects(() => ctx.parseSmsBackupXmlStream(new Blob(['<smses><mms date="1"><parts></parts>'])), /Incomplete XML/);
  ctx.cancelled = true;
  await assert.rejects(() => ctx.parseSmsBackupXmlStream(new Blob([mms(payload)])), e => e.cancelled);
  ctx.cancelled = false;
  console.log('PASS truncated attachment and cancellation');
  const original = (await ctx.parseSmsBackupXmlStream(new Blob([mms(payload)]))).messages;
  const output = await ctx.writeToSmsBackup(original);
  const roundtrip = (await ctx.parseSmsBackupXmlStream(output)).messages;
  assert.equal(Buffer.from(await ctx.resolveData(roundtrip[0].parts[1])).toString(), 'binary-image-content');
  assert.equal(roundtrip[0].parts[0].text, original[0].parts[0].text);
  console.log('PASS XML export round trip with lazy attachment');
  const rows = [{type:1,address:'1',date:'1',body:'SMS'}, {m_type:132,msg_box:1,date:'2',__sender_address:{address:'1'},__parts:[{ct:'text/plain',text:'last MMS'}]}];
  const entries = [{filename:'messages.ndjson',uncompressedSize:100,getData:async()=>new Blob([rows.map(JSON.stringify).join('\n')])}];
  const fig = await ctx.parseFigZip(entries);
  assert.equal(fig.messages.length, 2); assert.equal(fig.messages[1].parts[0].text, 'last MMS');
  console.log('PASS Fig/TAK final MMS without trailing newline');
  const fallback = {file:new Blob(['abc']), _needsFullScan:true};
  ctx.parsedData = {attachMap:{PART_1:fallback}};
  ctx._buildEntryIndex = async () => ({PART_1:{dataStart:0,method:0,compSize:3}});
  assert.equal(Buffer.from(await ctx.resolveData({_fallbackAttach:fallback})).toString(), 'abc');
  console.log('PASS deferred fallback ZIP attachment resolves through scanned backup map');
  console.log('ALL PARSER CHECKS PASSED');
})().catch(e => {console.error(e); process.exitCode = 1;});
