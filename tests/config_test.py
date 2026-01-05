from app.config import device_id_from_mac, safe_topic_part

def test_safe_topic_part():
    assert safe_topic_part(" My Device/Name:01+# ") == "My_Device_Name01__"

def test_device_id_from_mac():
    assert device_id_from_mac("AA:BB:CC:11:22:33") == "aabbcc112233"

    