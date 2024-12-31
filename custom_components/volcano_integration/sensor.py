"""Platform for sensor integration, creating separate sensors for heat, fan, temperature, and BT status."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature

DOMAIN = "volcano_integration"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up Volcano sensors for a config entry, creating four entities:
      - Temperature (°C)
      - Heat (ON/OFF)
      - Fan (ON/OFF)
      - Bluetooth Status
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
    """
    Base sensor that handles:
      - Registration/unregistration with the manager
      - Debug logs about availability, etc.
    """

    def __init__(self, manager):
        self._manager = manager
        _LOGGER.debug("%s: __init__ with manager=%s", type(self).__name__, manager)

    async def async_added_to_hass(self):
        """Register with the manager for immediate update notifications."""
        _LOGGER.debug("%s: async_added_to_hass -> registering sensor with manager", type(self).__name__)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister when removed."""
        _LOGGER.debug("%s: async_will_remove_from_hass -> unregistering sensor from manager", type(self).__name__)
        self._manager.unregister_sensor(self)


class VolcanoCurrentTempSensor(VolcanoBaseSensor):
    """Numeric Temperature Sensor for the Volcano device (in °C)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Return the current temperature from the manager."""
        val = self._manager.current_temperature
        _LOGGER.debug("%s: native_value -> %s °C", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Consider the sensor available only if BT is connected."""
        is_avail = (self._manager.bt_status == "CONNECTED")
        _LOGGER.debug("%s: available -> %s (bt_status=%s)", type(self).__name__, is_avail, self._manager.bt_status)
        return is_avail


class VolcanoHeatSensor(VolcanoBaseSensor):
    """Sensor for the Volcano's Heat state (ON/OFF). Derived from left byte in notifications."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat"
        self._attr_unique_id = "volcano_heat"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the manager's heat state (ON/OFF/UNKNOWN)."""
        val = self._manager.heat_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Optional: only show 'available' if BT is connected."""
        is_avail = (self._manager.bt_status == "CONNECTED")
        _LOGGER.debug("%s: available -> %s (bt_status=%s)", type(self).__name__, is_avail, self._manager.bt_status)
        return is_avail


class VolcanoFanSensor(VolcanoBaseSensor):
    """Sensor for the Volcano's Fan state (ON/OFF). Derived from right byte in notifications."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Fan"
        self._attr_unique_id = "volcano_fan"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the manager's fan state (ON/OFF/UNKNOWN)."""
        val = self._manager.fan_state
        _LOGGER.debug("%s: native_value -> %s", type(self).__name__, val)
        return val

    @property
    def available(self):
        """Optional: only show 'available' if BT is connected."""
        is_avail = (self._manager.bt_status == "CONNECTED")
        _LOGGER.debug("%s: available -> %s (bt_status=%s)", type(self).__name__, is_avail, self._manager.bt_status)
        return is_avail


class VolcanoBTStatusSensor(VolcanoBaseSensor):
    """Sensor that shows the current Bluetooth status/error string."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the manager's bt_status string (CONNECTED, DISCONNECTED, ERROR, etc.)."""
        val = self._manager.bt_status
        _LOGGER.debug("%s: native_value -> '%s'", type(self).__name__, val)
        return val

    @property
    def available(self):
        """
        We keep this sensor 'always' available,
        so it can display DISCONNECTED or ERROR states too.
        """
        return True
