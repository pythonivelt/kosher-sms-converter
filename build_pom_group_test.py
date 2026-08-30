import json, os, struct, zlib

# Single group-MMS test in POM format, dated June 11 2026 10:00 AM New York (14:00 UTC)
# 1781186400 = 2026-06-11 14:00:00 UTC

ME = "+12125550000"
A = "+12124441100"
B = "+12124441101"
DATE_S = 1781186400

with open("photo_2026-04-25_21-57-23.jpg", "rb") as f:
    jpg = f.read()

smil = ('<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" '
        'height="100%" width="100%"/></layout></head><body><par dur="5000ms">'
        '<img src="group.jpg" region="Image" /></par></body></smil>')

part_name = "PART_1781186400001"
msg = {
    "_id": "1", "thread_id": "1", "date": str(DATE_S), "date_sent": "0",
    "msg_box": "1", "read": "1", "m_id": "", "ct_t": "application/vnd.wap.multipart.related",
    "m_cls": "personal", "m_type": "132", "v": "18", "pri": "129", "rr": "129",
    "tr_id": "", "d_rpt": "129", "locked": "0", "sub_id": "1", "seen": "1",
    "creator": "com.pomphone.messaging", "text_only": "0",
    "__display_name": "Test Contact A",
    "__sender_address": {"_id": "100001", "msg_id": "1", "address": A, "type": "137",
                          "charset": "106", "__display_name": "Test Contact A"},
    "__recipient_addresses": [
        {"_id": "100002", "msg_id": "1", "address": ME, "type": "151", "charset": "106"},
        {"_id": "100003", "msg_id": "1", "address": B, "type": "151", "charset": "106",
         "__display_name": "Test Contact B"}
    ],
    "__parts": [
        {"_id": "200001", "mid": "1", "seq": "-1", "ct": "application/smil",
         "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml", "text": smil},
        {"_id": "200002", "mid": "1", "seq": "0", "ct": "image/jpeg",
         "name": "group.jpg", "cid": "<group.jpg>", "cl": "group.jpg",
         "_data": f"/data/user_de/0/com.android.providers.telephony/app_parts/{part_name}"}
    ]
}

ndjson = (json.dumps(msg) + "\n").encode("utf-8")

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

out = "pom_group_test.zip"
with open(out, "wb") as f:
    f.write(streaming_entry("messages.ndjson", ndjson))
    f.write(streaming_entry(f"data/{part_name}", jpg))

print(f"Created {out}: {os.path.getsize(out)} bytes — 1 group MMS dated {DATE_S} (2026-06-11 10:00 EDT)")
