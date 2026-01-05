from app.publisher import RuuviMqttPublisher
from app.config import Settings

def test_topic_helpers():
    s = Settings(
        tags={"AA:BB:CC:11:22:33": "My Device"},
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_user="",
        mqtt_pass="",
        mqtt_retain=True,
        mqtt_qos=1,
        ha_discovery_prefix="homeassistant",
        avail_online="online",
        avail_offline="offline",
        publish_min_interval=10,
        mqtt_prefix="ruuvi",
    )
    pub = RuuviMqttPublisher(s)
    assert (
        pub.topic_bridge_availability()
        == "ruuvi/bridge/availability"
    )
    assert (
        pub.topic_availability("AA:BB:CC:11:22:33")
        == "ruuvi/My_Device/availability"
    )
    assert (
        pub.topic_json("AA:BB:CC:11:22:99")
        == "ruuvi/AA_BB_CC_11_22_99/json"
    )
    