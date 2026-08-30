#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');
const readline = require('readline');

const inputZip = process.argv[2];
if (!inputZip) {
  console.log('Usage: node fig-to-sms.js "path/to/fig messages.zip" [output.xml]');
  process.exit(1);
}

const outputXml = process.argv[3] || inputZip.replace(/\.zip$/i, '') + '.xml';
const tmpDir = path.join(os.tmpdir(), 'fig-to-sms-' + Date.now());

function escapeXml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\r/g, '&#13;');
}

function formatReadableDate(ts) {
  const ms = parseInt(ts, 10);
  if (!ms || isNaN(ms)) return '';
  const d = new Date(ms < 1e12 ? ms * 1000 : ms);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', second: '2-digit',
    hour12: true
  });
}

function buildSmsElement(msg) {
  const contactName = msg.__display_name || '(Unknown)';
  const readable = formatReadableDate(msg.date);
  const address = (msg.address || '').replace(/\s/g, '');
  return `  <sms protocol="${escapeXml(msg.protocol ?? 0)}" address="${escapeXml(address)}" date="${escapeXml(msg.date)}" type="${escapeXml(msg.type)}" subject="null" body="${escapeXml(msg.body || '')}" toa="null" sc_toa="null" service_center="null" read="${escapeXml(msg.read ?? 0)}" status="${escapeXml(msg.status ?? -1)}" locked="${escapeXml(msg.locked ?? 0)}" date_sent="${escapeXml(msg.date_sent ?? msg.date)}" sub_id="${escapeXml(msg.sub_id ?? 1)}" readable_date="${escapeXml(readable)}" contact_name="${escapeXml(contactName)}" />`;
}

function buildMmsElement(msg, dataDir) {
  let address = '';
  let contactName = '(Unknown)';
  const isReceived = String(msg.msg_box) === '1';

  if (isReceived && msg.__sender_address) {
    address = (msg.__sender_address.address || '').replace(/\s/g, '');
    contactName = msg.__sender_address.__display_name || '(Unknown)';
  } else if (!isReceived && msg.__recipient_addresses && msg.__recipient_addresses.length > 0) {
    address = (msg.__recipient_addresses[0].address || '').replace(/\s/g, '');
    contactName = msg.__recipient_addresses[0].__display_name || '(Unknown)';
  }

  if (!address) return null;

  const dateMs = parseInt(msg.date, 10) < 1e12
    ? parseInt(msg.date, 10) * 1000
    : parseInt(msg.date, 10);
  const readable = formatReadableDate(msg.date);
  const msgBox = msg.msg_box || 1;

  const parts = msg.__parts || [];
  let hasNonText = false;
  const partLines = [];

  for (const p of parts) {
    if (p.ct === 'application/smil') continue;

    if (p._data) {
      const partName = p._data.split('/').pop();
      const partPath = path.join(dataDir, partName);
      if (fs.existsSync(partPath)) {
        const raw = fs.readFileSync(partPath);
        const b64 = raw.toString('base64');
        hasNonText = true;
        partLines.push(`      <part seq="${escapeXml(p.seq ?? 0)}" ct="${escapeXml(p.ct)}" name="${escapeXml(p.cl || 'attachment')}" chset="null" cd="null" fn="${escapeXml(p.cl || '')}" cid="${escapeXml(p.cid || '')}" cl="${escapeXml(p.cl || '')}" ctt_s="null" ctt_t="null" data="${b64}" />`);
      }
    } else if (p.text != null) {
      partLines.push(`      <part seq="${escapeXml(p.seq ?? 0)}" ct="text/plain" name="body" chset="106" cd="null" fn="null" cid="null" cl="null" ctt_s="null" ctt_t="null" text="${escapeXml(p.text)}" />`);
    }
  }

  if (partLines.length === 0) {
    partLines.push(`      <part seq="0" ct="text/plain" name="body" chset="106" cd="null" fn="null" cid="null" cl="null" ctt_s="null" ctt_t="null" text="" />`);
  }

  const allAddrs = [];
  if (msg.__sender_address) {
    allAddrs.push({ address: msg.__sender_address.address, type: msg.__sender_address.type || 137 });
  }
  if (msg.__recipient_addresses) {
    for (const r of msg.__recipient_addresses) {
      allAddrs.push({ address: r.address, type: r.type || 151 });
    }
  }
  if (allAddrs.length === 0) {
    allAddrs.push({ address: address, type: isReceived ? 137 : 151 });
  }

  const addrLines = allAddrs.map(a =>
    `      <addr address="${escapeXml((a.address || '').replace(/\s/g, ''))}" type="${a.type}" charset="106" />`
  );

  const textOnly = hasNonText ? 0 : 1;

  return `  <mms date="${dateMs}" rr="null" sub="" ct_t="${escapeXml(msg.ct_t || 'application/vnd.wap.multipart.related')}" read_status="null" seen="${escapeXml(msg.seen ?? 1)}" msg_box="${msgBox}" address="${escapeXml(address)}" sub_cs="null" resp_st="null" retr_st="null" d_tm="null" text_only="${textOnly}" exp="null" locked="${escapeXml(msg.locked ?? 0)}" m_id="${escapeXml(msg.m_id || '')}" st="null" retr_txt_cs="null" retr_txt="null" creator="${escapeXml(msg.creator || 'com.figmessenger')}" date_sent="${escapeXml(msg.date_sent ?? 0)}" read="${escapeXml(msg.read ?? 0)}" m_size="${escapeXml(msg.m_size ?? 0)}" rpt_a="null" ct_cls="null" pri="null" sub_id="${escapeXml(msg.sub_id ?? 1)}" tr_id="${escapeXml(msg.tr_id || '')}" resp_txt="null" ct_l="null" m_cls="${escapeXml(msg.m_cls || 'personal')}" d_rpt="null" v="${escapeXml(msg.v || 18)}" service_center="null" _id="${escapeXml(msg._id || '')}" m_type="${escapeXml(msg.m_type || 128)}" readable_date="${escapeXml(readable)}" contact_name="${escapeXml(contactName)}">
    <parts>
${partLines.join('\n')}
    </parts>
    <addrs>
${addrLines.join('\n')}
    </addrs>
  </mms>`;
}

