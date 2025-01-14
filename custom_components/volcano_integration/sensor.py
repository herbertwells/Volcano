"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory

from . import DOMAIN

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
        # VolcanoAutoShutOffSensor(manager, entry),  <-- REMOVED
        VolcanoLEDBrightnessSensor(manager, entry),
        VolcanoHoursOfOperationSensor(manager, entry),
        VolcanoMinutesOfOperationSensor(manager, entry),
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
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


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
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.heat_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


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
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.pump_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


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
            "sw_version": "1.0.0",
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


class VolcanoBLEFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the BLE Firmware Version."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.ble_firmware_version
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.ble_firmware_version is not None)


class VolcanoSerialNumberSensor(VolcanoBaseSensor):
    """Sensor to display the Serial Number."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.serial_number
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.serial_number is not None)


class VolcanoFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor to display the Volcano Firmware Version."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.firmware_version
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.firmware_version is not None)


# REMOVED VolcanoAutoShutOffSensor class and references.


class VolcanoLEDBrightnessSensor(VolcanoBaseSensor):
    """Sensor to display the LED Brightness."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.led_brightness
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.led_brightness is not None)


class VolcanoHoursOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Hours of Operation."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.hours_of_operation
        _LOGGER.debug("%s: native_value -> '%s' hours", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.hours_of_operation is not None)


class VolcanoMinutesOfOperationSensor(VolcanoBaseSensor):
    """Sensor to display the Minutes of Operation."""

    def __init__(self, manager, config_entry):
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
        val = self._manager.minutes_of_operation
        _LOGGER.debug("%s: native_value -> '%s' minutes", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED" and self._manager.minutes_of_operation is not None)
