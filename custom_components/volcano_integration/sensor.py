"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from . import DOMAIN
from .bluetooth_coordinator import BT_DEVICE_ADDRESS

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
    """Base sensor that registers/unregisters with the VolcanoBTManager."""

    def __init__(self, manager):
        super().__init__()
        self._manager = manager

    async def async_added_to_hass(self):
        _LOGGER.debug("%s: added to hass -> registering sensor.", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        _LOGGER.debug("%s: removing from hass -> unregistering sensor.", type(self).__name__)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor (\u00b0C)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Current Temperature"
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


class VolcanoHeatStatusSensor(VolcanoBaseSensor):
    """Heat Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat Status"
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


class VolcanoPumpStatusSensor(VolcanoBaseSensor):
    """Pump Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump Status"
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


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor that shows the current Bluetooth status/error string."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
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


class StaticValueSensor(VolcanoBaseSensor):
    """Base class for static value sensors."""

    def __init__(self, manager, name, unique_id):
        super().__init__(manager)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:information-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def available(self):
        return True


class VolcanoBLEFirmwareVersionSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "BLE Firmware Version", "volcano_ble_firmware_version")

    @property
    def native_value(self):
        return self._manager.ble_firmware_version or "UNKNOWN"


class VolcanoSerialNumberSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Serial Number", "volcano_serial_number")

    @property
    def native_value(self):
        return self._manager.serial_number or "UNKNOWN"


class VolcanoFirmwareVersionSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Firmware Version", "volcano_firmware_version")

    @property
    def native_value(self):
        return self._manager.firmware_version or "UNKNOWN"


class VolcanoAutoShutOffSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Auto Shut Off", "volcano_auto_shut_off")

    @property
    def native_value(self):
        return self._manager.auto_shut_off or "UNKNOWN"


class VolcanoAutoShutOffSettingSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Auto Shut Off Setting", "volcano_auto_shut_off_setting")

    @property
    def native_value(self):
        return self._manager.auto_shut_off_setting or "UNKNOWN"


class VolcanoLEDBrightnessSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "LED Brightness", "volcano_led_brightness")

    @property
    def native_value(self):
        return self._manager.led_brightness or "UNKNOWN"


class VolcanoHoursOfOperationSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Hours of Operation", "volcano_hours_of_operation")

    @property
    def native_value(self):
        return self._manager.hours_of_operation or "UNKNOWN"


class VolcanoMinutesOfOperationSensor(StaticValueSensor):
    def __init__(self, manager):
        super().__init__(manager, "Minutes of Operation", "volcano_minutes_of_operation")

    @property
    def native_value(self):
        return self._manager.minutes_of_operation or "UNKNOWN"
