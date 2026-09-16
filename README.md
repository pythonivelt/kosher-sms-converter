# Kosher Phone SMS Converter

Switching kosher phones? This tool converts your text messages (SMS) and picture messages (MMS) so they transfer between phones — even when the phones use completely different backup formats.

**[Open the converter](https://pythonivelt.github.io/kosher-sms-converter/)** — runs 100% in your browser, nothing gets uploaded.

## What works

| Phone / App | Read backup (out) | Import (in) |
|-------|:---:|:---:|
| SMS Backup & Restore App * | ✅ SMS + MMS | ✅ SMS + MMS |
| Buggy Backup App | ✅ SMS only | ❌ Not in plan as of now |
| Fig | ✅ SMS + MMS | ✅ SMS + MMS |
| Wonder | ✅ SMS + MMS | ✅ SMS + MMS |
| Pom | ✅ SMS only | ❌ Not yet |
| TAK | ✅ SMS + MMS | ✅ SMS + MMS |

\* SMS Backup & Restore is an app that works on any open Android phone and some kosher phones.

## How it works

1. Open the converter in your phone's browser (or on a computer)
2. Pick your backup file (ZIP or XML)
3. The converter scans it and shows you what's inside
4. Choose the phone you want to convert to
5. Download the converted file and import it on your new phone

## Key details

- **Large files** — handles 2+ GB backups by streaming, works even on low-end phones
- **MMS support** — pictures, voice notes, and other attachments all transfer
- **Privacy** — your messages never leave your device, everything runs locally in the browser
- **Filtering** — convert just SMS, just MMS, or everything; option to skip PDFs

## Local backup viewer

Download/extract the repository (keep its files together) and open **index.html**
in a current desktop browser. No server, account, installation, or internet
connection is needed. The ZIP dependency is included in `vendor/zip.js` with its
license. The historical HTML snapshots are unchanged and still use their original
dependencies; use `index.html` for the offline viewer.

In the **Messages** tab, choose **Open backup** for a supported ZIP/XML backup.
Conversations appear on the left, with incoming/outgoing SMS and MMS, timestamps,
and inline pictures on the right. Search matches message text, contact names, or
phone numbers across the entire loaded backup, including messages on other pages.
Name/number matches show the whole conversation; text matches show matching messages.
Use **Older/Newer** for message pages and **Previous/Next** for conversation pages.

**Add contacts** accepts UTF-8 vCard 3.0/4.0 `.vcf` files, including multiple phone
numbers, folded lines and escaped names. Imported names override names embedded in
the backup for display only. The **Contacts** tab also works without a message
backup. vCard 2.1/quoted-printable exports are not supported; re-export as 3.0/4.0.
Each contacts file is limited to 20 MB. Contacts are kept when replacing a message
backup; **Close files** releases both contacts and messages.

The **Converter** tab contains the existing converter, filtering, merge mode and
download controls. **About** contains the phone support table, instructions and FAQ.
Switching tabs preserves loaded backups and converter settings. Import progress
and cancellation are available in Messages without switching tabs.
Viewing/searching does not filter the converter's input or change
attachment descriptors. No backup contents are written to browser storage.
Automatic analytics are disabled. The existing, explicitly invoked support/contact
actions still require a connection; they are not part of viewing or conversion.

### Architecture and large backups

- `workspace.js` and `workspace.css` switch between Messages, Converter and About
  without recreating the shared UI. Tabs also support arrow keys, Home and End.
- `index.html` remains the owner of format detection, parsing, merge/filter rules
  and export. The viewer consumes its normalized messages through a small adapter.
- `viewer.js` and `viewer.css` provide the independent viewer interface. Lists and
  threads render at most 60 records per page. Indexing and search yield periodically
  to keep the interface responsive. Search does not create another permanent copy
  of all message bodies.
- `xml-attachments.js` indexes base64 byte ranges while streaming XML, including
  across UTF-8/chunk boundaries. XML media is read directly from the original Blob
  on demand. Wonder uses the same XML reader and lazy ZIP attachment descriptors;
  Fig/TAK/Pom and Buggy continue using the existing format readers and fallback.
- Inline raster images load near the visible part of the thread, two at a time,
  and release their URLs when offscreen or when changing pages. Images larger than
  20 MB require a click. Other attachments are available as downloads; HTML and SVG
  attachments are never inserted as active page content.
- Text and message metadata remain in memory, as in the converter. ZIP directory
  metadata and decompressed XML/NDJSON Blobs also consume browser resources.
  Performance depends on message count, attachment size and the device. This is a
  bounded-rendering viewer, not a disk-backed database. Existing Pom/Buggy format
  limitations still apply. Group membership uses the converter's own-number
  inference, so ambiguous backups may still need manual checking.

### Tests

With Node 20 or newer, run `node tests/parsers.cjs` from the repository root. This
uses the actual parser/exporter source and needs no npm install. It checks byte
offsets, single/double quotes, BOM/Unicode, chunk boundaries, large attachment
scanning, cancellation, incomplete media, XML export round trips, and Fig's last
MMS record without a trailing newline.

For browser checks, serve the directory locally (for example,
`python -m http.server 8000 --bind 127.0.0.1`), then open
`http://127.0.0.1:8000/tests/browser.html`. **Run checks** exercises generated XML,
Fig/TAK, Wonder and Buggy backups, inline images, contacts, literal text rendering,
search, converter exports after viewing, cleanup and absence of network fetches.
**Run 100,000-message check** verifies bounded rendering and search beyond the
visible page. All fixtures are fictional and generated by the tests.

## Electron desktop app (Windows x64)

Extract the entire `Kosher-SMS-0.1.0-Windows-x64.zip`, then double-click
`Kosher SMS.exe`. Keep the accompanying files and folders together. This is a
portable folder, not a single-file executable or an installer. Electron is
included, so end users do not need Node.js, Python, a server, or internet access.
This initial build is unsigned and does not install shortcuts or automatic updates.

The desktop app loads the same `index.html` and tabbed interface as the website.
Its renderer has no Node access or preload bridge; context isolation and sandboxing
are enabled. The browser session is non-persistent and remote network requests
inside the app are blocked. Explicit links to GitHub, Google Play and Google Drive
open in the system browser. The website's online support forms therefore cannot
send from inside the offline desktop app. Ordinary Electron/Windows profile files
may be created, but backup messages and contacts are not saved there.

To rebuild the portable ZIP, use Python 3.9+:

```sh
python scripts/package_windows.py
```

The script downloads the official runtime version pinned in `desktop/runtime.json`,
verifies its SHA-256, and packages an explicit list of application files using
Electron's `resources/app` layout. It excludes test fixtures, backups, source
history, dependencies and development tools. The finished ZIP and its checksum
are in `dist/`. The verified runtime is cached there for offline rebuilds. Updating
Electron requires updating both `package.json` and the runtime version/checksum.

For development, install Node.js, run `npm install`, then `npm start`. Run `npm test`
for parser and desktop-policy checks. `npx electron tests/electron-smoke.cjs` runs
a desktop startup/import/tab smoke test using fictional data and writes its result
under `dist/electron-smoke/`. It requires an environment that permits Electron's
normal Windows child-process and sandbox initialization. Do not disable Electron's
sandbox to work around restrictions in a build environment.

## Contact

Questions, problems, or a phone format we don't support yet? Reach out: **pythonivelt@gmail.com** — email or Google Chat, both work.
