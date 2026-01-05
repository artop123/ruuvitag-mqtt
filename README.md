# RuuviTag → MQTT Publisher (Home Assistant)

This project listens to RuuviTag BLE advertisements (via BlueZ) and publishes sensor readings to MQTT.
It also publishes Home Assistant MQTT Discovery configs automatically, so sensors appear in Home Assistant without manual configuration.

## Features

- Reads RuuviTag BLE advertisements (BlueZ)
- Publishes readings to MQTT
- Home Assistant MQTT Discovery (temperature / humidity / pressure / battery)

## Requirements

- Linux host with a Bluetooth adapter
- Docker + Docker Compose
- Mosquitto / MQTT broker (Home Assistant add-on or standalone)

## Setup

Create a `docker-compose.yml` file. The `privileged`, `network_mode`, and `volumes` settings are required for Bluetooth access.

```yaml
services:
  ruuvi_mqtt:
    image: artop/ruuvitag-mqtt:latest
    container_name: ruuvi_mqtt
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - /var/run/dbus:/var/run/dbus
    environment:
      MQTT_HOST: "192.168.68.10"
      MQTT_PORT: "1883"
      MQTT_USER: "mqttuser"
      MQTT_PASS: "mqttpass"
```

Pull the image

```bash
docker compose pull
```

Run the scanner to list nearby RuuviTag devices:

```bash
docker compose run --rm ruuvi_mqtt python -m app.scan
```

Create a JSON mapping of devices (`mac-address: friendly name`):

```json
{"A1:B2:C3:D4:E5:F6":"outside","A7:B8:C9:DD:EE:FF":"livingroom"}
```

Add the devices to the `docker-compose.yml` environment variables:

```yaml
services:
  ruuvi_mqtt:
    # ...
    environment:
      RUUVI_TAGS: '{"A1:B2:C3:D4:E5:F6":"outside"}'
    # ...
```

Start the container

```bash
docker compose up -d
```
