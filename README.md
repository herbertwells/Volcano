# Volcano Integration (HACS Custom Integration)

This is a simple Home Assistant custom integration that connects to a Bluetooth GATT device:
- **Temperature** read from UUID `10110001-5354-4f52-5a26-4249434b454c`
- **Fan/Heat Control** notifications from UUID `1010000c-5354-4f52-5a26-4249434b454c`
- Uses static addresses and no user inputs, just a config flow with a "Submit" button.

## Features

1. Automatic reconnection every 3 seconds if disconnected.
2. Polling temperature every 1 second.
3. Subscribes to fan/heat notifications (displayed as a string sensor).
4. Verbose logging to help debug connection or parsing issues.

## Installation

1. Copy the `volcano_integration` folder to `config/custom_components/` in your Home Assistant setup.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services** -> **Add Integration** -> Search for **Volcano Integration** -> **Submit**.
4. Two new sensors will appear:
   - `Volcano Current Temperature`
   - `Volcano Fan/Heat Control`

## Adjusting Data Parsing

- By default, this integration tries to interpret:
  - 2-byte data as a 16-bit integer.
  - 4-byte data as a 32-bit float.
- If your device uses another format, update `bluetooth_coordinator.py` to match the actual data layout.
