"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        VolcanoCurrentTempSensor(manager),
        VolcanoFanHeatControlSensor(manager)
    ], update_before_add=True)


class VolcanoCurrentTempSensor(SensorEntity):
    """Sensor for the Volcano's current temperature."""

    def __init__(self, manager):
        self._manager = manager
        self._state = None
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_unit_of_measurement = TEMP_CELSIUS
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current temperature."""
        return self._state

    async def async_update(self):
        """Update the sensor state from the BT manager."""
        self._state = self._manager.current_temperature
        _LOGGER.debug("VolcanoCurrentTempSensor updated to: %s", self._state)


class VolcanoFanHeatControlSensor(SensorEntity):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, manager):
        self._manager = manager
        self._state = None
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the last received Fan/Heat Control string."""
        return self._state

    async def async_update(self):
        """Update the sensor state from the BT manager."""
        self._state = self._manager.fan_heat_status
        _LOGGER.debug("VolcanoFanHeatControlSensor updated to: %s", self._state)
