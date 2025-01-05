"""Platform for switch integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano switches for a config entry."""
    _LOGGER.debug("Setting up Volcano switches for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoAutoShutOffSwitch(manager, entry),
    ]
    async_add_entities(entities)


class VolcanoAutoShutOffSwitch(SwitchEntity):
    """Switch entity to control Auto Shutoff."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Auto Shutoff"
        self._attr_unique_id = f"volcano_auto_shutoff_{self._manager.bt_address}"
        self._attr_icon = "mdi:timer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }
        self._attr_is_on = False

    @property
    def is_on(self):
        return self._manager.auto_shut_off == "Enabled"

    async def async_turn_on(self, **kwargs):
        """Turn on Auto Shutoff."""
        await self._manager.set_auto_shutoff(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off Auto Shutoff."""
        await self._manager.set_auto_shutoff(False)
        self._attr_is_on = False
        self.async_write_ha_state()
