from datetime import datetime
import json
import os
from dataclasses import dataclass
from typing import Dict

def write_log(message: str):
    time = datetime.now().isoformat(timespec="seconds")
    message = f"{time} {message}"
    print(message)

def safe_topic_part(value: str) -> str:
    return (
        value.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(":", "")
        .replace("#", "_")
        .replace("+", "_")
    )

def device_id_from_mac(mac: str) -> str:
    return safe_topic_part(mac.lower())

@dataclass(frozen=True)
class Settings:
    tags: Dict[str, str]

    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_pass: str
    mqtt_prefix: str
    mqtt_retain: bool
    mqtt_qos: int

    ha_discovery_prefix: str
    avail_online: str
    avail_offline: str

    publish_min_interval: int


def load_settings() -> Settings:
    tags = json.loads(os.getenv("RUUVI_TAGS", "{}"))
    if not tags:
        raise SystemExit(
            "RUUVI_TAGS is empty. Set it e.g. "
            'RUUVI_TAGS=\'{"AA:BB:CC:11:22:33":"device1"}\''
        )

    return Settings(
        tags=tags,
        mqtt_host=os.getenv("MQTT_HOST", "localhost"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_user=os.getenv("MQTT_USER", ""),
        mqtt_pass=os.getenv("MQTT_PASS", ""),
        mqtt_prefix=os.getenv("MQTT_PREFIX", "ruuvi"),
        mqtt_retain=os.getenv("MQTT_RETAIN", "false").lower() == "true",
        mqtt_qos=int(os.getenv("MQTT_QOS", "0")),
        ha_discovery_prefix=os.getenv("HA_DISCOVERY_PREFIX", "homeassistant"),
        avail_online=os.getenv("AVAIL_ONLINE", "online"),
        avail_offline=os.getenv("AVAIL_OFFLINE", "offline"),
        publish_min_interval=int(os.getenv("PUBLISH_MIN_INTERVAL", "15")),
    )
