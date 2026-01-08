import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Dict, Optional
from .config import Settings, safe_topic_part, device_id_from_mac, write_log

class RuuviMqttPublisher:
    def __init__(self, settings: Settings):
        self.s = settings
        self.client: Optional[mqtt.Client] = None
        self.last_publish: Dict[str, float] = {}

    # ---------- Topic helpers ----------
    def tag_node(self, mac: str) -> str:
        name = self.s.tags.get(mac, mac)
        return safe_topic_part(name or mac)

    def topic_json(self, mac: str) -> str:
        return f"{self.s.mqtt_prefix}/{self.tag_node(mac)}/json"

    def topic_availability(self, mac: str) -> str:
        return f"{self.s.mqtt_prefix}/{self.tag_node(mac)}/availability"

    def topic_bridge_availability(self) -> str:
        return f"{self.s.mqtt_prefix}/bridge/availability"

    # ---------- HA Discovery ----------
    def publish_ha_discovery(self, mac: str, name: str):
        base_json_topic = self.topic_json(mac)
        avail_topic = self.topic_availability(mac)
        dev_id = device_id_from_mac(mac)

        device = {
            "identifiers": [f"ruuvi_{dev_id}"],
            "name": f"RuuviTag {name}",
            "manufacturer": "Ruuvi Innovations",
            "model": "RuuviTag",
        }

        sensors = {
            "temperature": {
                "name": f"{name} Temperature",
                "unit": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "value_template": "{{ value_json.temperature }}",
            },
            "humidity": {
                "name": f"{name} Humidity",
                "unit": "%",
                "device_class": "humidity",
                "state_class": "measurement",
                "value_template": "{{ value_json.humidity }}",
            },
            "pressure": {
                "name": f"{name} Pressure",
                "unit": "hPa",
                "device_class": "pressure",
                "state_class": "measurement",
                "value_template": "{{ value_json.pressure }}",
            },
            "battery": {
                "name": f"{name} Battery",
                "unit": "mV",
                "device_class": "voltage",
                "state_class": "measurement",
                "value_template": "{{ value_json.battery }}",
            },
        }

        for key, cfg in sensors.items():
            unique_id = f"ruuvi_{dev_id}_{key}"
            topic = f"{self.s.ha_discovery_prefix}/sensor/{unique_id}/config"

            payload = {
                "name": cfg["name"],
                "unique_id": unique_id,
                "state_topic": base_json_topic,
                "value_template": cfg["value_template"],
                "unit_of_measurement": cfg["unit"],
                "device_class": cfg["device_class"],
                "state_class": cfg["state_class"],
                "availability_topic": avail_topic,
                "payload_available": self.s.avail_online,
                "payload_not_available": self.s.avail_offline,
                "device": device,
            }

            self.client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)

    # ---------- Availability ----------
    def publish_all_online(self):
        for mac in self.s.tags.keys():
            self.client.publish(self.topic_availability(mac), self.s.avail_online, qos=1, retain=True)

    def publish_all_offline(self):
        for mac in self.s.tags.keys():
            self.client.publish(self.topic_availability(mac), self.s.avail_offline, qos=1, retain=True)

    # ---------- MQTT Connection ----------
    def connect(self) -> mqtt.Client:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

        if self.s.mqtt_user:
            client.username_pw_set(self.s.mqtt_user, self.s.mqtt_pass)

        bridge_avail = self.topic_bridge_availability()

        # LWT (bridge offline if hard crash)
        client.will_set(bridge_avail, self.s.avail_offline, qos=1, retain=True)

        # Reconnect backoff
        client.reconnect_delay_set(min_delay=1, max_delay=60)

        def on_connect(_client, _userdata, _flags, reason_code, _properties=None):
            write_log(f"MQTT connected, reason_code={reason_code}")

            # Bridge online
            _client.publish(bridge_avail, self.s.avail_online, qos=1, retain=True)

            # Re-publish discovery + per-tag online (important after broker restart)
            for mac, name in self.s.tags.items():
                self.publish_ha_discovery(mac, name)
            self.publish_all_online()

        def on_disconnect(_client, _userdata, disconnect_flags, reason_code, properties):
            write_log(f"MQTT disconnected, reason_code={reason_code} (will retry)")

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        # Async connect so app can start even if broker down
        client.connect_async(self.s.mqtt_host, self.s.mqtt_port, keepalive=60)
        client.loop_start()

        self.client = client
        return client

    def disconnect(self):
        if not self.client:
            return
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    # ---------- Publish sensor data ----------
    def should_publish(self, mac: str) -> bool:
        now = time.time()
        last = self.last_publish.get(mac, 0.0)
        return (now - last) >= self.s.publish_min_interval

    def publish_ruuvi(self, mac: str, payload: dict):
        if not self.client or not self.client.is_connected():
            return

        if not self.should_publish(mac):
            return

        self.last_publish[mac] = time.time()

        name = self.s.tags.get(mac, mac)
        ts = datetime.now().isoformat(timespec="seconds")

        data = dict(payload)
        data["mac"] = mac
        data["name"] = name
        data["time"] = ts

        self.client.publish(
            self.topic_json(mac),
            json.dumps(data, ensure_ascii=False),
            qos=self.s.mqtt_qos,
            retain=self.s.mqtt_retain,
        )
