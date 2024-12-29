"""Volcano Integration for Home Assistant.

This initialization file sets up the integration at Home Assistant startup.
"""
import asyncio
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Volcano Integration from YAML (static) config, if any."""
    _LOGGER.debug("Setting up the Volcano Integration (no config flow).")

    # We are intentionally not doing much here since we have no config flow.
    # Sensors will be set up via discovery in sensor.py or using platform setup.
    return True


async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up the Volcano Integration from config entry.")
    # Not used if we are not using config entries. Only included for future reference.
    return True


async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading the Volcano Integration.")
    # Not used if we are not using config entries. Only included for future reference.
    return True
