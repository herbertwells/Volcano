"""Volcano Integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"
PLATFORMS = ["sensor", "button", "number"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up integration via YAML (if any)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration from config entry: %s", entry.entry_id)

    manager = VolcanoBTManager()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    # Forward setup to sensor, button, and number platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.stop()

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
