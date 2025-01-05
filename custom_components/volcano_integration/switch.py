"""Platform for switch integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano switches for a config entry."""
    _LOGGER.debug("Setting up Volcano switches for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    # Add or keep any existing switches (pump on/off, etc.)
    entities = [
        VolcanoAutoShutOffSwitch(manager, entry),
        VolcanoVibrationSwitch(manager, entry),
    ]
    async_add_entities(entities)


class VolcanoAutoShutOffSwitch(SwitchEntity):
    """Switch entity to enable/disable Auto Shutoff."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Auto Shutoff"
        self._attr_unique_id = f"volcano_auto_shut_off_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:timer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

        # If you'd like it under "Configuration" or "Diagnostics," uncomment:
        # from homeassistant.helpers.entity import EntityCategory
        # self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self):
        """Return True if auto shutoff is ON (enabled)."""
        return self._manager.auto_shut_off == "ON"

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == "CONNECTED"

    async def async_turn_on(self, **kwargs):
        """Enable Auto Shutoff."""
        _LOGGER.debug("Turning on Auto Shutoff.")
        await self._manager.set_auto_shutoff(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Disable Auto Shutoff."""
        _LOGGER.debug("Turning off Auto Shutoff.")
        await self._manager.set_auto_shutoff(False)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister from manager."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)


class VolcanoVibrationSwitch(SwitchEntity):
    """Switch to enable/disable the Volcano's vibration feature."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Vibration"
        self._attr_unique_id = f"volcano_vibration_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:vibrate"  # or any icon you like
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

        # Mark it as Diagnostics if you want it hidden under "Diagnostics" by default:
        from homeassistant.helpers.entity import EntityCategory
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self):
        """Return True if vibration is ON."""
        return (self._manager.vibration == "ON")

    @property
    def available(self):
        """Available when Bluetooth is connected."""
        return (self._manager.bt_status == "CONNECTED")

    async def async_turn_on(self, **kwargs):
        """Enable vibration."""
        await self._manager.set_vibration(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Disable vibration."""
        await self._manager.set_vibration(False)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister from manager."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)

