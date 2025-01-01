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

1. **Download Integration:**
   - Clone the repository:
     ```bash
     git clone https://github.com/YourUsername/volcano_integration.git
     ```
   - Or download the ZIP and extract it.

2. **Copy to Home Assistant:**
   - Place the `volcano_integration` folder into your Home Assistant's `custom_components` directory:
     ```
     config/
     └── custom_components/
         └── volcano_integration/
             ├── __init__.py
             ├── bluetooth_coordinator.py
             ├── sensor.py
             ├── button.py
             ├── number.py
             └── manifest.json
     ```

3. **Install Dependencies:**
   - Ensure `bleak` library is installed (version ≥ 0.20.0):
     ```bash
     pip install bleak>=0.20.0
     ```

4. **Restart Home Assistant:**
   - Go to **Configuration > Server Controls** and click **Restart**.

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
  - Ensure `number.py` has `native_min_value` and `native_max_value` set to 40.0 and 230.0 respectively.
  - Delete the existing number entity in Home Assistant and restart.
  - Clear browser cache or use incognito mode.

- **Bluetooth Issues:**
  - Verify device MAC address in `bluetooth_coordinator.py`.
  - Ensure no other device is connected to the Volcano heater.
  - Check Bluetooth adapter compatibility.

- **Entities Not Showing:**
  - Check Home Assistant logs for errors.
  - Ensure all files are correctly placed in `custom_components/volcano_integration/`.

## Contributing

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with clear descriptions.

## License

MIT License. See [LICENSE](LICENSE) for details.
