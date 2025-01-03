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
    """Numeric Temperature Sensor (°C)."""

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
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

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
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.heat_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

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
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.pump_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

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
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        return True


class VolcanoFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor for Volcano Firmware Version."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Firmware Version"
        self._attr_unique_id = "volcano_firmware_version"
        self._attr_icon = "mdi:update"

    @property
    def native_value(self):
        return self._manager.firmware_version or "UNKNOWN"


class VolcanoSerialNumberSensor(VolcanoBaseSensor):
    """Sensor for Volcano Serial Number."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Serial Number"
        self._attr_unique_id = "volcano_serial_number"
        self._attr_icon = "mdi:barcode"

    @property
    def native_value(self):
        return self._manager.serial_number or "UNKNOWN"


class VolcanoBLEFirmwareVersionSensor(VolcanoBaseSensor):
    """Sensor for Volcano BLE Firmware Version."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano BLE Firmware Version"
        self._attr_unique_id = "volcano_ble_firmware_version"
        self._attr_icon = "mdi:chip"

    @property
    def native_value(self):
        return self._manager.ble_firmware_version or "UNKNOWN"


class VolcanoAutoShutOffSensor(VolcanoBaseSensor):
    """Sensor for Volcano Auto Shut Off."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Auto Shut Off"
        self._attr_unique_id = "volcano_auto_shut_off"
        self._attr_icon = "mdi:timer-off"

    @property
    def native_value(self):
        return self._manager.auto_shut_off or "UNKNOWN"


class VolcanoAutoShutOffSettingSensor(VolcanoBaseSensor):
    """Sensor for Volcano Auto Shut Off Setting."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Auto Shut Off Setting"
        self._attr_unique_id = "volcano_auto_shut_off_setting"
        self._attr_icon = "mdi:timer-settings"

    @property
    def native_value(self):
        return self._manager.auto_shut_off_setting or "UNKNOWN"


class VolcanoLEDBrightnessSensor(VolcanoBaseSensor):
    """Sensor for Volcano LED Brightness."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = "volcano_led_brightness"
        self._attr_icon = "mdi:brightness-6"

    @property
    def native_value(self):
        return self._manager.led_brightness or "UNKNOWN"
