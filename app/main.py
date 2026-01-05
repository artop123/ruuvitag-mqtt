import signal
import sys
import time

from ruuvitag_sensor.ruuvi import RuuviTagSensor

from .config import load_settings
from .publisher import RuuviMqttPublisher


def main():
    s = load_settings()

    print("Starting RuuviTag → MQTT publisher")
    print("Tags:")
    for mac, name in s.tags.items():
        print(f" - {mac} = {name}")
    print(
        f"MQTT: {s.mqtt_host}:{s.mqtt_port}, "
        f"prefix='{s.mqtt_prefix}', retain={s.mqtt_retain}, qos={s.mqtt_qos}, "
        f"min_interval={s.publish_min_interval}s"
    )

    pub = RuuviMqttPublisher(s)
    pub.connect()

    # Graceful shutdown → publish offline
    def shutdown(_signum=None, _frame=None):
        print("Shutting down, publishing OFFLINE ...")
        try:
            if pub.client and pub.client.is_connected():
                pub.publish_all_offline()
                pub.client.publish(pub.topic_bridge_availability(), s.avail_offline, qos=1, retain=True)
                time.sleep(0.2)
        except Exception as e:
            print("Failed to publish offline:", e)

        pub.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    macs = list(s.tags.keys())

    def callback(data):
        # data is: (mac, dict)
        mac = data[0]
        payload = data[1]
        try:
            pub.publish_ruuvi(mac, payload)
        except Exception as e:
            print(f"MQTT publish failed for {mac}: {e}")

    # Blocks and calls callback when data arrives
    RuuviTagSensor.get_data(callback, macs)

    # Keep alive
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
