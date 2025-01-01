# Volcano Integration for Home Assistant

A custom Home Assistant integration to monitor and control your Volcano heater via Bluetooth.

## Features

- **Temperature Monitoring:** Displays current temperature (°C).
- **Heat Status:** Shows if the heater is ON, OFF, or UNKNOWN.
- **Fan Status:** Indicates if the fan is ON, OFF, or UNKNOWN.
- **RSSI Monitoring:** Displays Bluetooth signal strength (dBm).
- **Bluetooth Status:** Shows connection status (CONNECTING, CONNECTED, DISCONNECTED).
- **Control Buttons:**
  - **Connect/Disconnect:** Manage Bluetooth connection manually.
  - **Fan On/Off:** Control the fan state.
  - **Heat On/Off:** Control the heater state.
- **Temperature Setpoint:** Slider to set heater temperature (40°C - 230°C, default 170°C).

## Installation

1. **Add Integration via HACS:**
   - Ensure you have [HACS](https://hacs.xyz/) installed.
   - In Home Assistant, go to **HACS > Integrations**.
   - Click **Browse & Add Repositories**.
   - Search for "Volcano Integration" and add it.

2. **Dependencies Managed by HACS:**
   - The integration requires `bleak>=0.20.0`.
   - HACS will automatically install this dependency based on the `manifest.json`.

3. **Restart Home Assistant:**
   - After installation, go to **Configuration > Server Controls**.
   - Click **Restart** under **Server management**.

## Configuration

1. **Add Integration:**
   - Navigate to **Configuration > Devices & Services**.
   - Click **Add Integration** and search for "Volcano Integration".
   - Follow the prompts to set up.

2. **Manage Connection:**
   - Use **Volcano Connect** and **Volcano Disconnect** buttons to manage Bluetooth manually.

## Entities

### Sensors

- **Volcano Current Temperature:** Displays current temperature.
- **Volcano Heat Status:** Shows heater state.
- **Volcano Fan Status:** Shows fan state.
- **Volcano RSSI:** Shows Bluetooth signal strength.
- **Volcano Bluetooth Status:** Shows Bluetooth connection status.

### Buttons

- **Volcano Connect:** Connect to the Volcano device.
- **Volcano Disconnect:** Disconnect from the Volcano device.
- **Volcano Fan On:** Turn fan ON.
- **Volcano Fan Off:** Turn fan OFF.
- **Volcano Heat On:** Turn heater ON.
- **Volcano Heat Off:** Turn heater OFF.

### Number Entity

- **Volcano Heater Temperature Setpoint:** Set heater temperature (40°C - 230°C, default 170°C).

## Troubleshooting

- **Slider Range Incorrect (0°C - 100°C):**
  - Ensure `manifest.json` includes `"bleak>=0.20.0"` under `requirements`.
  - Create a new GitHub release/tag for the integration.
  - Update the integration via HACS to trigger dependency installation.
  - Clear browser cache or use an incognito window.

- **Bluetooth Issues:**
  - Verify device MAC address in `bluetooth_coordinator.py`.
  - Ensure no other device is connected to the Volcano heater.
  - Check Bluetooth adapter compatibility.

- **Entities Not Showing:**
  - Check Home Assistant logs for errors.
  - Ensure all files are correctly placed in `custom_components/volcano_integration/`.
