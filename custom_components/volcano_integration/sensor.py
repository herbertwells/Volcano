"""Platform for sensor integration, creating separate sensors for heat, fan, temperature, and BT status."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up Volcano sensors for a config entry.
    """
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(manager),
        VolcanoHeatSensor(manager),
        VolcanoFanSensor(manager),
        VolcanoBTStatusSensor(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseSensor(SensorEntity):
    """Base sensor that registers with the VolcanoBTManager."""

    def __init__(self, manager):
        self._manager = manager

    async def async_added_to_hass(self):
        _LOGGER.debug("%s: added to hass -> registering sensor.", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        _LOGGER.debug("%s: removing from hass -> unregistering sensor.", type(self).__name__)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor for the Volcano device (°C)."""

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
    """Sensor for the Volcano's Heat state (ON/OFF)."""

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


class VolcanoFanSensor(VolcanoBaseSensor):
    """Sensor for the Volcano's Fan state (ON/OFF)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Fan"
        self._attr_unique_id = "volcano_fan"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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

    @property
    def native_value(self):
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        # Always show the BT Status sensor, so user can see errors/disconnect states
        return True
