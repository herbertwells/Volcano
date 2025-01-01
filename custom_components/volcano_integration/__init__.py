"""Volcano Integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"
PLATFORMS = ["sensor", "button", "number"]

SERVICE_SET_TEMPERATURE = "set_temperature"

SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required("temperature"): vol.Coerce(float),
    vol.Optional("wait_until_reached", default=False): cv.boolean,
})

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Volcano Integration via YAML (if any)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration from config entry: %s", entry.entry_id)

    manager = VolcanoBTManager()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    # Forward setup to sensor, button, and number platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register Services
    async def handle_set_temperature(call):
        temperature = call.data.get("temperature")
        wait = call.data.get("wait_until_reached")
        _LOGGER.debug(f"Service 'set_temperature' called with temperature={temperature}, wait={wait}")
        await manager.set_heater_temperature(temperature)
        if wait:
            await wait_for_temperature(hass, manager, temperature)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        handle_set_temperature,
        schema=SET_TEMPERATURE_SCHEMA
    )

    return True

async def wait_for_temperature(hass: HomeAssistant, manager: VolcanoBTManager, target_temp: float):
    """Wait until the current temperature reaches or exceeds the target temperature."""
    _LOGGER.debug(f"Waiting for temperature to reach {target_temp}°C")
    while manager.current_temperature is not None and manager.current_temperature < target_temp:
        await asyncio.sleep(2)  # Poll every 2 seconds
    _LOGGER.debug(f"Target temperature {target_temp}°C reached")

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.stop()

    # Unregister services if needed
    hass.services.async_remove(DOMAIN, SERVICE_SET_TEMPERATURE)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
