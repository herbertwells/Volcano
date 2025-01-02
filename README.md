
# Volcano Integration for Home Assistant

Control and monitor your **Storz & Bickel Volcano Hybrid Vaporizer** directly from Home Assistant with this custom integration. Enjoy seamless automation, real-time updates, and convenient control of your vaporizer’s key features.

## Features

- **Set Heater Temperature**: Adjust the target temperature (40–230°C) with precision.
- **Control the Pump and Heater**: Turn the pump and heater on or off.
- **Real-Time Status Monitoring**:
  - Current temperature
  - Heater status (ON/OFF/UNKNOWN)
  - Pump status (ON/OFF/UNKNOWN)
  - Bluetooth connection status (DISCONNECTED/CONNECTING/CONNECTED/ERROR)

## Installation

1. **Download and Add Files**:
   - Clone or download this repository.
   - Place the `volcano_integration` folder into your Home Assistant `custom_components` directory.

2. **Restart Home Assistant**:
   - Go to **Settings** > **System** > **Restart**.

3. **Add the Integration**:
   - Navigate to **Settings** > **Devices & Services**.
   - Click **Add Integration** and search for `Volcano Integration`.

4. **Configure**:
   - Provide the Bluetooth address for your Volcano Vaporizer during setup.

## Key Entities

### Sensors
- **Current Temperature**: Displays the vaporizer’s real-time temperature.
- **Heater Status**: Indicates the heater state (`ON`, `OFF`, or `UNKNOWN`).
- **Pump Status**: Shows the pump state (`ON`, `OFF`, or `UNKNOWN`).
- **Bluetooth Status**: Displays the connection status.

### Controls
- **Heater Temperature Setpoint**: Adjust the target temperature.
- **Pump and Heater Buttons**: Control the pump and heater directly.

## Automate Your Experience

Leverage Home Assistant automations to optimize your Volcano experience. For example:
- Automatically preheat your vaporizer in the morning.
- Turn off the pump and heater when your session ends.

## Troubleshooting

- Ensure the vaporizer’s Bluetooth is active and discoverable.
- Check the logs in Home Assistant for any connection errors.
- Verify the Bluetooth address matches your device.

## Contributing

We welcome contributions! Submit a pull request or open an issue on our [GitHub repository](https://github.com/Chuffnugget/volcano_integration).
