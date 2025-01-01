"""Platform for sensor integration, now with pump instead of fan and RSSI support."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature, SIGNAL_STRENGTH_DECIBELS

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(manager),
        VolcanoHeatSensor(manager),
        VolcanoPumpSensor(manager),  # Changed from Fan to Pump
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

    @property
    def native_value(self):
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


class VolcanoHeatSensor(VolcanoBaseSensor):
    """Heat state (ON/OFF/UNKNOWN)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat"
        self._attr_unique_id = "volcano_heat"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        val = self._manager.heat_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


class VolcanoPumpSensor(VolcanoBaseSensor):
    """Pump state (ON/OFF/UNKNOWN)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump"
        self._attr_unique_id = "volcano_pump"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
        # No built-in device_class for RSSI, specify unit
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS

    @property
    def native_value(self):
        val = self._manager.rssi
        _LOGGER.debug("%s: native_value -> %s dBm", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Available only if BLE is connected."""
        return (self._manager.bt_status == "CONNECTED")
