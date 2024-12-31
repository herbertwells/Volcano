"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"

async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up Volcano sensors for a config entry.
    We assume `__init__.py` stored the manager in hass.data[DOMAIN][entry.entry_id].
    """
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        VolcanoCurrentTempSensor(manager),
        VolcanoFanHeatControlSensor(manager),
        VolcanoBTStatusSensor(manager),
    ]
    async_add_entities(entities)


class VolcanoCurrentTempSensor(SensorEntity):
    """Numeric Temperature Sensor for the Volcano device."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        # Mark entity category if desired, or leave it None
        self._attr_entity_category = None

    @property
    def native_value(self):
        """Return the current temperature from the manager."""
        return self._manager.current_temperature

    @property
    def available(self):
        """Optional: consider this sensor 'available' only if BT is connected."""
        return (self._manager.bt_status == "CONNECTED")


class VolcanoFanHeatControlSensor(SensorEntity):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the last received fan/heat notification text."""
        return self._manager.fan_heat_status

    @property
    def available(self):
        """Same logic—optional."""
        return (self._manager.bt_status == "CONNECTED")


class VolcanoBTStatusSensor(SensorEntity):
    """Sensor to display the current Bluetooth status/error string."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the manager's current bt_status."""
        return self._manager.bt_status

    @property
    def available(self):
        # If you want this entity always shown, you can just return True:
        return True
