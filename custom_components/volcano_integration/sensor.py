"""sensor.py - Volcano Integration for Home Assistant."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from .const import (
    DOMAIN,
    BT_STATUS_CONNECTED,
    UUID_BLE_FIRMWARE_VERSION,
    UUID_SERIAL_NUMBER,
    UUID_FIRMWARE_VERSION,
    UUID_LED_BRIGHTNESS,
    UUID_HOURS_OF_OPERATION,
    UUID_MINUTES_OF_OPERATION,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    # Removed VolcanoAutoShutOffSensor from this list.
    entities = [
        VolcanoCurrentTempSensor(manager, entry),
        VolcanoHeatStatusSensor(manager, entry),
        VolcanoPumpStatusSensor(manager, entry),
        VolcanoBTStatusSensor(manager, entry),
        VolcanoBLEFirmwareVersionSensor(manager, entry),
        VolcanoSerialNumberSensor(manager, entry),
        VolcanoFirmwareVersionSensor(manager, entry),
        VolcanoLEDBrightnessSensor(manager, entry),
        VolcanoHoursOfOperationSensor(manager, entry),
        VolcanoMinutesOfOperationSensor(manager, entry),
    ]
    async_add_entities(entities)

class VolcanoBaseSensor(SensorEntity):
    """Base sensor that registers/unregisters with the VolcanoBTManager."""

    def __init__(self, manager, config_entry):
        """Initialize the base sensor with manager and config entry."""
        super().__init__()
        self._manager = manager
        self._config_entry = config_entry

    async def async_added_to_hass(self):
        """Register the sensor for state updates."""
        _LOGGER.debug("%s: added to hass -> registering sensor.", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister the sensor to stop receiving updates."""
        _LOGGER.debug("%s: removing from hass -> unregistering sensor.", type(self).__name__)
        self._manager.unregister_sensor(self)

class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor (°C)."""

    def __init__(self, manager, config_entry):
        """Initialize the Current Temperature sensor."""
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
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the current temperature."""
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

class VolcanoHeatStatusSensor(VolcanoBaseSensor):
    """Heat Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager, config_entry):
        """Initialize the Heat Status sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Heat Status"
        self._attr_unique_id = f"volcano_heat_status_{self._manager.bt_address}"
        self._attr_icon = "mdi:fire"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the current heat status."""
        val = self._manager.heat_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

class VolcanoPumpStatusSensor(VolcanoBaseSensor):
    """Pump Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager, config_entry):
        """Initialize the Pump Status sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Pump Status"
        self._attr_unique_id = f"volcano_pump_status_{self._manager.bt_address}"
        self._attr_icon = "mdi:air-purifier"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the current pump status."""
        val = self._manager.pump_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor that shows the current Bluetooth status/error string."""

    def __init__(self, manager, config_entry):
        """Initialize the Bluetooth Status sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = f"volcano_bt_status_{self._manager.bt_address}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the current Bluetooth status."""
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Always available as it shows Bluetooth status."""
        return True

class VolcanoBLEFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the BLE Firmware Version."""

    def __init__(self, manager, config_entry):
        """Initialize the BLE Firmware Version sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano BLE Firmware Version"
        self._attr_unique_id = f"volcano_ble_firmware_version_{self._manager.bt_address}"
        self._attr_icon = "mdi:information"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the BLE firmware version."""
        val = self._manager.ble_firmware_version
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and firmware version is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.ble_firmware_version is not None)

class VolcanoSerialNumberSensor(VolcanoBaseSensor):
    """Sensor to display the Serial Number."""

    def __init__(self, manager, config_entry):
        """Initialize the Serial Number sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Serial Number"
        self._attr_unique_id = f"volcano_serial_number_{self._manager.bt_address}"
        self._attr_icon = "mdi:card-account-details"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the serial number."""
        val = self._manager.serial_number
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and serial number is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.serial_number is not None)

class VolcanoFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the Volcano Firmware Version."""

    def __init__(self, manager, config_entry):
        """Initialize the Firmware Version sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Firmware Version"
        self._attr_unique_id = f"volcano_firmware_version_{self._manager.bt_address}"
        self._attr_icon = "mdi:information-outline"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the firmware version."""
        val = self._manager.firmware_version
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and firmware version is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.firmware_version is not None)

class VolcanoLEDBrightnessSensor(VolcanoBaseSensor):
    """Sensor to display the LED Brightness."""

    def __init__(self, manager, config_entry):
        """Initialize the LED Brightness sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = f"volcano_led_brightness_{self._manager.bt_address}"
        self._attr_icon = "mdi:brightness-5"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the LED brightness."""
        val = self._manager.led_brightness
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and LED brightness is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.led_brightness is not None)

class VolcanoHoursOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Hours of Operation."""

    def __init__(self, manager, config_entry):
        """Initialize the Hours of Operation sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Hours of Operation"
        self._attr_unique_id = f"volcano_hours_of_operation_{self._manager.bt_address}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the hours of operation."""
        val = self._manager.hours_of_operation
        _LOGGER.debug("%s: native_value -> '%s' hours", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and hours of operation is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.hours_of_operation is not None)

class VolcanoMinutesOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Minutes of Operation."""

    def __init__(self, manager, config_entry):
        """Initialize the Minutes of Operation sensor."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Minutes of Operation"
        self._attr_unique_id = f"volcano_minutes_of_operation_{self._manager.bt_address}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the minutes of operation."""
        val = self._manager.minutes_of_operation
        _LOGGER.debug("%s: native_value -> '%s' minutes", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only when Bluetooth is connected and minutes of operation is known."""
        return (self._manager.bt_status == BT_STATUS_CONNECTED and self._manager.minutes_of_operation is not None)
