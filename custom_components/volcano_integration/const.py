"""const.py - Volcano Integration for Home Assistant."""

import voluptuous as vol
from homeassistant.helpers import selector

DOMAIN = "volcano_integration"

# Possible Bluetooth status strings
BT_STATUS_DISCONNECTED = "DISCONNECTED"
BT_STATUS_CONNECTING = "CONNECTING"
BT_STATUS_CONNECTED = "CONNECTED"
BT_STATUS_ERROR = "ERROR"

# Vibration Bitmask Constants
VIBRATION_BIT_MASK = 0x0400  # Bit 10

# Control Register UUIDs
UUID_PUMP_NOTIFICATIONS = "1010000c-5354-4f52-5a26-4249434b454c"  # Pump Notifications - WARNING! Duplicate
REGISTER1_UUID = "1010000c-5354-4f52-5a26-4249434b454c"        # Pump Notifications - WARNING! Duplicate
REGISTER2_UUID = "1010000d-5354-4f52-5a26-4249434b454c"        # [Specify Purpose]
REGISTER3_UUID = "1010000e-5354-4f52-5a26-4249434b454c"        # Vibration Control

# UUIDs for GATT Characteristics
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"             # Current Temperature
UUID_PUMP_ON = "10110013-5354-4f52-5a26-4249434b454c"
UUID_PUMP_OFF = "10110014-5354-4f52-5a26-4249434b454c"
UUID_HEAT_ON = "1011000f-5354-4f52-5a26-4249434b454c"
UUID_HEAT_OFF = "10110010-5354-4f52-5a26-4249434b454c"
UUID_HEATER_SETPOINT = "10110003-5354-4f52-5a26-4249434b454c"

# Static attributes
UUID_BLE_FIRMWARE_VERSION = "10100004-5354-4f52-5a26-4249434b454c"    # BLE Firmware Version
UUID_SERIAL_NUMBER = "10100008-5354-4f52-5a26-4249434b454c"         # Serial Number
UUID_FIRMWARE_VERSION = "10100003-5354-4f52-5a26-4249434b454c"      # Volcano Firmware Version
UUID_AUTO_SHUT_OFF = "1011000c-5354-4f52-5a26-4249434b454c"         # Auto Shutoff
UUID_AUTO_SHUT_OFF_SETTING = "1011000d-5354-4f52-5a26-4249434b454c" # Auto Shutoff Setting
UUID_LED_BRIGHTNESS = "10110005-5354-4f52-5a26-4249434b454c"       # LED Brightness
UUID_HOURS_OF_OPERATION = "10110015-5354-4f52-5a26-4249434b454c"   # Hours of Operation
UUID_MINUTES_OF_OPERATION = "10110016-5354-4f52-5a26-4249434b454c" # Minutes of Operation
UUID_VIBRATION = "1010000e-5354-4f52-5a26-4249434b454c"           # Vibration Control

# Temperature Control Constants
MIN_TEMP = 40.0        # Minimum Temperature in °C
MAX_TEMP = 230.0       # Maximum Temperature in °C
DEFAULT_TEMP = 170.0   # Default Temperature in °C
STEP = 1.0             # Temperature Step

# LED Brightness Constants
MIN_BRIGHTNESS = 0    # Minimum LED Brightness (%)
MAX_BRIGHTNESS = 100  # Maximum LED Brightness (%)
DEFAULT_BRIGHTNESS = 20  # Default LED Brightness (%)

# Auto Shutoff Settings
MIN_AUTO_SHUTOFF = 1    # Minimum Auto Shutoff Time (minutes)
MAX_AUTO_SHUTOFF = 240  # Maximum Auto Shutoff Time (minutes)
DEFAULT_AUTO_SHUTOFF = 30  # Default Auto Shutoff Time (minutes)

# Hours and Minutes of Operation
DEFAULT_HOURS_OF_OPERATION = 0
DEFAULT_MINUTES_OF_OPERATION = 0

# Refresh Option Value for Config Flow
REFRESH_OPTION_VALUE = "REFRESH_DEVICE_LIST"

