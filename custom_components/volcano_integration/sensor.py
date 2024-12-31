"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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
    Base sensor that handles registration/unregistration with the manager.
    """

    def __init__(self, manager):
        self._manager = manager

    async def async_added_to_hass(self):
        """Register with the manager for immediate update notifications."""
        _LOGGER.debug("Registering %s with VolcanoBTManager", self.name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister when removed."""
        _LOGGER.debug("Unregistering %s from VolcanoBTManager", self.name)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor for the Volcano device."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Return the current temperature from the manager."""
        return self._manager.current_temperature

    @property
    def available(self):
        """Optional: only available if BT is connected."""
        return (self._manager.bt_status == "CONNECTED")


class VolcanoFanHeatControlSensor(VolcanoBaseSensor):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the last fan/heat notification text."""
        return self._manager.fan_heat_status

    @property
    def available(self):
        return (self._manager.bt_status == "CONNECTED")


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor to display the current Bluetooth status/error string."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the manager's current BT status string."""
        return self._manager.bt_status

    @property
    def available(self):
        # We keep this sensor always available to show error/disconnected states
        return True
