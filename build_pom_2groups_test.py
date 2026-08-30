import json, os, struct, zlib

# POM-format test, all dated today June 11 2026 ~10:00 AM EDT:
#   Group 1 (A + B + ME):   3 MMS — incoming picture, incoming text-only, outgoing text-only
#   Group 2 (C + A + D, NO own number): 2 MMS — incoming picture, outgoing picture
#   Plus 1-on-1 SMS controls with A and C
# Diagnostic: if only group 2 shows on Fig, the own-number recipient is what hides groups.

ME = "insert-address-token"  # what real Android phones store when they don't know their own number
A = "+12124441100"  # Test Contact A
B = "+12124441101"  # Test Contact B
C = "+12124441102"  # Test Contact C
D = "+12124441103"  # Test Contact D
T0 = 1781186400     # 2026-06-11 10:00:00 EDT, in seconds

with open("photo_2026-04-25_21-57-23.jpg", "rb") as f: jpg = f.read()
with open("test_red.png", "rb") as f: png = f.read()

def smil_img(src):
    return ('<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" '
            f'height="100%" width="100%"/></layout></head><body><par dur="5000ms"><img src="{src}" '
            'region="Image" /></par></body></smil>')
SMIL_TXT = ('<smil><head><layout><root-layout/><region id="Text" top="0" left="0" height="100%" '
            'width="100%"/></layout></head><body><par dur="5000ms"><text src="text.000000.txt" '
            'region="Text" /></par></body></smil>')

lines = []
part_files = []
ids = {"msg": 0, "part": 200000, "addr": 100000}

def nid(k):
    ids[k] += 1; return str(ids[k])

def sms(tid, addr, name, body, date_s, direction):
    lines.append(json.dumps({
        "_id": nid("msg"), "thread_id": tid, "address": addr, "date": str(date_s*1000),
        "date_sent": "0", "protocol": "0", "read": "1", "status": "-1",
        "type": "1" if direction == "in" else "2", "reply_path_present": "0", "body": body,
        "locked": "0", "sub_id": "1", "error_code": "-1", "creator": "com.pomphone.messaging",
        "seen": "1", "ipmsg_id": "0", "__display_name": name}))

def addr_obj(mid, address, typ, dname=None):
    o = {"_id": nid("addr"), "msg_id": mid, "address": address, "type": typ, "charset": "106"}
    if dname: o["__display_name"] = dname
    return o

def mms(tid, dname, date_s, direction, sender, recipients, kind, content=None, stamp=None):
    mid = nid("msg")
    parts = []
    if kind == "text":
        parts.append({"_id": nid("part"), "mid": mid, "seq": "-1", "ct": "application/smil",
                      "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml", "text": SMIL_TXT})
        parts.append({"_id": nid("part"), "mid": mid, "seq": "0", "ct": "text/plain",
                      "name": "text.000000.txt", "chset": "106", "cid": "<text.000000.txt>",
                      "cl": "text.000000.txt", "text": content})
    else:
        fname, data, ct = content
        parts.append({"_id": nid("part"), "mid": mid, "seq": "-1", "ct": "application/smil",
                      "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml", "text": smil_img(fname)})
        pn = f"PART_{stamp}"
        part_files.append((f"data/{pn}", data))
        parts.append({"_id": nid("part"), "mid": mid, "seq": "0", "ct": ct, "name": fname,
                      "cid": f"<{fname}>", "cl": fname,
                      "_data": f"/data/user_de/0/com.android.providers.telephony/app_parts/{pn}"})
    obj = {
        "_id": mid, "thread_id": tid, "date": str(date_s), "date_sent": "0",
        "msg_box": "1" if direction == "in" else "2", "read": "1", "m_id": "",
        "ct_t": "application/vnd.wap.multipart.related", "m_cls": "personal",
        "m_type": "132" if direction == "in" else "128", "v": "18", "pri": "129", "rr": "129",
        "tr_id": "", "d_rpt": "129", "locked": "0", "sub_id": "1", "seen": "1",
        "creator": "com.pomphone.messaging", "text_only": "1" if kind == "text" else "0",
        "__display_name": dname,
        "__sender_address": addr_obj(mid, sender[0], "137", sender[1]),
        "__recipient_addresses": [addr_obj(mid, r[0], "151", r[1]) for r in recipients],
        "__parts": parts}
    lines.append(json.dumps(obj))

# --- SMS first (sms-ie writes all SMS, then all MMS) ---
sms("2", A, "Test Contact A", "Control: single chat with A", T0+360, "in")
sms("2", A, "Test Contact A", "Control reply to A", T0+420, "out")
sms("3", C, "Test Contact C", "Control: single chat with C", T0+480, "in")
sms("3", C, "Test Contact C", "Control reply to C", T0+540, "out")

# --- Group 1: A + B + ME (own number among recipients — realistic) ---
mms("1", "Test Contact A", T0,     "in",  (A, "Test Contact A"), [(ME, None), (B, "Test Contact B")],
    "img", ("group1.jpg", jpg, "image/jpeg"), "1781186400001")
mms("1", "Test Contact B", T0+120, "in",  (B, "Test Contact B"), [(ME, None), (A, "Test Contact A")],
    "text", "Text reply inside group 1 (from B)")
mms("1", "Test Contact A", T0+240, "out", (ME, None), [(A, "Test Contact A"), (B, "Test Contact B")],
    "text", "Outgoing text in group 1")

# --- Group 2: C + A + D (NO own number anywhere in recipients) ---
mms("5", "Test Contact C", T0+600, "in",  (C, "Test Contact C"), [(A, "Test Contact A"), (D, "Test Contact D")],
    "img", ("group2.jpg", jpg, "image/jpeg"), "1781187000001")
mms("5", "Test Contact C", T0+720, "out", (ME, None), [(C, "Test Contact C"), (A, "Test Contact A"), (D, "Test Contact D")],
    "img", ("red.png", png, "image/png"), "1781187120001")

ndjson = ("\n".join(lines) + "\n").encode("utf-8")

def deflate_raw(data):
    c = zlib.compressobj(6, zlib.DEFLATED, -15)
    return c.compress(data) + c.flush()

def streaming_entry(name, data):
    nameb = name.encode("utf-8")
    comp = deflate_raw(data)
    crc = zlib.crc32(data) & 0xFFFFFFFF
    lfh = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0x0808, 8, 0, 0x5CB7, 0, 0, 0, len(nameb), 0)
    dd = struct.pack("<IIII", 0x08074B50, crc, len(comp), len(data))
    return lfh + nameb + comp + dd

out = "pom_2groups_test.zip"
with open(out, "wb") as f:
    f.write(streaming_entry("messages.ndjson", ndjson))
    for zname, data in part_files:
        f.write(streaming_entry(zname, data))

n_sms = sum(1 for l in lines if "m_type" not in json.loads(l))
print(f"Created {out}: {os.path.getsize(out)} bytes — {n_sms} SMS, {len(lines)-n_sms} MMS, {len(part_files)} attachments")
