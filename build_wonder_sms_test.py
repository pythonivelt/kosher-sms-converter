import zipfile, os, random

out_dir = r"C:\Users\Moishe Schnitzler\Downloads\wonder-sms-tests"
os.makedirs(out_dir, exist_ok=True)

today = "2026-06-04"
contacts = ["+12124441100", "+12124441101", "+12124441102"]

# Recent timestamps (last few days)
base_ts = 1780000000000  # recent

def make_sms_list(count_per_contact):
    msgs = []
    ts = base_ts
    for c in contacts:
        for i in range(count_per_contact):
            typ = "1" if i % 2 == 0 else "2"  # alternate in/out
            body = f"Test msg {i+1} to {c[-4:]}"
            msgs.append(f'  <sms address="{c}" body="{body}" date="{ts}" date_sent="0" type="{typ}" read="1" seen="1" />')
            ts += random.randint(30000, 120000)  # 30s-2min apart
    return msgs

def save_wonder(name, sms_lines):
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<messages sms_count="{len(sms_lines)}" mms_count="0">\n'
    xml += '\n'.join(sms_lines) + '\n'
    xml += '</messages>\n'
    path = os.path.join(out_dir, name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Messages_Backup_{today}.xml", xml)
    print(f"  {name}: {os.path.getsize(path)} bytes, {len(sms_lines)} messages")

# Test 1: 10 messages per contact = 30 total, recent dates
print("Test 1: 30 messages (10 per contact), recent dates")
save_wonder("wonder_sms_test1_recent.zip", make_sms_list(10))

# Test 2: 7 messages per contact = 21 total, dates from a month ago
print("Test 2: 21 messages, dates from a month ago")
base_ts_old = 1777500000000
msgs2 = []
ts = base_ts_old
for c in contacts:
    for i in range(7):
        typ = "1" if i % 2 == 0 else "2"
        body = f"Old msg {i+1} to {c[-4:]}"
        msgs2.append(f'  <sms address="{c}" body="{body}" date="{ts}" date_sent="0" type="{typ}" read="1" seen="1" />')
        ts += random.randint(60000, 300000)
save_wonder("wonder_sms_test2_older.zip", msgs2)

# Test 3: Mixed — some with date_sent filled in for outgoing
print("Test 3: 24 messages, outgoing has date_sent filled")
msgs3 = []
ts = base_ts
for c in contacts:
    for i in range(8):
        typ = "1" if i % 2 == 0 else "2"
        body = f"Mixed msg {i+1} to {c[-4:]}"
        ds = "0" if typ == "1" else str(ts - 1000)
        msgs3.append(f'  <sms address="{c}" body="{body}" date="{ts}" date_sent="{ds}" type="{typ}" read="1" seen="1" />')
        ts += random.randint(30000, 120000)
save_wonder("wonder_sms_test3_datesent.zip", msgs3)

print(f"\nDone! 3 test files in {out_dir}")
