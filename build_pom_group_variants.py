import json, os, struct, zlib

# Five isolated group-MMS variants (one per thread, disjoint numbers) to learn
# Fig's threading rule. Each message's text says which variant it is.
# All dated today June 11 2026, 10:30-10:38 AM EDT.

TOK = "insert-address-token"
T0 = 1781188200  # 10:30 EDT

with open("test_red.png", "rb") as f: png = f.read()

SMIL_TXT = ('<smil><head><layout><root-layout/><region id="Text" top="0" left="0" height="100%" '
            'width="100%"/></layout></head><body><par dur="5000ms"><text src="text.000000.txt" '
            'region="Text" /></par></body></smil>')
def smil_img(src):
    return ('<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" '
            f'height="100%" width="100%"/></layout></head><body><par dur="5000ms"><img src="{src}" '
            'region="Image" /></par></body></smil>')

lines, part_files = [], []
ids = {"part": 300000, "addr": 400000}
def nid(k):
    ids[k] += 1; return str(ids[k])

def addr(mid, address, typ):
    return {"_id": nid("addr"), "msg_id": mid, "address": address, "type": typ, "charset": "106"}

def variant(mid, tid, date_s, direction, sender, recipients, label, with_image):
    parts = []
    if with_image:
        pn = f"PART_17811882{mid}01"
        part_files.append((f"data/{pn}", png))
        parts.append({"_id": nid("part"), "mid": mid, "seq": "-1", "ct": "application/smil",
                      "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml", "text": smil_img("v.png")})
        parts.append({"_id": nid("part"), "mid": mid, "seq": "0", "ct": "image/png", "name": "v.png",
                      "cid": "<v.png>", "cl": "v.png",
                      "_data": f"/data/user_de/0/com.android.providers.telephony/app_parts/{pn}"})
        parts.append({"_id": nid("part"), "mid": mid, "seq": "1", "ct": "text/plain",
                      "name": "text.000000.txt", "chset": "106", "cid": "<text.000000.txt>",
                      "cl": "text.000000.txt", "text": label})
    else:
        parts.append({"_id": nid("part"), "mid": mid, "seq": "-1", "ct": "application/smil",
                      "name": "smil.xml", "cid": "<smil>", "cl": "smil.xml", "text": SMIL_TXT})
        parts.append({"_id": nid("part"), "mid": mid, "seq": "0", "ct": "text/plain",
                      "name": "text.000000.txt", "chset": "106", "cid": "<text.000000.txt>",
                      "cl": "text.000000.txt", "text": label})
    obj = {
        "_id": mid, "thread_id": tid, "date": str(date_s), "date_sent": "0",
        "msg_box": "1" if direction == "in" else "2", "read": "1", "m_id": "",
        "ct_t": "application/vnd.wap.multipart.related", "m_cls": "personal",
        "m_type": "132" if direction == "in" else "128", "v": "18", "pri": "129", "rr": "129",
        "tr_id": "", "d_rpt": "129", "locked": "0", "sub_id": "1", "seen": "1",
        "creator": "com.pomphone.messaging",
        "text_only": "0" if with_image else "1",
        "__sender_address": addr(mid, sender, "137"),
        "__recipient_addresses": [addr(mid, r, "151") for r in recipients],
        "__parts": parts}
    lines.append(json.dumps(obj))

N = lambda x: f"+1212444{x}"

variant("11", "10", T0,     "in",  N(1110), [TOK, N(1111)],          "V1: incoming TEXT, token + 1111", False)
variant("12", "20", T0+120, "in",  N(1112), [TOK, N(1113)],          "V2: incoming PICTURE, token + 1113", True)
variant("13", "30", T0+240, "in",  N(1114), [N(1115), N(1116)],      "V3: incoming TEXT, no token, 1115 + 1116", False)
variant("14", "40", T0+360, "in",  N(1117), [N(1118), N(1119)],      "V4: incoming PICTURE, no token, 1118 + 1119", True)
variant("15", "50", T0+480, "out", TOK,     [N(1120), N(1121)],      "V5: OUTGOING TEXT to 1120 + 1121", False)

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

out = "pom_group_variants.zip"
with open(out, "wb") as f:
    f.write(streaming_entry("messages.ndjson", ndjson))
    for zname, data in part_files:
        f.write(streaming_entry(zname, data))

print(f"Created {out}: {os.path.getsize(out)} bytes — {len(lines)} MMS variants, {len(part_files)} attachments")
