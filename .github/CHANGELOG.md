# Full change log

Every change, including small ones left out of the release notes.

## v1.1.15 (2026-11-04)
- Keyphone is public: read .kpb backups and convert to Keyphone, on the normal page (was beta only).
- Keyphone added to the "What's supported" table, the README table, the chart picture (assets/chart.svg), the top of the page and the Google description.
- FAQ: new question "I restored my messages on a Wonder, but I don't see them" (clear the Messages app's storage).
- FAQ: "What if my phone isn't listed?" now points to the file description option instead of Contact Us.

### v1.1.15 quiet update (2026-11-04, no version change)
- Group chats from Keyphone backups stay correct when converting to other phones. Keyphone leaves the phone's own number out, and the converter used to guess a group member as "you". Now it only guesses when the number is on most incoming picture messages and never writes to you; otherwise it leaves your number out. Fig, Wonder and other backups that include the number are unchanged.
- Wonder files: when your own number isn't known, sent picture messages use Android's standard placeholder instead of an empty sender.
- Big Keyphone files: "Finishing Keyphone file…" now shows a percentage, and the bar no longer jumps back at the end.

## v1.1.14 (2026-11-04)
- Converting to Wonder makes a file in Wonder's own backup format.
- Fig backups can be converted to Wonder (no more "no conversion needed").
- Wonder restore steps shown after converting, not when Wonder is selected.
- Unsupported phones: one "Send file description" button, with email and phone model required, and the file shown on the page. Anonymizer button removed.
- README: Wonder restore note, file description privacy note.

## (no version) 2026-11-04
- Fig IV option removed from beta. Fig IV backups are read as Fig.

## v1.1.13 (2026-11-03)
- Better file descriptions. Keyphone on beta.

## v1.1.12 (2026-11-02)
- Pick any backup file, no questions asked.

## v1.1.11 (2026-11-02)
- File description for unsupported phones.

## v1.1.10 (2026-11-02)
- Unsupported backups show the right screen.

## v1.1.9 (2026-11-02)
- Safer, organized anonymized copies.

## v1.1.8 (2026-11-01)
- Fig all-in-one backups open for everyone.

## (no version) 2026-10-28
- Plainer wording: no long dashes.

## v1.1.7 (2026-10-25)
- How to restore on a Fig.

## v1.1.6 (2026-10-22)
- Pom works for everyone, with pictures and voice notes.

## v1.1.5 (2026-10-21)
- Preview messages before converting.

## v1.1.4 (2026-10-21)
- Remove control characters from XML output.

## v1.1.3 (2026-10-20)
- Top bar stays on screen, with links.

## v1.1.2 (2026-10-20)
- Better logs, sent with an explanation.

## v1.1.1 (2026-10-20)
- Clearer wording at the top of the page.

## v1.1.0 (2026-10-20)
- New black and white dark mode.

## v1.0.0 (2026-10-20)
- New dark mode.

Older versions: see the commit history.
