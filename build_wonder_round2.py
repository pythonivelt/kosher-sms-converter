import zipfile, os

img_path = "photo_2026-04-25_21-57-23.jpg"
with open(img_path, "rb") as f:
    img_data = f.read()

# Also create a small 100x100 JPEG for testing size
from struct import pack
# Minimal JPEG: just use the real one but note it's 98KB

out_dir = r"C:\Users\Moishe Schnitzler\Downloads\wonder-test-zips-r2"
os.makedirs(out_dir, exist_ok=True)

today = "2026-06-02"
ts_ms = 1777011080393
ts_s = ts_ms // 1000
contact = "+12124441100"
contact_bare = "12124441100"
dummy_recv = "15550000000"

smil_full = '&lt;smil&gt;\n    &lt;head&gt;\n        &lt;layout&gt;\n            &lt;root-layout width=&quot;240&quot; height=&quot;160&quot;/&gt;\n            &lt;region id=&quot;Image&quot; width=&quot;100%&quot; height=&quot;67%&quot; left=&quot;0%&quot; top=&quot;0%&quot; fit=&quot;meet&quot;/&gt;\n            &lt;region id=&quot;Text&quot; width=&quot;100%&quot; height=&quot;33%&quot; left=&quot;0%&quot; top=&quot;67%&quot; fit=&quot;meet&quot;/&gt;\n        &lt;/layout&gt;\n    &lt;/head&gt;\n    &lt;body&gt;\n    &lt;par dur=&quot;8000ms&quot;&gt;&lt;img src=&quot;image000000.jpg&quot; region=&quot;Image&quot;/&gt;&lt;/par&gt;&lt;/body&gt;\n&lt;/smil&gt;'

smil_with_file = smil_full.replace('image000000.jpg', 'mms_2_2.jpg')

def save(name, xml, attachments, compression=zipfile.ZIP_DEFLATED):
    path = os.path.join(out_dir, name)
    with zipfile.ZipFile(path, "w", compression) as zf:
        zf.writestr(f"Messages_Backup_{today}.xml", xml)
        for fn, data in attachments.items():
            zf.writestr(fn, data)
    print(f"  {name}: {os.path.getsize(path)} bytes")

# All round 2 tests use both addrs (required based on round 1)
# Focus on picture visibility

# R2-V1: file attr matches cl, SMIL src matches cl (baseline from round 1 v2)
print("R2-V1: Baseline — file=mms_2_2.jpg, cl=image000000.jpg, smil src=image000000.jpg")
xml1 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_r2_v1.zip", xml1, {"mms_attachments/mms_2_2.jpg": img_data})

# R2-V2: SMIL src = file name (mms_2_2.jpg) instead of cl
print("R2-V2: SMIL src matches file attr (mms_2_2.jpg)")
xml2 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_with_file}" />
    <part ct="image/jpeg" name="mms_2_2.jpg" cl="mms_2_2.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_r2_v2.zip", xml2, {"mms_attachments/mms_2_2.jpg": img_data})

# R2-V3: No SMIL, just the image part with both name+cl+file all same
print("R2-V3: No SMIL, all names match mms_2_2.jpg")
xml3 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="image/jpeg" name="mms_2_2.jpg" cl="mms_2_2.jpg" file="mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_r2_v3.zip", xml3, {"mms_attachments/mms_2_2.jpg": img_data})

# R2-V4: Image directly in ZIP root (not in mms_attachments/)
print("R2-V4: Image in ZIP root, not mms_attachments/")
xml4 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="image000000.jpg" />
  </mms>
</messages>
'''
save("wonder_r2_v4.zip", xml4, {"image000000.jpg": img_data})

# R2-V5: file attr includes path: mms_attachments/mms_2_2.jpg
print("R2-V5: file attr has full path mms_attachments/mms_2_2.jpg")
xml5 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_attachments/mms_2_2.jpg" />
  </mms>
</messages>
'''
save("wonder_r2_v5.zip", xml5, {"mms_attachments/mms_2_2.jpg": img_data})

# R2-V6: data attribute instead of file (like SMS Backup & Restore uses base64)
# Wonder might read inline base64 data
import base64
b64_img = base64.b64encode(img_data).decode()
print("R2-V6: Inline base64 data attribute instead of file")
xml6 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" data="{b64_img}" />
  </mms>
</messages>
'''
save("wonder_r2_v6.zip", xml6, {})

# R2-V7: Both file AND data attributes
print("R2-V7: Both file + data attributes")
xml7 = f'''<?xml version="1.0" encoding="UTF-8"?>
<messages sms_count="1" mms_count="1">
  <sms address="{contact}" body="Test" date="{ts_ms}" date_sent="0" type="1" read="1" seen="1" />
  <mms date="{ts_s}" read="1" msg_box="1" ct_t="application/vnd.wap.multipart.related" m_type="132" seen="1">
    <addr address="{contact_bare}" type="137" />
    <addr address="{dummy_recv}" type="151" />
    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil_full}" />
    <part ct="image/jpeg" name="image000000.jpg" cl="image000000.jpg" file="mms_2_2.jpg" data="{b64_img}" />
  </mms>
</messages>
'''
save("wonder_r2_v7.zip", xml7, {"mms_attachments/mms_2_2.jpg": img_data})

# R2-V8: STORE compression instead of DEFLATE for attachments
print("R2-V8: STORE compression")
save("wonder_r2_v8.zip", xml1, {"mms_attachments/mms_2_2.jpg": img_data}, zipfile.ZIP_STORED)

print(f"\nDone! 8 round-2 test files in {out_dir}")
