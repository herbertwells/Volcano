"""Platform for sensor integration."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VolcanoRawTempSensor(manager),
        VolcanoFanHeatControlSensor(manager),
    ], update_before_add=True)


class VolcanoRawTempSensor(SensorEntity):
    """Sensor that just shows the raw temperature data as a string."""

    def __init__(self, manager):
        self._manager = manager
        self._state = None

        self._attr_name = "Volcano Temperature (Raw Data)"
        self._attr_unique_id = "volcano_temp_raw"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the raw temperature data in hex form."""
        return self._state

    async def async_update(self):
        """Pull the latest raw data from the BT manager."""
        self._state = self._manager.current_temperature_raw
        _LOGGER.debug("VolcanoRawTempSensor updated to: %s", self._state)


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
        """Return the latest fan/heat notification string."""
        return self._state

    async def async_update(self):
        """Pull the last notification from the BT manager."""
        self._state = self._manager.fan_heat_status
        _LOGGER.debug("VolcanoFanHeatControlSensor updated to: %s", self._state)
