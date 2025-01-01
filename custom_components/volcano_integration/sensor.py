"""Platform for sensor integration, now with fan renamed and RSSI support."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature, SIGNAL_STRENGTH_DECIBELS

from . import DOMAIN
from .bluetooth_coordinator import BT_DEVICE_ADDRESS  # Kept import for device identifiers

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(manager),
        VolcanoHeatStatusSensor(manager),
        VolcanoFanStatusSensor(manager),
        VolcanoBTStatusSensor(manager),
        VolcanoRSSISensor(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseSensor(SensorEntity):
    """Base sensor that registers/unregisters with the VolcanoBTManager."""

    def __init__(self, manager):
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
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "YourManufacturer",  # Replace with actual manufacturer
            "model": "Volcano Model",           # Replace with actual model
            "sw_version": "1.0.0",             # Replace with actual software version
            "via_device": None,                # Replace if via another device
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

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat Status"
        self._attr_unique_id = "volcano_heat_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "YourManufacturer",
            "model": "Volcano Model",
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


class VolcanoFanStatusSensor(VolcanoBaseSensor):
    """Fan Status Sensor (ON/OFF/UNKNOWN)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Fan Status"
        self._attr_unique_id = "volcano_fan_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "YourManufacturer",
            "model": "Volcano Model",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.fan_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor that shows the current Bluetooth status/error string."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "YourManufacturer",
            "model": "Volcano Model",
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


class VolcanoRSSISensor(VolcanoBaseSensor):
    """Sensor that shows the device RSSI in dBm (updated every 60s)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano RSSI"
        self._attr_unique_id = "volcano_rssi"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "YourManufacturer",
            "model": "Volcano Model",
            "sw_version": "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        val = self._manager.rssi
        _LOGGER.debug("%s: native_value -> %s dBm", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only if BLE is connected."""
        return (self._manager.bt_status == "CONNECTED")
