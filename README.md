# Volcano Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![ha_version](https://img.shields.io/badge/Home%20Assistant-2023.8.0-blue.svg)](https://www.home-assistant.io)

A custom Home Assistant integration for controlling Storz & Bickel Volcano Hybrid vaporizers via Bluetooth LE.

## Features

- Temperature monitoring and control
- Pump and heater control
- LED brightness control
- Auto shutoff configuration
- Operating hours monitoring
- Firmware version info
- Serial number display

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "ADD"
6. Search for "Volcano Integration" in HACS
7. Click "Download"
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/volcano_integration` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Volcano Integration"
4. Follow the configuration steps

## Available Services

- `volcano_integration.connect`: Connect to the Volcano device
- `volcano_integration.disconnect`: Disconnect from the device
- `volcano_integration.pump_on`: Turn the pump on
- `volcano_integration.pump_off`: Turn the pump off
- `volcano_integration.heat_on`: Turn the heater on
- `volcano_integration.heat_off`: Turn the heater off
- `volcano_integration.set_temperature`: Set target temperature
- `volcano_integration.set_auto_shutoff_setting`: Configure auto shutoff time
- `volcano_integration.set_led_brightness`: Set LED brightness

## Support

For bugs and feature requests, please use the [GitHub Issues](https://github.com/Chuffnugget/volcano_integration/issues) page.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
