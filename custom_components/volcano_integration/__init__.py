"""Volcano Integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up integration via YAML (if any), but we won't use it here."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration from config entry: %s", entry.entry_id)

    # Create the BT Manager instance and start it
    manager = VolcanoBTManager()
    manager.start(hass)

    # Store in hass.data so sensors can retrieve it
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    # Forward setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    # Stop the manager
    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        manager.stop()

    # Unload the sensor platform(s)
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return True
