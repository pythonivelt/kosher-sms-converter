# Kosher Phone SMS Converter

Move your text messages and picture messages from one kosher phone to another — even when the two phones save their backups in completely different formats.

**[Open the converter →](https://pythonivelt.github.io/kosher-sms-converter/)**

Free, nothing to install, and your messages never leave your device.

## Supported phones and apps

| Phone / App | Can read its backup | Can make a file it imports |
|-------|:---:|:---:|
| SMS Backup & Restore App * | ✅ SMS + MMS | ✅ SMS + MMS |
| Buggy Backup App | ✅ SMS only | ❌ Not in plan as of now |
| Fig | ✅ SMS + MMS | ✅ SMS + MMS |
| Wonder | ✅ SMS + MMS | ✅ SMS + MMS |
| Pom | ✅ SMS only | ❌ Not yet |
| TAK | ✅ SMS + MMS | ✅ SMS + MMS |

\* SMS Backup & Restore is an app that works on any regular Android phone and on some kosher phones.

## How to use it

1. **Back up** the messages on your old phone.
2. **Open the converter** — on a computer is best, especially for big backups. A phone's browser works too.
3. **Choose your backup file** (ZIP or XML). The converter shows what's inside: how many messages, pictures and group chats.
4. **Pick the phone or app you're moving to**, and what you want to keep.
5. **Click Convert**, save the new file, and restore it on your new phone.

## What it can do

- **Pictures and voice notes come along** — photos, voice notes, videos and other MMS attachments are converted together with the texts.
- **Keep only what you want** — everything, text messages only, or MMS only. You can also leave out group chats or PDF files.
- **Clean up a backup without converting it** — remove pictures or keep only some messages, and get a file in the same format back.
- **Handles very big backups** — opens backups of 2 GB and more, and saves very big conversions in parts (see below).

## Very big backups

Backups with lots of pictures can be several gigabytes. Browsers can't reliably save one file that big, so when the converted backup is larger than about 500 MB, the converter saves it as several smaller files, named `…-part1`, `…-part2`, and so on.

- The parts download one after another, automatically, with a short pause in between and a "time left" estimate. Keep the page open until it says all parts are saved.
- Messages are never cut in half, and each chat stays in one file whenever possible.
- **To restore:** copy all the parts to your phone, restore part 1, then part 2, and continue in order. Once every part is restored, all your messages and chats are complete.
- If one part doesn't download, a "Download it again" link saves that same part again — you never have to start over.
- Use a computer for big backups. Phones usually can't save files this big.

## Privacy

Everything happens inside your browser. Your backup file, your messages, phone numbers, contact names and pictures are never uploaded anywhere.

To know the converter is working, it sends an anonymous summary of each conversion — totals like how many messages were converted, how big the file was and whether it worked. It never includes the content of any message.

## Questions or problems?

Found a bug, or have a phone the converter doesn't support yet? Write to **pythonivelt@gmail.com** (email or Google Chat), or use the **Contact** link at the bottom of the converter page.

## Open source

The whole converter is one HTML file — [`index.html`](index.html) — so anyone can check exactly what it does.
