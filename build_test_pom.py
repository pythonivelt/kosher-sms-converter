import json, os, struct, zlib

# Build a TRUE replica of a POM streaming ZIP (Java ZipOutputStream, unfinalized):
# - local headers: flags=0x0808 (data descriptor + UTF-8), method=8, sizes ZEROED
# - after each entry's deflate data: signed data descriptor PK\x07\x08 + crc + csize + usize
# - NO central directory, NO EOCD (file just ends after the last descriptor)

img1_path = "photo_2026-04-25_21-57-23.jpg"
img2_path = "test_red.png"
with open(img1_path, "rb") as f:
    img1_data = f.read()
with open(img2_path, "rb") as f:
    img2_data = f.read()

messages = []
messages.append(json.dumps({"_id":"1","thread_id":"1","address":"+12124441100","date":"1714085843000","date_sent":"1714085840000","protocol":"0","read":"1","status":"-1","type":"1","reply_path_present":"0","body":"Hello from POM test","locked":"0","sub_id":"1","error_code":"-1","creator":"com.pomphone.messaging","seen":"1","ipmsg_id":"0","__display_name":"Test Contact"}))
messages.append(json.dumps({"_id":"2","thread_id":"1","address":"+12124441100","date":"1714085900000","date_sent":"0","protocol":"0","read":"1","status":"0","type":"2","reply_path_present":"0","body":"Reply from POM","locked":"0","sub_id":"1","error_code":"-1","creator":"com.pomphone.messaging","seen":"1","ipmsg_id":"0","__display_name":"Test Contact"}))

mms1_smil = '<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" height="100%" width="100%"/></layout></head><body><par dur="5000ms"><img src="photo.jpg" region="Image" /></par></body></smil>'
messages.append(json.dumps({
    "_id":"3","thread_id":"1","date":"1714086","date_sent":"0","msg_box":"1","read":"1",
    "m_id":"","ct_t":"application/vnd.wap.multipart.related","m_cls":"personal",
    "m_type":"132","v":"18","pri":"129","rr":"129","tr_id":"","d_rpt":"129",
    "locked":"0","sub_id":"1","seen":"1","creator":"com.pomphone.messaging","text_only":"0",
    "__display_name":"Test Contact",
    "__sender_address":{"_id":"100001","msg_id":"3","address":"+12124441100","type":"137","charset":"106","__display_name":"Test Contact"},
    "__parts":[
        {"_id":"200001","mid":"3","seq":"-1","ct":"application/smil","name":"smil.xml","cid":"<smil>","cl":"smil.xml","text":mms1_smil},
        {"_id":"200002","mid":"3","seq":"0","ct":"image/jpeg","name":"photo.jpg","cid":"<photo>","cl":"photo.jpg","_data":"/data/user_de/0/com.android.providers.telephony/app_parts/PART_1779591189810"}
    ]
}))
mms2_smil = '<smil><head><layout><root-layout/></layout></head><body><par dur="5000ms"><img src="shot.png"/></par></body></smil>'
messages.append(json.dumps({
    "_id":"4","thread_id":"1","date":"1714087","date_sent":"0","msg_box":"2","read":"1",
    "m_id":"","ct_t":"application/vnd.wap.multipart.related","m_cls":"personal",
    "m_type":"128","v":"18","pri":"129","rr":"129","tr_id":"","d_rpt":"129",
    "locked":"0","sub_id":"1","seen":"1","creator":"com.pomphone.messaging","text_only":"0",
    "__display_name":"Test Contact",
    "__recipient_addresses":[{"_id":"100003","msg_id":"4","address":"+12124441100","type":"151","charset":"106","__display_name":"Test Contact"}],
    "__parts":[
        {"_id":"200003","mid":"4","seq":"-1","ct":"application/smil","name":"smil.xml","cid":"<smil>","cl":"smil.xml","text":mms2_smil},
        {"_id":"200004","mid":"4","seq":"0","ct":"image/png","name":"shot.png","cid":"<shot>","cl":"shot.png","_data":"/data/user_de/0/com.android.providers.telephony/app_parts/PART_1779590339934"}
    ]
}))

ndjson_content = ("\n".join(messages) + "\n").encode("utf-8")

def deflate_raw(data):
    c = zlib.compressobj(6, zlib.DEFLATED, -15)  # raw deflate, like ZIP method 8
    return c.compress(data) + c.flush()

def streaming_entry(name, data):
    """Local header (zeroed sizes, flag 0x0808) + deflate data + signed data descriptor."""
    nameb = name.encode("utf-8")
    comp = deflate_raw(data)
    crc = zlib.crc32(data) & 0xFFFFFFFF
    lfh = struct.pack("<IHHHHHIIIHH",
        0x04034B50,  # signature
        20,          # version needed
        0x0808,      # flags: data descriptor + UTF-8 (Java ZipOutputStream style)
        8,           # method: deflate
        0, 0x5CB7,   # mod time/date (arbitrary, matches report vibe)
        0,           # crc (zeroed — in descriptor)
        0,           # comp size (zeroed)
        0,           # uncomp size (zeroed)
        len(nameb),
        0)           # extra len
    dd = struct.pack("<IIII", 0x08074B50, crc, len(comp), len(data))
    return lfh + nameb + comp + dd

out_path = "test_pom_backup.zip"
with open(out_path, "wb") as f:
    f.write(streaming_entry("messages.ndjson", ndjson_content))
    f.write(streaming_entry("data/PART_1779591189810", img1_data))
    f.write(streaming_entry("data/PART_1779590339934", img2_data))
    # No central directory, no EOCD — exactly like the POM file

print(f"Created {out_path}: {os.path.getsize(out_path)} bytes (streaming ZIP, signed DDs, no central directory)")
