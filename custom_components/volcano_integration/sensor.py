"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from .const import (
    DOMAIN,
    BT_DEVICE_ADDRESS,
    UUID_BLE_FIRMWARE_VERSION,
    UUID_SERIAL_NUMBER,
    UUID_FIRMWARE_VERSION,
    UUID_AUTO_SHUT_OFF,
    UUID_AUTO_SHUT_OFF_SETTING,
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
        VolcanoCurrentTempSensor(manager),
        VolcanoHeatStatusSensor(manager),
        VolcanoPumpStatusSensor(manager),
        VolcanoBTStatusSensor(manager),
        VolcanoBLEFirmwareVersionSensor(manager),
        VolcanoSerialNumberSensor(manager),
        VolcanoFirmwareVersionSensor(manager),
        VolcanoAutoShutOffSensor(manager),
        VolcanoAutoShutOffSettingSensor(manager),
        VolcanoLEDBrightnessSensor(manager),
        VolcanoHoursOfOperationSensor(manager),
        VolcanoMinutesOfOperationSensor(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseSensor(SensorEntity):
    """Base sensor for static attributes."""

    def __init__(self, manager, name, unique_id):
        self._manager = manager
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def available(self):
        """Always available for static attributes."""
        return True


# Sensors for live attributes

class VolcanoCurrentTempSensor(SensorEntity):
    """Sensor for current temperature."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_icon = "mdi:thermometer"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        return self._manager.current_temperature

    @property
    def available(self):
        return self._manager.bt_status == "CONNECTED"


class VolcanoHeatStatusSensor(SensorEntity):
    """Sensor for heat status."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Heat Status"
        self._attr_unique_id = "volcano_heat_status"
        self._attr_icon = "mdi:fire"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        return self._manager.heat_state

    @property
    def available(self):
        return self._manager.bt_status == "CONNECTED"


class VolcanoPumpStatusSensor(SensorEntity):
    """Sensor for pump status."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Pump Status"
        self._attr_unique_id = "volcano_pump_status"
        self._attr_icon = "mdi:air-purifier"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        return self._manager.pump_state

    @property
    def available(self):
        return self._manager.bt_status == "CONNECTED"


class VolcanoBTStatusSensor(SensorEntity):
    """Sensor for Bluetooth status."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        return self._manager.bt_status

    @property
    def available(self):
        return True


# Sensors for static attributes

class VolcanoBLEFirmwareVersionSensor(VolcanoBaseSensor):
    """BLE Firmware Version Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "BLE Firmware Version", "volcano_ble_firmware_version")

    @property
    def native_value(self):
        return self._manager.ble_firmware_version or "UNKNOWN"


class VolcanoSerialNumberSensor(VolcanoBaseSensor):
    """Serial Number Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Serial Number", "volcano_serial_number")

    @property
    def native_value(self):
        return self._manager.serial_number or "UNKNOWN"


class VolcanoFirmwareVersionSensor(VolcanoBaseSensor):
    """Volcano Firmware Version Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Firmware Version", "volcano_firmware_version")

    @property
    def native_value(self):
        return self._manager.firmware_version or "UNKNOWN"


class VolcanoAutoShutOffSensor(VolcanoBaseSensor):
    """Auto Shutoff Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Auto Shutoff", "volcano_auto_shutoff")

    @property
    def native_value(self):
        return "Enabled" if self._manager.auto_shut_off == b"\x01" else "Disabled"


class VolcanoAutoShutOffSettingSensor(VolcanoBaseSensor):
    """Auto Shutoff Setting Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Auto Shutoff Setting", "volcano_auto_shutoff_setting")

    @property
    def native_value(self):
        seconds = int.from_bytes(self._manager.auto_shut_off_setting or b"\x00", "little")
        return f"{seconds // 60} minutes"


class VolcanoLEDBrightnessSensor(VolcanoBaseSensor):
    """LED Brightness Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "LED Brightness", "volcano_led_brightness")

    @property
    def native_value(self):
        return int.from_bytes(self._manager.led_brightness or b"\x00", "little")


class VolcanoHoursOfOperationSensor(VolcanoBaseSensor):
    """Hours of Operation Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Hours of Operation", "volcano_hours_of_operation")

    @property
    def native_value(self):
        return int.from_bytes(self._manager.hours_of_operation or b"\x00", "little")


class VolcanoMinutesOfOperationSensor(VolcanoBaseSensor):
    """Minutes of Operation Sensor."""

    def __init__(self, manager):
        super().__init__(manager, "Minutes of Operation", "volcano_minutes_of_operation")

    @property
    def native_value(self):
        return int.from_bytes(self._manager.minutes_of_operation or b"\x00", "little")
