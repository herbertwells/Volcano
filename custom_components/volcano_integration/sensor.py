"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import EntityCategory

from .bluetooth_coordinator import VolcanoBTManager
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Global reference to the manager. In a more advanced setup, you'd store this
# in hass.data with a custom domain key.
BT_MANAGER = None


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensors with static config."""
    global BT_MANAGER

    _LOGGER.debug("Setting up Volcano sensors (no config flow).")

    if not BT_MANAGER:
        _LOGGER.debug("Creating new VolcanoBTManager instance.")
        BT_MANAGER = VolcanoBTManager()
        BT_MANAGER.start(hass)

    # Create sensor entities and add them
    sensors = [
        VolcanoCurrentTempSensor(BT_MANAGER),
        VolcanoFanHeatControlSensor(BT_MANAGER),
    ]

    async_add_entities(sensors, update_before_add=True)


class VolcanoCurrentTempSensor(SensorEntity):
    """Sensor for the Volcano's current temperature."""

    def __init__(self, manager: VolcanoBTManager):
        self._manager = manager
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._state = None
        self._attr_unit_of_measurement = TEMP_CELSIUS
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current temperature."""
        return self._state

    async def async_update(self):
        """Update the sensor state from the manager."""
        self._state = self._manager.current_temperature
        _LOGGER.debug("CurrentTempSensor updated to: %s", self._state)


class VolcanoFanHeatControlSensor(SensorEntity):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, manager: VolcanoBTManager):
        self._manager = manager
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._state = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the last received Fan/Heat Control string."""
        return self._state

    async def async_update(self):
        """Update the sensor state from the manager."""
        self._state = self._manager.fan_heat_status
        _LOGGER.debug("FanHeatControlSensor updated to: %s", self._state)