# Service Names
SERVICE_CONNECT = "connect"
SERVICE_DISCONNECT = "disconnect"
SERVICE_PUMP_ON = "pump_on"
SERVICE_PUMP_OFF = "pump_off"
SERVICE_HEAT_ON = "heat_on"
SERVICE_HEAT_OFF = "heat_off"
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_AUTO_SHUTOFF_SETTING = "set_auto_shutoff_setting"
SERVICE_SET_LED_BRIGHTNESS = "set_led_brightness"

# Service Descriptions
SERVICE_DESCRIPTIONS = {
    SERVICE_CONNECT: {
        "description": "Connect to the Volcano device.",
        "fields": {
            "wait_until_connected": {
                "name": "Wait Until Connected",
                "description": "Whether to block until the device is fully connected.",
                "required": False,
                "default": False,
                "selector": {
                    "boolean": {}
                },
            }
        },
    },
    SERVICE_DISCONNECT: {
        "description": "Disconnect from the Volcano device.",
        "fields": {},
    },
    SERVICE_PUMP_ON: {
        "description": "Turn the Volcano's pump on.",
        "fields": {},
    },
    SERVICE_PUMP_OFF: {
        "description": "Turn the Volcano's pump off.",
        "fields": {},
    },
    SERVICE_HEAT_ON: {
        "description": "Turn the Volcano's heater on.",
        "fields": {},
    },
    SERVICE_HEAT_OFF: {
        "description": "Turn the Volcano's heater off.",
        "fields": {},
    },
    SERVICE_SET_TEMPERATURE: {
        "description": "Set the temperature of the Volcano vaporizer.",
        "fields": {
            "temperature": {
                "name": "Temperature",
                "description": "The target temperature in °C (40-230).",
                "required": True,
                "example": 170,
                "selector": {
                    "number": {
                        "min": MIN_TEMP,
                        "max": MAX_TEMP,
                        "step": STEP,
                        "unit_of_measurement": "°C",
                    }
                },
            },
            "wait_until_reached": {
                "name": "Wait Until Reached",
                "description": "Whether to block until the target temperature is reached.",
                "required": True,
                "default": True,
                "selector": {
                    "boolean": {}
                },
            },
        },
    },
    SERVICE_SET_AUTO_SHUTOFF_SETTING: {
        "description": "Set the Auto Shutoff Setting for the Volcano in minutes.",
        "fields": {
            "minutes": {
                "name": "Minutes",
                "description": "Auto Shutoff delay, in minutes.",
                "required": True,
                "default": DEFAULT_AUTO_SHUTOFF,
                "selector": {
                    "number": {
                        "min": MIN_AUTO_SHUTOFF,
                        "max": MAX_AUTO_SHUTOFF,
                        "step": 1,
                        "unit_of_measurement": "min",
                    }
                },
            },
        },
    },
    SERVICE_SET_LED_BRIGHTNESS: {
        "description": "Set the LED Brightness of the Volcano (0-100).",
        "fields": {
            "brightness": {
                "name": "Brightness",
                "description": "The LED brightness percentage (0-100).",
                "required": True,
                "default": DEFAULT_BRIGHTNESS,
                "selector": {
                    "number": {
                        "min": MIN_BRIGHTNESS,
                        "max": MAX_BRIGHTNESS,
                        "step": 1,
                        "unit_of_measurement": "%",
                    }
                },
            },
        },
    },
}

# Define Service Schemas
CONNECT_SCHEMA = vol.Schema({
    vol.Optional("wait_until_connected", default=False): bool,
})

DISCONNECT_SCHEMA = vol.Schema({})

PUMP_ON_SCHEMA = vol.Schema({})

PUMP_OFF_SCHEMA = vol.Schema({})

HEAT_ON_SCHEMA = vol.Schema({})

HEAT_OFF_SCHEMA = vol.Schema({})

SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(min=MIN_TEMP, max=MAX_TEMP)),
    vol.Required("wait_until_reached", default=True): bool,
})

SET_AUTO_SHUTOFF_SCHEMA = vol.Schema({
    vol.Required("minutes", default=DEFAULT_AUTO_SHUTOFF): vol.All(vol.Coerce(int), vol.Range(min=MIN_AUTO_SHUTOFF, max=MAX_AUTO_SHUTOFF)),
})

SET_LED_BRIGHTNESS_SCHEMA = vol.Schema({
    vol.Required("brightness", default=DEFAULT_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=MIN_BRIGHTNESS, max=MAX_BRIGHTNESS)),
})
