# Volcano Integration for Home Assistant

**This integration is under heavy, active development. There may be multiple updates per day, possibly resulting in errors or distruption to the integration or Home Assistant. I will change this notice once the software is available for a proper  release.**

A custom Home Assistant integration to connect and control the **Storz & Bickel Volcano Hybrid Vaporizer** via Bluetooth. This integration enables precise control over the vaporizer's heat and pump functions, real-time monitoring of temperature, and seamless automation.

---

## Features

- **Temperature Control**: Set the heater temperature between 40°C and 230°C with 1°C precision.
- **Pump Control**: Turn the pump ON or OFF to start or stop air circulation.
- **Real-Time Temperature Monitoring**: Monitor the current heater temperature in real-time.
- **Bluetooth Status**: View the current Bluetooth connection status (Connected, Disconnected, etc.).
- **Full Automation Support**: Automate heat, pump, and temperature settings using Home Assistant scripts or automations.
- **User-Friendly Services**: Use built-in Home Assistant services to control the vaporizer.

---

## Requirements

- **Bluetooth Hardware**: The host system must have Bluetooth hardware or a compatible USB Bluetooth adapter.
- **Python Dependency**: Requires the `bleak` library (minimum version 0.20.0).

---

## Installation

1. **Download the Integration**:
   - Clone or download the repository from GitHub: [GitHub Repository](https://github.com/Chuffnugget/volcano_integration).

2. **Place in Custom Components**:
   - Extract the files and place the `volcano_integration` folder in the `custom_components` directory within your Home Assistant configuration directory.

3. **Install Dependencies**:
   - Ensure the required dependencies (e.g., `bleak`) are installed. Home Assistant should handle this automatically.

4. **Restart Home Assistant**:
   - After placing the files, restart Home Assistant.

5. **Add the Integration**:
   - Navigate to **Settings > Integrations > Add Integration**, search for "Volcano Integration," and follow the setup instructions.

---

## Usage

### Entities

- **Sensors**:
  - Current Temperature: Displays the current temperature of the vaporizer.
  - Heat Status: Shows whether the heater is ON, OFF, or in an unknown state.
  - Pump Status: Indicates if the pump is ON, OFF, or in an unknown state.
  - Bluetooth Status: Displays the current Bluetooth connection status.

- **Buttons**:
  - Connect: Establishes a Bluetooth connection with the vaporizer.
  - Disconnect: Ends the Bluetooth connection.
  - Pump On/Off: Turns the pump ON or OFF.
  - Heat On/Off: Turns the heater ON or OFF.

- **Number Control**:
  - Heater Temperature Setpoint: Allows setting the desired temperature between 40°C and 230°C.

### Services

- `volcano_integration.connect`: Connect to the vaporizer.
- `volcano_integration.disconnect`: Disconnect from the vaporizer.
- `volcano_integration.pump_on`: Turn the pump ON.
- `volcano_integration.pump_off`: Turn the pump OFF.
- `volcano_integration.heat_on`: Turn the heater ON.
- `volcano_integration.heat_off`: Turn the heater OFF.
- `volcano_integration.set_temperature`: Set the heater temperature.

---

## Uninstall

1. **Remove the Integration**:
   - Navigate to **Settings > Integrations** and remove the "Volcano Integration."

2. **Delete Files**:
   - Delete the `volcano_integration` folder from the `custom_components` directory.

3. **Restart Home Assistant**:
   - Restart Home Assistant to finalize the uninstallation process.

---

## Support

For issues or feature requests, visit the [GitHub Issues](https://github.com/Chuffnugget/volcano_integration/issues) page.

---

## License

This project is licensed under the [MIT License](LICENSE).
