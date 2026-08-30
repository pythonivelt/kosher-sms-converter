import json, os, struct, zlib

# Full POM-format test backup: SMS + MMS (pictures + voice notes + group chat)
# Byte-accurate POM streaming ZIP: zeroed LFH sizes, flags 0x0808, signed data
# descriptors, NO central directory, NO EOCD (exactly like real POM exports).

ME = "+12125550000"
A = "+12124441100"   # Test Contact A
B = "+12124441101"   # Test Contact B

with open("photo_2026-04-25_21-57-23.jpg", "rb") as f:
    jpg = f.read()
with open("test_red.png", "rb") as f:
    png = f.read()

# Minimal valid AMR-NB voice note (~1.5s): header + 75 mode-7 frames
amr = b"#!AMR\n" + (bytes([0x3C]) + bytes(31)) * 75

def smil(src, tag):
    if tag == "img":
        return ('<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" '
                'height="100%" width="100%"/></layout></head><body><par dur="5000ms">'
                f'<img src="{src}" region="Image" /></par></body></smil>')
    return ('<smil><head><layout><root-layout/></layout></head><body><par dur="5000ms">'
            f'<audio src="{src}" /></par></body></smil>')

msgs = []
pid = [200000]
part_files = []  # (zip_name, bytes)

def sms(tid, addr, name, body, date_ms, direction):
    msgs.append(json.dumps({
        "_id": str(len(msgs)+1), "thread_id": tid, "address": addr,
        "date": str(date_ms), "date_sent": "0", "protocol": "0", "read": "1",
        "status": "-1", "type": "1" if direction == "in" else "2",
        "reply_path_present": "0", "body": body, "locked": "0", "sub_id": "1",
        "error_code": "-1", "creator": "com.pomphone.messaging", "seen": "1",
        "ipmsg_id": "0", "__display_name": name}))

def mms(tid, name, date_s, direction, sender, recipients, content_ct, content_name, data_bytes, part_stamp):
    pid[0] += 1
    smil_id = str(pid[0]); pid[0] += 1
    cont_id = str(pid[0])
    mid = str(len(msgs)+1)
    tag = "img" if content_ct.startswith("image/") else "audio"
    part_name = f"PART_{part_stamp}"
    part_files.append((f"data/{part_name}", data_bytes))
    obj = {
        "_id": mid, "thread_id": tid, "date": str(date_s), "date_sent": "0",
        "msg_box": "1" if direction == "in" else "2", "read": "1",
        "m_id": "", "ct_t": "application/vnd.wap.multipart.related", "m_cls": "personal",
        "m_type": "132" if direction == "in" else "128", "v": "18", "pri": "129",
        "rr": "129", "tr_id": "", "d_rpt": "129", "locked": "0", "sub_id": "1",
        "seen": "1", "creator": "com.pomphone.messaging", "text_only": "0",
        "__display_name": name,
        "__parts": [
            {"_id": smil_id, "mid": mid, "seq": "-1", "ct": "application/smil",
             "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml",
             "text": smil(content_name, tag)},
            {"_id": cont_id, "mid": mid, "seq": "0", "ct": content_ct,
             "name": content_name, "cid": f"<{content_name}>", "cl": content_name,
             "_data": f"/data/user_de/0/com.android.providers.telephony/app_parts/{part_name}"}
        ]
    }
    aid = [100000 + pid[0]]
    def addr_obj(address, typ, dname):
        aid[0] += 1
        o = {"_id": str(aid[0]), "msg_id": mid, "address": address, "type": typ, "charset": "106"}
        if dname: o["__display_name"] = dname
        return o
    if sender:
        obj["__sender_address"] = addr_obj(sender[0], "137", sender[1])
    if recipients:
        obj["__recipient_addresses"] = [addr_obj(r[0], "151", r[1]) for r in recipients]
    msgs.append(json.dumps(obj))

base = 1747000000000  # ms, May 2025-ish

# Thread 1 — Contact A: SMS both ways, incoming picture, outgoing voice note
sms("1", A, "Test Contact A", "Hi! POM test message (received)", base, "in")
sms("1", A, "Test Contact A", "Reply from the POM (sent)", base + 60000, "out")
mms("1", "Test Contact A", (base + 120000)//1000, "in",  (A, "Test Contact A"), [(ME, None)], "image/jpeg", "photo.jpg", jpg, "1747000001001")
mms("1", "Test Contact A", (base + 180000)//1000, "out", (ME, None), [(A, "Test Contact A")], "audio/amr", "voice.amr", amr, "1747000001002")

# Thread 2 — Contact B: SMS both ways, outgoing picture, incoming voice note
sms("2", B, "Test Contact B", "Second conversation test (received)", base + 240000, "in")
sms("2", B, "Test Contact B", "And the answer (sent)", base + 300000, "out")
mms("2", "Test Contact B", (base + 360000)//1000, "out", (ME, None), [(B, "Test Contact B")], "image/png", "shot.png", png, "1747000002001")
mms("2", "Test Contact B", (base + 420000)//1000, "in",  (B, "Test Contact B"), [(ME, None)], "audio/amr", "memo.amr", amr, "1747000002002")

# Thread 3 — group MMS from A to me + B, with picture (should become a group on Fig)
mms("3", "Test Contact A", (base + 480000)//1000, "in", (A, "Test Contact A"), [(ME, None), (B, "Test Contact B")], "image/jpeg", "group.jpg", jpg, "1747000003001")

ndjson = ("\n".join(msgs) + "\n").encode("utf-8")

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

out = "pom_test_sms_mms.zip"
with open(out, "wb") as f:
    f.write(streaming_entry("messages.ndjson", ndjson))
    for zname, data in part_files:
        f.write(streaming_entry(zname, data))

print(f"Created {out}: {os.path.getsize(out)} bytes — {sum(1 for m in msgs if 'm_type' not in json.loads(m))} SMS, "
      f"{sum(1 for m in msgs if 'm_type' in json.loads(m))} MMS, {len(part_files)} attachments")
