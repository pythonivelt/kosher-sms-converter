import zipfile, os, datetime

img_path = "photo_2026-04-25_21-57-23.jpg"
with open(img_path, "rb") as f:
    img_data = f.read()

today = datetime.date.today().strftime("%Y-%m-%d")
now_ms = 1777011080393  # match the sample timestamp range

def build_wonder_zip(filename, sms_list, mms_list):
    """Build a Wonder-format ZIP backup."""
    sms_count = len(sms_list)
    mms_count = len(mms_list)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += f'<messages sms_count="{sms_count}" mms_count="{mms_count}">\n'

    for sms in sms_list:
        body = sms["body"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        xml += f'  <sms address="{sms["address"]}" body="{body}" date="{sms["date"]}" date_sent="0" type="{sms["type"]}" read="1" seen="1" />\n'

    attach_files = {}  # filename -> data
    mms_idx = 1
    for mms in mms_list:
        mms_idx += 1
        xml += f'  <mms date="{mms["date"]}" read="1" msg_box="{mms["msg_box"]}" ct_t="application/vnd.wap.multipart.related" m_type="{mms["m_type"]}" seen="1">\n'
        for addr in mms["addrs"]:
            xml += f'    <addr address="{addr["address"]}" type="{addr["type"]}" />\n'

        # SMIL part
        img_name = mms.get("img_name", "image000000.jpg")
        smil = f'&lt;smil&gt;&lt;head&gt;&lt;layout&gt;&lt;root-layout width=&quot;240&quot; height=&quot;160&quot;/&gt;&lt;region id=&quot;Image&quot; width=&quot;100%&quot; height=&quot;67%&quot; left=&quot;0%&quot; top=&quot;0%&quot; fit=&quot;meet&quot;/&gt;&lt;/layout&gt;&lt;/head&gt;&lt;body&gt;&lt;par dur=&quot;8000ms&quot;&gt;&lt;img src=&quot;{img_name}&quot; region=&quot;Image&quot;/&gt;&lt;/par&gt;&lt;/body&gt;&lt;/smil&gt;'
        xml += f'    <part ct="application/smil" name="smil.xml" cl="smil.xml" text="{smil}" />\n'

        # Image part
        part_idx = 2
        zip_fname = f"mms_{mms_idx}_{part_idx}.jpg"
        xml += f'    <part ct="image/jpeg" name="{img_name}" cl="{img_name}" file="{zip_fname}" />\n'
        attach_files[f"mms_attachments/{zip_fname}"] = mms.get("img_data", img_data)

        # Text part if present
        if mms.get("text"):
            text = mms["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            xml += f'    <part ct="text/plain" name="text.txt" cl="text.txt" text="{text}" />\n'

        xml += '  </mms>\n'

    xml += '</messages>\n'

    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Messages_Backup_{today}.xml", xml)
        for fname, data in attach_files.items():
            zf.writestr(fname, data)

    print(f"Created {filename}: {os.path.getsize(filename)} bytes ({sms_count} SMS, {mms_count} MMS)")


# Version 1: SMS only
build_wonder_zip(
    "../test_wonder_v1_sms_only.zip",
    sms_list=[
        {"address": "+12124441100", "body": "Test message 1", "date": str(now_ms), "type": "1"},
        {"address": "+12124441100", "body": "Test reply", "date": str(now_ms + 5000), "type": "2"},
        {"address": "+12124441100", "body": "Got it", "date": str(now_ms + 10000), "type": "1"},
    ],
    mms_list=[]
)

# Version 2: MMS only (1 incoming, 1 outgoing)
build_wonder_zip(
    "../test_wonder_v2_mms_only.zip",
    sms_list=[],
    mms_list=[
        {
            "date": str(now_ms // 1000),  # MMS dates in seconds
            "msg_box": "1", "m_type": "132",
            "addrs": [{"address": "12124441100", "type": "137"}, {"address": "19299970082", "type": "151"}],
            "img_name": "image000000.jpg",
        },
        {
            "date": str((now_ms + 60000) // 1000),
            "msg_box": "2", "m_type": "128",
            "addrs": [{"address": "19299970082", "type": "137"}, {"address": "+12124441100", "type": "151"}],
            "img_name": "image000000.jpg",
        },
    ]
)

# Version 3: Mix of SMS and MMS
build_wonder_zip(
    "../test_wonder_v3_mixed.zip",
    sms_list=[
        {"address": "+12124441100", "body": "Hello from test", "date": str(now_ms), "type": "1"},
        {"address": "+12124441100", "body": "Hi back", "date": str(now_ms + 5000), "type": "2"},
    ],
    mms_list=[
        {
            "date": str((now_ms + 30000) // 1000),
            "msg_box": "1", "m_type": "132",
            "addrs": [{"address": "12124441100", "type": "137"}, {"address": "19299970082", "type": "151"}],
            "img_name": "image000000.jpg",
            "text": "Check this picture",
        },
    ]
)

print("\nAll test files created in Downloads folder")
