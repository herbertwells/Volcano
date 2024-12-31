"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Volcano sensors for a config entry."""
    _LOGGER.debug("Setting up Volcano sensors for entry: %s", entry.entry_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoCurrentTempSensor(coordinator),
        VolcanoFanHeatControlSensor(coordinator),
        VolcanoBTStatusSensor(coordinator),
        VolcanoRSSISensor(coordinator),
    ]
    async_add_entities(entities)


class VolcanoCurrentTempSensor(SensorEntity):
    """Numeric Temperature Sensor for the Volcano device."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "Volcano Current Temperature"
        self._attr_unique_id = "volcano_current_temperature"
        # Mark as temperature device class for nicer UI
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_entity_category = None  # or EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the current temperature (float)."""
        return self._coordinator.data["temperature"]

    @property
    def available(self) -> bool:
        """Entity is available if we're not in an error or disconnected state."""
        bt_status = self._coordinator.data["bt_status"]
        # If it starts with "ERROR", or is "DISCONNECTED", we might consider it unavailable
        # But your preference may vary; you could keep it "available" but None for the reading.
        if bt_status.startswith("ERROR") or bt_status == "DISCONNECTED":
            return False
        return True

    async def async_update(self):
        """No-op. Data is updated by the coordinator every 1s."""
        pass

    async def async_added_to_hass(self) -> None:
        """Request an immediate update once we add this entity."""
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))


class VolcanoFanHeatControlSensor(SensorEntity):
    """Sensor for the Volcano's Fan/Heat Control notifications."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "Volcano Fan/Heat Control"
        self._attr_unique_id = "volcano_fan_heat_control"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the latest fan/heat notification string."""
        return self._coordinator.data["fan_heat_status"]

    async def async_update(self):
        """No-op. The coordinator updates data in background."""
        pass

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))


class VolcanoBTStatusSensor(SensorEntity):
    """Sensor reflecting the current Bluetooth connectivity status (detailed)."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "Volcano Bluetooth Status"
        self._attr_unique_id = "volcano_bt_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the coordinator's current Bluetooth status string."""
        return self._coordinator.data["bt_status"]

    async def async_update(self):
        """No-op. The coordinator updates data in background."""
        pass

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))


class VolcanoRSSISensor(SensorEntity):
    """Sensor to display the current RSSI value from the device."""

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "Volcano RSSI"
        self._attr_unique_id = "volcano_rssi"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # If you want a device_class, it's optional. There's no built-in 'RSSI' device class.
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the last known RSSI (int in dBm) or None."""
        return self._coordinator.data["rssi"]

    async def async_update(self):
        """No-op. The coordinator updates data in background."""
        pass

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))
