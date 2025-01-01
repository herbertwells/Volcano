"""Volcano Integration for Home Assistant."""
import logging
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .bluetooth_coordinator import VolcanoBTManager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "volcano_integration"
PLATFORMS = ["sensor", "button", "number"]

# Define service names
SERVICE_CONNECT = "connect"
SERVICE_DISCONNECT = "disconnect"
SERVICE_PUMP_ON = "pump_on"
SERVICE_PUMP_OFF = "pump_off"
SERVICE_HEAT_ON = "heat_on"
SERVICE_HEAT_OFF = "heat_off"
SERVICE_SET_TEMPERATURE = "set_temperature"

# Define schemas
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

    # Register Services
    async def handle_connect(call):
        """Handle the connect service."""
        _LOGGER.debug("Service 'connect' called.")
        await manager.async_user_connect()

    async def handle_disconnect(call):
        """Handle the disconnect service."""
        _LOGGER.debug("Service 'disconnect' called.")
        await manager.async_user_disconnect()

    async def handle_pump_on(call):
        """Handle the pump_on service."""
        _LOGGER.debug("Service 'pump_on' called.")
        await manager.write_gatt_command(manager.UUID_PUMP_ON, payload=b"\x01")

    async def handle_pump_off(call):
        """Handle the pump_off service."""
        _LOGGER.debug("Service 'pump_off' called.")
        await manager.write_gatt_command(manager.UUID_PUMP_OFF, payload=b"\x00")

    async def handle_heat_on(call):
        """Handle the heat_on service."""
        _LOGGER.debug("Service 'heat_on' called.")
        await manager.write_gatt_command(manager.UUID_HEAT_ON, payload=b"\x01")

    async def handle_heat_off(call):
        """Handle the heat_off service."""
        _LOGGER.debug("Service 'heat_off' called.")
        await manager.write_gatt_command(manager.UUID_HEAT_OFF, payload=b"\x00")

    async def handle_set_temperature(call):
        """Handle the set_temperature service."""
        temperature = call.data.get("temperature")
        wait = call.data.get("wait_until_reached")
        _LOGGER.debug(f"Service 'set_temperature' called with temperature={temperature}, wait={wait}")
        await manager.set_heater_temperature(temperature)
        if wait:
            await wait_for_temperature(hass, manager, temperature)

    async def wait_for_temperature(hass: HomeAssistant, manager: VolcanoBTManager, target_temp: float):
        """Wait until the current temperature reaches or exceeds the target temperature."""
        _LOGGER.debug(f"Waiting for temperature to reach {target_temp}°C")
        while manager.current_temperature is not None and manager.current_temperature < target_temp:
            _LOGGER.debug("wait_for_temperature. Waiting 500ms for temperature target.")
            await asyncio.sleep(0.5)  # Poll every 500 ms
        _LOGGER.debug(f"Target temperature {target_temp}°C reached")

    # Register each service with Home Assistant
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONNECT,
        handle_connect,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DISCONNECT,
        handle_disconnect,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PUMP_ON,
        handle_pump_on,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PUMP_OFF,
        handle_pump_off,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_HEAT_ON,
        handle_heat_on,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_HEAT_OFF,
        handle_heat_off,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        handle_set_temperature,
        schema=SET_TEMPERATURE_SCHEMA,
    )

    # Start the Bluetooth manager
    await manager.start()

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.stop()

    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_CONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_DISCONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_PUMP_ON)
    hass.services.async_remove(DOMAIN, SERVICE_PUMP_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_ON)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_SET_TEMPERATURE)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
