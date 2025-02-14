"""switch.py - Volcano Integration for Home Assistant."""
import logging

from homeassistant.components.switch import SwitchEntity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano switches for a config entry."""
    _LOGGER.debug("Setting up Volcano switches for entry: %s", entry.entry_id)

    # Retrieve the Bluetooth manager from Home Assistant's data registry
    manager = hass.data[DOMAIN][entry.entry_id]

    # All switch entities removed as requested:
    # - VolcanoVibrationSwitch
    # - VolcanoAutoShutOffSwitch
    async_add_entities([])  # No switch entities.
