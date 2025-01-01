"""Volcano Integration for Home Assistant."""
import logging
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
import voluptuous as vol

from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"
PLATFORMS = ["sensor", "button", "number"]

# Define services
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_CONNECT = "connect"
SERVICE_DISCONNECT = "disconnect"
SERVICE_FAN_ON = "fan_on"
SERVICE_FAN_OFF = "fan_off"
SERVICE_HEAT_ON = "heat_on"
SERVICE_HEAT_OFF = "heat_off"

# Define service schemas
SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(min=40.0, max=230.0)),
    vol.Optional("wait_until_reached", default=False): cv.boolean,
})

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

    # Register services
    async def handle_set_temperature(call):
        temperature = call.data.get("temperature")
        wait = call.data.get("wait_until_reached")
        _LOGGER.debug(f"Service 'set_temperature' called with temperature={temperature}, wait={wait}")
        await manager.set_heater_temperature(temperature)
        if wait:
            await wait_for_temperature(hass, manager, temperature)

    async def handle_connect(call):
        """Handle the connect service."""
        _LOGGER.debug("Service 'connect' called.")
        await manager.async_user_connect()

    async def handle_disconnect(call):
        """Handle the disconnect service."""
        _LOGGER.debug("Service 'disconnect' called.")
        await manager.async_user_disconnect()

    async def handle_fan_on(call):
        """Handle the fan_on service."""
        _LOGGER.debug("Service 'fan_on' called.")
        await manager.fan_on()

    async def handle_fan_off(call):
        """Handle the fan_off service."""
        _LOGGER.debug("Service 'fan_off' called.")
        await manager.fan_off()

    async def handle_heat_on(call):
        """Handle the heat_on service."""
        _LOGGER.debug("Service 'heat_on' called.")
        await manager.heat_on()

    async def handle_heat_off(call):
        """Handle the heat_off service."""
        _LOGGER.debug("Service 'heat_off' called.")
        await manager.heat_off()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        handle_set_temperature,
        schema=SET_TEMPERATURE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONNECT,
        handle_connect,
        schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISCONNECT,
        handle_disconnect,
        schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_FAN_ON,
        handle_fan_on,
        schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_FAN_OFF,
        handle_fan_off,
        schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HEAT_ON,
        handle_heat_on,
        schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HEAT_OFF,
        handle_heat_off,
        schema=vol.Schema({})
    )

    # Create a device
    device_info = DeviceInfo(
        identifiers={(DOMAIN, "volcano_vaporisor")},
        name="Volcano Vaporisor",
        manufacturer="Volcano",
        model="Vaporisor",
        sw_version="1.0.0",
    )
    manager.device_info = device_info

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

    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_SET_TEMPERATURE)
    hass.services.async_remove(DOMAIN, SERVICE_CONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_DISCONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_FAN_ON)
    hass.services.async_remove(DOMAIN, SERVICE_FAN_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_ON)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_OFF)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