async function main() {
  console.log(`Input:  ${inputZip}`);
  console.log(`Output: ${outputXml}`);
  console.log();

  // Extract zip
  console.log('Extracting zip…');
  fs.mkdirSync(tmpDir, { recursive: true });
  try {
    execSync(`unzip -o -q "${inputZip}" -d "${tmpDir}"`, { stdio: 'pipe', maxBuffer: 10 * 1024 * 1024 });
  } catch (e) {
    console.error('Failed to extract zip. Make sure unzip is installed.');
    process.exit(1);
  }

  const ndjsonPath = path.join(tmpDir, 'messages.ndjson');
  const dataDir = path.join(tmpDir, 'data');
  const hasDataDir = fs.existsSync(dataDir);

  if (!fs.existsSync(ndjsonPath)) {
    console.error('No messages.ndjson found in zip.');
    cleanup();
    process.exit(1);
  }

  // First pass: count messages
  console.log('Counting messages…');
  let totalMessages = 0;
  const countStream = readline.createInterface({ input: fs.createReadStream(ndjsonPath, 'utf8') });
  for await (const line of countStream) {
    if (line.trim()) totalMessages++;
  }
  console.log(`Found ${totalMessages.toLocaleString()} messages`);

  // Second pass: convert and write
  console.log('Converting…');
  const out = fs.createWriteStream(outputXml, 'utf8');

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

  out.write(`<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>\n`);
  out.write(`<!--File Created By Fig-to-SMS Converter on ${dateStr} ${timeStr}-->\n`);
  out.write(`<smses count="PLACEHOLDER" backup_date="${Date.now()}" type="full">\n`);

  let countIn = 0, countOut = 0, countMms = 0, countSkip = 0;
  let processed = 0;

  const rl = readline.createInterface({ input: fs.createReadStream(ndjsonPath, 'utf8') });

  for await (const rawLine of rl) {
    const line = rawLine.trim();
    if (!line) continue;

    let msg;
    try { msg = JSON.parse(line); } catch { countSkip++; processed++; continue; }

    const t = msg.type;
    let element = null;

    if (t === '1' || t === 1) {
      element = buildSmsElement(msg);
      countIn++;
    } else if (t === '2' || t === 2) {
      element = buildSmsElement(msg);
      countOut++;
    } else if (msg.m_type !== undefined || msg.__parts) {
      element = buildMmsElement(msg, hasDataDir ? dataDir : '');
      if (element) countMms++;
      else countSkip++;
    } else {
      countSkip++;
    }

    if (element) out.write(element + '\n');

    processed++;
    if (processed % 1000 === 0) {
      process.stdout.write(`\r  ${processed.toLocaleString()} / ${totalMessages.toLocaleString()} messages processed…`);
    }
  }

  out.write('</smses>\n');
  out.end();

  await new Promise(resolve => out.on('finish', resolve));

  // Fix the count placeholder
  const totalCount = countIn + countOut + countMms;
  const fd = fs.openSync(outputXml, 'r+');
  const header = Buffer.alloc(300);
  fs.readSync(fd, header, 0, 300, 0);
  const headerStr = header.toString('utf8');
  const placeholderPos = headerStr.indexOf('count="PLACEHOLDER"');
  if (placeholderPos !== -1) {
    const countStr = `count="${totalCount}"`.padEnd('count="PLACEHOLDER"'.length);
    fs.writeSync(fd, countStr, placeholderPos, 'utf8');
  }
  fs.closeSync(fd);

  process.stdout.write('\r' + ' '.repeat(60) + '\r');
  console.log('Done!\n');
  console.log(`  Received SMS:  ${countIn.toLocaleString()}`);
  console.log(`  Sent SMS:      ${countOut.toLocaleString()}`);
  console.log(`  MMS:           ${countMms.toLocaleString()}`);
  console.log(`  Skipped:       ${countSkip.toLocaleString()}`);
  console.log(`  Total:         ${totalCount.toLocaleString()}`);

  const stat = fs.statSync(outputXml);
  const sizeMb = (stat.size / 1024 / 1024).toFixed(1);
  console.log(`\n  Output size: ${sizeMb} MB`);
  console.log(`  Saved to: ${outputXml}`);

  cleanup();
}

function cleanup() {
  try {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  } catch {}
}

process.on('SIGINT', () => { cleanup(); process.exit(1); });
main().catch(err => { console.error(err); cleanup(); process.exit(1); });
