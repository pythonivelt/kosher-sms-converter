import zipfile, os

img_path = "photo_2026-04-25_21-57-23.jpg"
with open(img_path, "rb") as f:
    img_data = f.read()

out_dir = r"C:\Users\Moishe Schnitzler\Downloads\wonder-test-zips"
today = "2026-06-01"
ts_ms = 1777011080393
ts_s = ts_ms // 1000
contact = "+12124441100"
contact_bare = "12124441100"

def save(name, xml, attachments, compression=zipfile.ZIP_DEFLATED):
    path = os.path.join(out_dir, name)
    with zipfile.ZipFile(path, "w", compression) as zf:
        zf.writestr(f"Messages_Backup_{today}.xml", xml)
        for fn, data in attachments.items():
            zf.writestr(fn, data)
    print(f"  {name}: {os.path.getsize(path)} bytes")

smil_full = '&lt;smil&gt;\n    &lt;head&gt;\n        &lt;layout&gt;\n            &lt;root-layout width=&quot;240&quot; height=&quot;160&quot;/&gt;\n            &lt;region id=&quot;Image&quot; width=&quot;100%&quot; height=&quot;67%&quot; left=&quot;0%&quot; top=&quot;0%&quot; fit=&quot;meet&quot;/&gt;\n            &lt;region id=&quot;Text&quot; width=&quot;100%&quot; height=&quot;33%&quot; left=&quot;0%&quot; top=&quot;67%&quot; fit=&quot;meet&quot;/&gt;\n        &lt;/layout&gt;\n    &lt;/head&gt;\n    &lt;body&gt;\n    &lt;par dur=&quot;8000ms&quot;&gt;&lt;img src=&quot;image000000.jpg&quot; region=&quot;Image&quot;/&gt;&lt;/par&gt;&lt;/body&gt;\n&lt;/smil&gt;'

smil_short = '&lt;smil xmlns=&quot;http://www.w3.org/2001/SMIL20/Language&quot;&gt;&lt;head&gt;&lt;layout/&gt;&lt;/head&gt;&lt;body&gt;&lt;par dur=&quot;8000ms&quot;&gt;&lt;img src=&quot;image000000.jpg&quot;/&gt;&lt;/par&gt;&lt;/body&gt;&lt;/smil&gt;'

# V1: Exact replica — sender addr only (incoming MMS)
print("V1: Exact replica, sender addr only")
xml1 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="2" mms_count="1">
  <sms address="{contact}" body="Test message" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <sms address="{contact}" body="Reply" date="{ts_ms+5000}" date_sent="0" type="2" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_v1_sender_only.zip", xml1, {"mms_attachments/mms_2_2.jpg": img_data})

# V2: Both addrs but receiver as insert-number placeholder
print("V2: Both addrs, receiver as 15550000000")
xml2 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="2" mms_count="1">
  <sms address="{contact}" body="Test message" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <sms address="{contact}" body="Reply" date="{ts_ms+5000}" date_sent="0" type="2" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="15550000000" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_v2_dummy_receiver.zip", xml2, {"mms_attachments/mms_2_2.jpg": img_data})

# V3: No addr entries at all on MMS
print("V3: No addr entries on MMS")
xml3 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="2" mms_count="1">
  <sms address="{contact}" body="Test message" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <sms address="{contact}" body="Reply" date="{ts_ms+5000}" date_sent="0" type="2" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_v3_no_addr.zip", xml3, {"mms_attachments/mms_2_2.jpg": img_data})

# V4: STORE compression
print("V4: STORE compression")
save("wonder_v4_store.zip", xml1, {"mms_attachments/mms_2_2.jpg": img_data}, zipfile.ZIP_STORED)

# V5: SMS only
print("V5: SMS only")
xml5 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="3" mms_count="0">
  <sms address="{contact}" body="Test 1" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <sms address="{contact}" body="Test 2" date="{ts_ms+5000}" date_sent="0" type="2" read="1" seen="1" />
  <sms address="{contact}" body="Test 3" date="{ts_ms+10000}" date_sent="0" type="1" read="1" seen="1" />
</messages>
'''
save("wonder_v5_sms_only.zip", xml5, {})

# V6: MMS with text + image
print("V6: MMS with text + image")
xml6 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="0" mms_count="1">
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
    <part ct="text/plain" name="text.txt" cl="text.txt" text="Look at this picture!" />
  </mms>
</messages>
'''
save("wonder_v6_mms_with_text.zip", xml6, {"mms_attachments/mms_2_2.jpg": img_data})

# V7: Minimal
print("V7: Minimal attributes")
xml7 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Hello" date="{ts_ms}" type="1" read="1" />
  <mms date="{ts_s}" msg_box="1" m_type="132">
    <addr address="{contact_bare}" type="137" />
    <part ct="image/jpeg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_v7_minimal.zip", xml7, {"mms_attachments/mms_2_2.jpg": img_data})

# V8: No SMIL
print("V8: No SMIL part")
xml8 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_v8_no_smil.zip", xml8, {"mms_attachments/mms_2_2.jpg": img_data})

# V9: In + out MMS, short SMIL on outgoing
print("V9: Incoming + outgoing MMS")
xml9 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="0" mms_count="2">
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
  <mms date="{ts_s+100}" read="1" msg_box="2" ct_t="application/vnd.wap.multipart.related" m_type="128" seen="0">
    <addr address="{contact}" type="151" />
    <part ct="application/smil" cl="smil.xml" text="{smil_short}" />
    <part ct="image/jpeg" cl="image000000.jpg" file="mms_3_4.jpg" />
  </mms>
</messages>
'''
save("wonder_v9_in_and_out.zip", xml9, {
    "mms_attachments/mms_2_2.jpg": img_data,
    "mms_attachments/mms_3_4.jpg": img_data,
})

print("\nDone! 9 files rebuilt")
