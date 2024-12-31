"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VolcanoCurrentTempSensor(manager),         # NEW numeric temperature sensor
        VolcanoFanHeatControlSensor(manager),
        VolcanoBTStatusSensor(manager),
    ], update_before_add=True)


class VolcanoCurrentTempSensor(SensorEntity):
    """Numeric Temperature Sensor for the Volcano device."""

    def __init__(self, manager):
        """Initialize the numeric temperature sensor."""
        self._manager = manager
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        # Tell HA this is a temperature sensor (improves UI, graphs, etc.)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        # New recommended approach for units:
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        # Not strictly needed, but if you want it in Diagnostics or none:
        # self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self._state = None

    @property
    def native_value(self):
        """Return the current temperature as a float in Celsius."""
        return self._state

    async def async_update(self):
        """Refresh the sensor state from the BT manager."""
        self._state = self._manager.current_temperature
        _LOGGER.debug("VolcanoCurrentTempSensor updated to: %s °C", self._state)


class VolcanoFanHeatControlSensor(SensorEntity):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._state = None

    @property
    def native_value(self):
        """Return the latest fan/heat notification string."""
        return self._state

    async def async_update(self):
        """Pull the last notification from the BT manager."""
        self._state = self._manager.fan_heat_status
        _LOGGER.debug("VolcanoFanHeatControlSensor updated to: %s", self._state)


class VolcanoBTStatusSensor(SensorEntity):
    """Sensor reflecting the current Bluetooth connectivity status."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._state = None

    @property
    def native_value(self):
        """Return the manager's current Bluetooth status string."""
        return self._state

    async def async_update(self):
        """Pull the BT status from the manager."""
        self._state = self._manager.bt_status
        _LOGGER.debug("VolcanoBTStatusSensor updated to: %s", self._state)
