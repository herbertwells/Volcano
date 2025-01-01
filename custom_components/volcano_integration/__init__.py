"""Volcano Integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Volcano Integration."""
    _LOGGER.debug("Initializing Volcano Integration setup.")
    hass.data.setdefault(DOMAIN, {})
    return True  # Indicate successful setup

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration entry: %s", entry.entry_id)
    try:
        manager = VolcanoBTManager()
        hass.data[DOMAIN][entry.entry_id] = manager

        # Removed the automatic start to prevent Bluetooth connection on startup
        # await manager.start()

        _LOGGER.info("Volcano Integration setup complete for entry: %s", entry.entry_id)
        return True  # Indicate successful setup

    except Exception as e:
        _LOGGER.error("Error during Volcano Integration setup: %s", e)
        raise ConfigEntryNotReady from e  # Let HA know the setup failed temporarily

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)
    manager: VolcanoBTManager = hass.data[DOMAIN].get(entry.entry_id)

    if manager:
        try:
            await manager.stop()
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("Volcano Integration unloaded for entry: %s", entry.entry_id)
            return True  # Indicate successful unload
        except Exception as e:
            _LOGGER.error("Error unloading Volcano Integration: %s", e)
            return False  # Indicate unload failed
    else:
        _LOGGER.warning("No manager found for entry: %s", entry.entry_id)
        return False  # Indicate unload failed
