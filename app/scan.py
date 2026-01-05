import os
from ruuvitag_sensor.ruuvi import RuuviTagSensor


def main():
    os.environ.setdefault("RUUVI_BLE_ADAPTER", "bluez")

    print("Scanning for RuuviTags ...")
    print("Tip: Move the tags to make them advertise more often.\n")

    RuuviTagSensor.find_ruuvitags()

if __name__ == "__main__":
    main()
