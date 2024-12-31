"""Platform for sensor integration with extra debug logging."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(manager),
        VolcanoFanHeatControlSensor(manager),
        VolcanoBTStatusSensor(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseSensor(SensorEntity):
    """
    Base sensor that handles registration/unregistration with the VolcanoBTManager.
    Also includes logging for debug purposes.
    """

    def __init__(self, manager):
        self._manager = manager
        # We won't set _attr_name, _attr_unique_id, etc. here;
        # child classes define them.
        _LOGGER.debug("%s: __init__ called (manager=%s)", type(self).__name__, manager)

    async def async_added_to_hass(self):
        """Register with the manager for immediate update notifications."""
        _LOGGER.debug("%s: async_added_to_hass -> registering with manager.", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister when removed."""
        _LOGGER.debug("%s: async_will_remove_from_hass -> unregistering from manager.", type(self).__name__)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor for the Volcano device, with extra logging."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        _LOGGER.debug("%s: __init__ (name=%s, unique_id=%s)",
                      type(self).__name__, self._attr_name, self._attr_unique_id)

    @property
    def native_value(self):
        """Return the current temperature from the manager."""
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Optional: Only 'available' if BT is connected."""
        is_avail = (self._manager.bt_status == "CONNECTED")
        _LOGGER.debug("%s: available -> %s (bt_status=%s)",
                      type(self).__name__, is_avail, self._manager.bt_status)
        return is_avail


class VolcanoFanHeatControlSensor(VolcanoBaseSensor):
    """Sensor for the Volcano's Fan/Heat Control notifications, with extra logging."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        _LOGGER.debug("%s: __init__ (name=%s, unique_id=%s)",
                      type(self).__name__, self._attr_name, self._attr_unique_id)

    @property
    def native_value(self):
        """Return the last fan/heat notification text from the manager."""
        val = self._manager.fan_heat_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Only 'available' if BT is connected."""
        is_avail = (self._manager.bt_status == "CONNECTED")
        _LOGGER.debug("%s: available -> %s (bt_status=%s)",
                      type(self).__name__, is_avail, self._manager.bt_status)
        return is_avail


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor to display the current Bluetooth status/error string, with extra logging."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        _LOGGER.debug("%s: __init__ (name=%s, unique_id=%s)",
                      type(self).__name__, self._attr_name, self._attr_unique_id)

    @property
    def native_value(self):
        """Return the manager's current bt_status."""
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """
        We keep this sensor always available to display errors/disconnected states.
        If you wanted it 'unavailable' when disconnected, you could do so similarly.
        """
        _LOGGER.debug("%s: available -> True (always)", type(self).__name__)
        return True
