"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory  # Imported EntityCategory
from . import DOMAIN
from .const import (
    BT_STATUS_CONNECTED,
    BT_STATUS_DISCONNECTED,
    UUID_BLE_FIRMWARE_VERSION,
    UUID_SERIAL_NUMBER,
    UUID_FIRMWARE_VERSION,
    UUID_AUTO_SHUT_OFF,
    UUID_LED_BRIGHTNESS,
    UUID_HOURS_OF_OPERATION,
    UUID_MINUTES_OF_OPERATION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(manager, entry),
        VolcanoHeatStatusSensor(manager, entry),
        VolcanoPumpStatusSensor(manager, entry),
        VolcanoBTStatusSensor(manager, entry),
        VolcanoBLEFirmwareVersionSensor(manager, entry),        # New Sensor
        VolcanoSerialNumberSensor(manager, entry),               # New Sensor
        VolcanoFirmwareVersionSensor(manager, entry),            # New Sensor
        VolcanoAutoShutOffSensor(manager, entry),                # New Sensor
        VolcanoLEDBrightnessSensor(manager, entry),              # New Sensor
        VolcanoHoursOfOperationSensor(manager, entry),           # New Sensor
        VolcanoMinutesOfOperationSensor(manager, entry),         # New Sensor
    ]
    async_add_entities(entities)


class VolcanoBaseSensor(SensorEntity):
    """Base sensor that registers/unregisters with the VolcanoBTManager."""

    def __init__(self, manager, config_entry):
        super().__init__()
        self._manager = manager
        self._config_entry = config_entry

    async def async_added_to_hass(self):
        _LOGGER.debug("%s: added to hass -> registering sensor.", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        _LOGGER.debug("%s: removing from hass -> unregistering sensor.", type(self).__name__)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor (°C)."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = f"volcano_current_temperature_{self._manager.bt_address}"
        self._attr_icon = "mdi:thermometer"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.current_temperature
        else:
            val = 0.0  # Default temperature when disconnected
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


class VolcanoHeatStatusSensor(VolcanoBaseSensor):
    """Heat Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Heat Status"
        self._attr_unique_id = f"volcano_heat_status_{self._manager.bt_address}"
        self._attr_icon = "mdi:fire"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.heat_state
        else:
            val = "OFF"  # Default heat status when disconnected
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


class VolcanoPumpStatusSensor(VolcanoBaseSensor):
    """Pump Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Pump Status"
        self._attr_unique_id = f"volcano_pump_status_{self._manager.bt_address}"
        self._attr_icon = "mdi:air-purifier"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.pump_state
        else:
            val = "OFF"  # Default pump status when disconnected
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor that shows the current Bluetooth status/error string."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = f"volcano_bt_status_{self._manager.bt_address}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        # Always show the BT Status sensor
        return True


# New Sensor: BLE Firmware Version
class VolcanoBLEFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the BLE Firmware Version."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano BLE Firmware Version"
        self._attr_unique_id = f"volcano_ble_firmware_version_{self._manager.bt_address}"
        self._attr_icon = "mdi:information"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.ble_firmware_version
        else:
            val = "Not Connected"  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: Serial Number
class VolcanoSerialNumberSensor(VolcanoBaseSensor):
    """Sensor to display the Serial Number."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Serial Number"
        self._attr_unique_id = f"volcano_serial_number_{self._manager.bt_address}"
        self._attr_icon = "mdi:card-account-details"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.serial_number
        else:
            val = "Not Connected"  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: Firmware Version
class VolcanoFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the Volcano Firmware Version."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Firmware Version"
        self._attr_unique_id = f"volcano_firmware_version_{self._manager.bt_address}"
        self._attr_icon = "mdi:information-outline"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.firmware_version
        else:
            val = "Not Connected"  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: Auto Shutoff
class VolcanoAutoShutOffSensor(VolcanoBaseSensor):
    """Sensor to display the Auto Shutoff status."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Auto Shutoff"
        self._attr_unique_id = f"volcano_auto_shutoff_{self._manager.bt_address}"
        self._attr_icon = "mdi:timer"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.auto_shut_off
        else:
            val = "OFF"  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: LED Brightness
class VolcanoLEDBrightnessSensor(VolcanoBaseSensor):
    """Sensor to display the LED Brightness."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = f"volcano_led_brightness_{self._manager.bt_address}"
        self._attr_icon = "mdi:brightness-5"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.led_brightness
        else:
            val = 100  # Default brightness when disconnected
        _LOGGER.debug("%s: native_value -> '%s%%'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: Hours of Operation
class VolcanoHoursOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Hours of Operation."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Hours of Operation"
        self._attr_unique_id = f"volcano_hours_of_operation_{self._manager.bt_address}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.hours_of_operation
        else:
            val = 0  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s' hours", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True


# New Sensor: Minutes of Operation
class VolcanoMinutesOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Minutes of Operation."""

    def __init__(self, manager, config_entry):
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Minutes of Operation"
        self._attr_unique_id = f"volcano_minutes_of_operation_{self._manager.bt_address}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = None  # Generic sensor
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Categorized as Diagnostic
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            val = self._manager.minutes_of_operation
        else:
            val = 0  # Default value when disconnected
        _LOGGER.debug("%s: native_value -> '%s' minutes", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available, shows default when disconnected."""
        return True
