# Volcano Integration

**Volcano Integration** allows you to control and monitor your Volcano Vaporizer directly from Home Assistant.

## Features

- Monitor current temperature
- Control pump (ON/OFF)
- Control heat (ON/OFF)
- Set heater temperature

## Installation

### Via HACS (Recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.
2. Navigate to **HACS > Integrations**.
3. Click the **+** button to add a new integration.
4. Search for **Volcano Integration** and install it.
5. Restart Home Assistant.

### Manual Installation

1. Download the repository as a ZIP file.
2. Extract the contents and place the `volcano_integration` folder inside the `custom_components` directory of your Home Assistant configuration.
3. Restart Home Assistant.

## Configuration

1. Navigate to **Configuration > Integrations** in Home Assistant.
2. Click **Add Integration** and search for **Volcano Integration**.
3. Enter the required information:
   - **Name:** Volcano Vaporizer
   - **MAC Address:** Your device's MAC address (format: XX:XX:XX:XX:XX:XX)
4. Complete the setup and restart Home Assistant if prompted.

## Usage

- **Sensors:**
  - **Volcano Current Temperature:** Displays the current temperature of the device.
  - **Volcano Heat Status:** Shows whether the heat is ON or OFF.
  - **Volcano Pump Status:** Indicates the pump's current state (ON/OFF).
  - **Volcano Bluetooth Status:** Shows the Bluetooth connection status.

- **Buttons:**
  - **Volcano Connect:** Manually connect the device.
  - **Volcano Disconnect:** Manually disconnect the device.
  - **Volcano Pump On:** Turn the pump ON.
  - **Volcano Pump Off:** Turn the pump OFF.
  - **Volcano Heat On:** Turn the heat ON.
  - **Volcano Heat Off:** Turn the heat OFF.

- **Number:**
  - **Volcano Heater Temperature Setpoint:** Set the desired heater temperature (40–230 °C).

## Troubleshooting

- **Icon Not Displaying Correctly:** Ensure that both `icon` and `logo` are correctly specified in `manifest.json`.
- **Connection Issues:** Verify the MAC address and ensure the device is powered on and within Bluetooth range.
- **Unknown Pump/Heat Patterns:** Check the logs for any new byte patterns and update `VALID_PATTERNS` accordingly.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

[MIT License](LICENSE)
