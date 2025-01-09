# Volcano Integration for Home Assistant

**This integration is under heavy, active development. There may be multiple updates per day, possibly resulting in errors or disruption to the integration or Home Assistant. I will change this notice once the software is available for a proper release.**

A custom Home Assistant integration to connect and control the **Storz & Bickel Volcano Hybrid Vaporizer** via Bluetooth. This integration enables precise control over the vaporizer's heat and pump functions, real-time monitoring of temperature, and seamless automation into the Home Assistant scripting and automation systems.

---

## Features

- **Temperature Control**: Set the heater temperature between 40°C and 230°C with 1°C precision.
- **Pump Control**: Turn the pump **ON** or **OFF** to start or stop air circulation.
- **Heat Control**: Turn the heater **ON** or **OFF**.
- **Vibration Control**: Enable or disable the vibration feature.
- **LED Brightness Control**: Adjust the LED brightness between 0% and 100%.
- **Auto Shutoff Control**: Enable/disable auto shutoff and set the shutoff duration.
- **Real-Time Temperature Monitoring**: Monitor the current heater temperature in real-time.
- **Bluetooth Status**: View the current Bluetooth connection status (Connected, Disconnected, etc.).
- **Firmware and Serial Information**: Access BLE firmware version, device firmware version, and serial number.
- **Operational Hours Monitoring**: Track hours and minutes of operation.
- **Connection Control**: Manage Bluetooth connection via a dedicated switch.
- **Full Automation Support**: Automate heat, pump, vibration, LED brightness, auto shutoff, and connection settings using Home Assistant scripts or automations.
- **User-Friendly Services**: Use built-in Home Assistant services to control various aspects of the vaporizer.

---

## Requirements

- **Bluetooth Hardware**: The host system must have Bluetooth hardware or a compatible USB Bluetooth adapter.
- **Python Dependency**: Requires the `bleak` library (minimum version 0.20.0).

---

## Installation

### Installation via HACS

1. **Prerequisites**:
   - Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.

2. **Add the Repository to HACS**:
   - In Home Assistant, navigate to **HACS > Integrations**.
   - Click the **"+"** button to add a new repository.
   - Enter the repository URL: `https://github.com/Chuffnugget/volcano_integration`.
   - Select **Integration** as the category.

3. **Install the Integration**:
   - After adding, find **Volcano Integration** in the HACS Integrations list.
   - Click **Install**.

4. **Restart Home Assistant**:
   - After installation, restart Home Assistant to activate the integration.

5. **Configure the Integration**:
   - Navigate to **Settings > Devices & Services**, find **Volcano Integration**, and follow the setup instructions. The configuration menu will scan for Bluetooth devices, displaying a list. Simply select your Volcano Vaporizer and the setup will complete.

### Manual Installation

1. **Download the Integration**:
   - Clone or download the repository from GitHub: [GitHub Repository](https://github.com/Chuffnugget/volcano_integration).

2. **Place in Custom Components**:
   - Extract the files and place the `volcano_integration` folder in the `custom_components` directory within your Home Assistant configuration directory.

3. **Install Dependencies**:
   - Ensure the required dependencies (e.g., `bleak>=0.20.0`) are installed. Home Assistant should handle this automatically.

4. **Restart Home Assistant**:
   - After placing the files, restart Home Assistant.

5. **Add the Integration**:
   - Navigate to **Settings > Devices & Services > Add Integration**, search for "Volcano Integration," and follow the setup instructions.

---

## Usage

### Entities

- **Sensors**:
  - **Current Temperature**: Displays the current temperature of the vaporizer.
  - **Heat Status**: Shows whether the heater is **ON**, **OFF**, or in an unknown state.
  - **Pump Status**: Indicates if the pump is **ON**, **OFF**, or in an unknown state.
  - **Bluetooth Status**: Displays the current Bluetooth connection status.
  - **BLE Firmware Version**: Shows the BLE firmware version of the device.
  - **Serial Number**: Displays the device's serial number.
  - **Firmware Version**: Shows the device's firmware version.
  - **Auto Shutoff**: Indicates whether auto shutoff is enabled.
  - **LED Brightness**: Displays the current LED brightness level.
  - **Hours of Operation**: Tracks the total hours the device has been in operation.
  - **Minutes of Operation**: Tracks the total minutes the device has been in operation.

- **Switches**:
  - **Heat**: Turns the heater **ON** or **OFF**.
  - **Pump**: Turns the pump **ON** or **OFF**.
  - **Auto Shutoff**: Enables or disables the auto shutoff feature.
  - **Vibration**: Enables or disables the vibration feature.
  - **Connection**: Connects or disconnects the vaporizer from Home Assistant.

- **Numbers**:
  - **Heater Temperature Setpoint**: Allows setting the desired temperature between 40°C and 230°C.
  - **LED Brightness**: Adjusts the LED brightness between 0% and 100%.
  - **Auto Shutoff Setting**: Sets the auto shutoff duration in minutes (30-360).

### Services

- `volcano_integration.connect`: Connect to the vaporizer.
- `volcano_integration.disconnect`: Disconnect from the vaporizer.
- `volcano_integration.set_temperature`: Set the heater temperature.
  - **Parameters**:
    - `temperature` (optional): The target temperature in °C (40-230).
    - `percentage` (optional): The target temperature as a percentage (0-100%).
    - `wait_until_reached` (optional, default: true): Whether to block until the target temperature is reached.
- `volcano_integration.set_led_brightness`: Set the LED brightness.
  - **Parameters**:
    - `brightness` (required): The LED brightness percentage (0-100%).
- `volcano_integration.set_auto_shutoff`: Enable or disable auto shutoff.
  - **Parameters**:
    - `enabled` (required): Set to true to enable auto shutoff, false to disable.
- `volcano_integration.set_auto_shutoff_setting`: Set the auto shutoff time in minutes.
  - **Parameters**:
    - `minutes` (required): The duration in minutes before auto shutoff is triggered (30-360).
- `volcano_integration.set_vibration`: Enable or disable vibration.
  - **Parameters**:
    - `enabled` (required): Set to true to enable vibration, false to disable.
