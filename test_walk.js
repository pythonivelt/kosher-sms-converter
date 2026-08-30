// Verify the validated-data-descriptor walk against test_pom_backup.zip
// Mirrors walkZipEntries() in android-sms-converter.html
const fs = require('fs');
const zlib = require('zlib');

const buf = fs.readFileSync('test_pom_backup.zip');
const fileSize = buf.length;

function u32(pos) { return buf.readUInt32LE(pos); }

const entries = [];
let off = 0;
while (off <= fileSize - 30) {
  if (!(buf[off] === 0x50 && buf[off+1] === 0x4B && buf[off+2] === 0x03 && buf[off+3] === 0x04)) break;
  const method = buf.readUInt16LE(off+8);
  const flags = buf.readUInt16LE(off+6);
  const compSizeHdr = u32(off+18);
  const fnLen = buf.readUInt16LE(off+26);
  const exLen = buf.readUInt16LE(off+28);
  const name = buf.slice(off+30, off+30+fnLen).toString('utf8');
  const dataStart = off + 30 + fnLen + exLen;

  if (compSizeHdr > 0 || !(flags & 8)) {
    entries.push({name, method, dataStart, compSize: compSizeHdr});
    off = dataStart + compSizeHdr;
    if (flags & 8) {
      const sig = u32(off);
      if (sig === 0x08074B50) off += 16; else if (sig !== 0x04034B50) off += 12;
    }
    continue;
  }

  // Scan for validated descriptor (same candidate logic as the browser walk)
  let found = false;
  for (let p = dataStart; p <= fileSize - 4; p++) {
    if (buf[p] !== 0x50 || buf[p+1] !== 0x4B) continue;
    if (buf[p+2] === 0x07 && buf[p+3] === 0x08 && p + 16 <= fileSize) {
      const comp = u32(p+8);
      if (comp === p - dataStart) {
        entries.push({name, method, dataStart, compSize: comp});
        off = p + 16; found = true; break;
      }
    } else if (buf[p+2] === 0x03 && buf[p+3] === 0x04 && p - 12 >= dataStart) {
      const comp = u32(p-8);
      if (comp === p - 12 - dataStart) {
        entries.push({name, method, dataStart, compSize: comp});
        off = p; found = true; break;
      }
    }
  }
  if (!found) {
    // EOF checks (last entry)
    const sigPos = fileSize - 16;
    if (sigPos > dataStart && u32(sigPos) === 0x08074B50 && u32(fileSize-8) === sigPos - dataStart) {
      entries.push({name, method, dataStart, compSize: sigPos - dataStart});
    } else if (fileSize - 12 > dataStart && u32(fileSize-8) === fileSize - 12 - dataStart) {
      entries.push({name, method, dataStart, compSize: fileSize - 12 - dataStart});
    }
    break;
  }
}

console.log('Entries found:', entries.length);
let pass = true;
for (const e of entries) {
  const comp = buf.slice(e.dataStart, e.dataStart + e.compSize);
  try {
    const raw = zlib.inflateRawSync(comp);
    console.log(`  ${e.name}: comp=${e.compSize} -> uncomp=${raw.length} OK`);
    if (e.name === 'messages.ndjson') {
      const lines = raw.toString('utf8').trim().split('\n');
      console.log(`    NDJSON lines: ${lines.length} (expect 4)`);
      if (lines.length !== 4) pass = false;
      for (const l of lines) JSON.parse(l); // must all parse
    }
    if (e.name.includes('PART_1779591189810')) {
      const orig = fs.readFileSync('photo_2026-04-25_21-57-23.jpg');
      const match = Buffer.compare(raw, orig) === 0;
      console.log(`    JPG byte-match: ${match}`);
      if (!match) pass = false;
    }
    if (e.name.includes('PART_1779590339934')) {
      const orig = fs.readFileSync('test_red.png');
      const match = Buffer.compare(raw, orig) === 0;
      console.log(`    PNG byte-match: ${match}`);
      if (!match) pass = false;
    }
  } catch (err) {
    console.log(`  ${e.name}: DECOMPRESS FAILED — ${err.message}`);
    pass = false;
  }
}
if (entries.length !== 3) pass = false;
console.log(pass ? 'ALL TESTS PASS' : 'TESTS FAILED');
process.exit(pass ? 0 : 1);
