import zipfile, json, os

img_path = "photo_2026-04-25_21-57-23.jpg"
with open(img_path, "rb") as f:
    img_data = f.read()

out_dir = r"C:\Users\Moishe Schnitzler\Downloads\pom-test-zips"
os.makedirs(out_dir, exist_ok=True)

ts_ms = 1714085843000
ts_s = ts_ms // 1000
contact = "+12124441100"

def build_ndjson_zip(name, messages_json, attachments, compression=zipfile.ZIP_DEFLATED, creator="com.figmessenger"):
    """Build a Fig/Pom NDJSON ZIP."""
    path = os.path.join(out_dir, name)
    ndjson = "\n".join(json.dumps(m) for m in messages_json) + "\n"
    with zipfile.ZipFile(path, "w", compression) as zf:
        zf.writestr("messages.ndjson", ndjson)
        for fn, data in attachments.items():
            zf.writestr(fn, data)
    print(f"  {name}: {os.path.getsize(path)} bytes")

def sms(id, addr, body, date, typ, creator="com.figmessenger"):
    return {"_id":str(id),"thread_id":"1","address":addr,"date":str(date),"date_sent":"0","protocol":"0","read":"1","status":"-1","type":str(typ),"reply_path_present":"0","body":body,"locked":"0","sub_id":"1","error_code":"-1","creator":creator,"seen":"1","ipmsg_id":"0","__display_name":"Test Contact"}

def mms_in(id, addr, part_name, smil, date_val, creator="com.figmessenger", extra_parts=None, addr_id_start=100001, part_id_start=200001):
    """Incoming MMS"""
    obj = {"_id":str(id),"thread_id":"1","date":str(date_val),"date_sent":"0","msg_box":"1","read":"1",
        "m_id":"","ct_t":"application/vnd.wap.multipart.related","m_cls":"personal",
        "m_type":"132","v":"18","pri":"129","rr":"129","tr_id":"","d_rpt":"129",
        "locked":"0","sub_id":"1","seen":"1","creator":creator,"text_only":"0",
        "__display_name":"Test Contact",
        "__sender_address":{"_id":str(addr_id_start),"msg_id":str(id),"address":addr,"type":"137","charset":"106","__display_name":"Test Contact"},
        "__parts":[]}
    if smil:
        obj["__parts"].append({"_id":str(part_id_start),"mid":str(id),"seq":"-1","ct":"application/smil","name":"smil.xml","cid":"<smil>","cl":"smil.xml","text":smil})
    obj["__parts"].append({"_id":str(part_id_start+1),"mid":str(id),"seq":"0","ct":"image/jpeg","name":"image000000.jpg","cid":"<image000000>","cl":"image000000.jpg","_data":"/data/user_de/0/com.android.providers.telephony/app_parts/"+part_name})
    if extra_parts:
        for ep in extra_parts:
            obj["__parts"].append(ep)
    return obj

def mms_out(id, addr, part_name, smil, date_val, creator="com.figmessenger", addr_id_start=100003, part_id_start=200003):
    """Outgoing MMS"""
    obj = {"_id":str(id),"thread_id":"1","date":str(date_val),"date_sent":"0","msg_box":"2","read":"1",
        "m_id":"","ct_t":"application/vnd.wap.multipart.related","m_cls":"personal",
        "m_type":"128","v":"18","pri":"129","rr":"129","tr_id":"","d_rpt":"129",
        "locked":"0","sub_id":"1","seen":"1","creator":creator,"text_only":"0",
        "__display_name":"Test Contact",
        "__recipient_addresses":[{"_id":str(addr_id_start),"msg_id":str(id),"address":addr,"type":"151","charset":"106","__display_name":"Test Contact"}],
        "__parts":[]}
    if smil:
        obj["__parts"].append({"_id":str(part_id_start),"mid":str(id),"seq":"-1","ct":"application/smil","name":"smil.xml","cid":"<smil>","cl":"smil.xml","text":smil})
    obj["__parts"].append({"_id":str(part_id_start+1),"mid":str(id),"seq":"0","ct":"image/jpeg","name":"image000000.jpg","cid":"<image000000>","cl":"image000000.jpg","_data":"/data/user_de/0/com.android.providers.telephony/app_parts/"+part_name})
    return obj

smil_full = '<smil><head><layout><root-layout/><region id="Image" fit="meet" top="0" left="0" height="100%" width="100%"/></layout></head><body><par dur="5000ms"><img src="image000000.jpg" region="Image" /></par></body></smil>'
smil_short = '<smil><head><layout><root-layout/></layout></head><body><par dur="5000ms"><img src="image000000.jpg"/></par></body></smil>'

# V1: Fig creator, full SMIL, MMS date in seconds, both in+out
print("V1: Fig creator, full SMIL, date in seconds")
build_ndjson_zip("pom_v1_fig_full.zip", [
    sms(1, contact, "Test incoming", ts_ms, 1),
    sms(2, contact, "Test outgoing", ts_ms+5000, 2),
    mms_in(3, contact, "PART_001", smil_full, ts_s),
    mms_out(4, contact, "PART_002", smil_full, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V2: Pom creator
print("V2: Pom creator")
build_ndjson_zip("pom_v2_pom_creator.zip", [
    sms(1, contact, "Test incoming", ts_ms, 1, "com.pomphone.messaging"),
    sms(2, contact, "Test outgoing", ts_ms+5000, 2, "com.pomphone.messaging"),
    mms_in(3, contact, "PART_001", smil_full, ts_s, "com.pomphone.messaging"),
    mms_out(4, contact, "PART_002", smil_full, ts_s+100, "com.pomphone.messaging"),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V3: MMS date in milliseconds instead of seconds
print("V3: MMS date in milliseconds")
build_ndjson_zip("pom_v3_date_ms.zip", [
    sms(1, contact, "Test incoming", ts_ms, 1),
    sms(2, contact, "Test outgoing", ts_ms+5000, 2),
    mms_in(3, contact, "PART_001", smil_full, ts_ms),
    mms_out(4, contact, "PART_002", smil_full, ts_ms+60000),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V4: No SMIL part
print("V4: No SMIL part")
build_ndjson_zip("pom_v4_no_smil.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    mms_in(3, contact, "PART_001", None, ts_s),
    mms_out(4, contact, "PART_002", None, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V5: Short SMIL
print("V5: Short SMIL")
build_ndjson_zip("pom_v5_short_smil.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    mms_in(3, contact, "PART_001", smil_short, ts_s),
    mms_out(4, contact, "PART_002", smil_short, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V6: STORE compression (no deflate)
print("V6: STORE compression")
build_ndjson_zip("pom_v6_store.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    mms_in(3, contact, "PART_001", smil_full, ts_s),
    mms_out(4, contact, "PART_002", smil_full, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data}, zipfile.ZIP_STORED)

# V7: With both sender+recipient on incoming MMS
print("V7: Both sender+recipient addrs on incoming")
m7 = mms_in(3, contact, "PART_001", smil_full, ts_s)
m7["__recipient_addresses"] = [{"_id":"100002","msg_id":"3","address":"+19299970082","type":"151","charset":"106","__display_name":"(Unknown)"}]
build_ndjson_zip("pom_v7_both_addrs.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    m7,
    mms_out(4, contact, "PART_002", smil_full, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V8: MMS only, no SMS
print("V8: MMS only, no SMS")
build_ndjson_zip("pom_v8_mms_only.zip", [
    mms_in(3, contact, "PART_001", smil_full, ts_s),
    mms_out(4, contact, "PART_002", smil_full, ts_s+100),
], {"data/PART_001": img_data, "data/PART_002": img_data})

# V9: SMS only (control test — we know this works)
print("V9: SMS only (control)")
build_ndjson_zip("pom_v9_sms_only.zip", [
    sms(1, contact, "Test 1 incoming", ts_ms, 1),
    sms(2, contact, "Test 2 outgoing", ts_ms+5000, 2),
    sms(3, contact, "Test 3 incoming", ts_ms+10000, 1),
], {})

# V10: text_only=1 on MMS (no image, just text part)
print("V10: Text-only MMS")
m10 = {"_id":"3","thread_id":"1","date":str(ts_s),"date_sent":"0","msg_box":"1","read":"1",
    "m_id":"","ct_t":"application/vnd.wap.multipart.related","m_cls":"personal",
    "m_type":"132","v":"18","pri":"129","rr":"129","tr_id":"","d_rpt":"129",
    "locked":"0","sub_id":"1","seen":"1","creator":"com.figmessenger","text_only":"1",
    "__display_name":"Test Contact",
    "__sender_address":{"_id":"100001","msg_id":"3","address":contact,"type":"137","charset":"106","__display_name":"Test Contact"},
    "__parts":[{"_id":"200001","mid":"3","seq":"0","ct":"text/plain","text":"This is a text-only MMS"}]}
build_ndjson_zip("pom_v10_text_mms.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    m10,
], {})

# V11: Long PART names like real POM (timestamps)
print("V11: Long PART names like real POM")
build_ndjson_zip("pom_v11_long_part_names.zip", [
    sms(1, contact, "Test", ts_ms, 1),
    mms_in(3, contact, "PART_1779591189810", smil_full, ts_s),
    mms_out(4, contact, "PART_1779590339934", smil_full, ts_s+100),
], {"data/PART_1779591189810": img_data, "data/PART_1779590339934": img_data})

print(f"\nDone! 11 test files in {out_dir}")
