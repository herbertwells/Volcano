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
SERVICE_SET_BRIGHTNESS = "set_brightness"
SERVICE_SET_AUTO_SHUTOFF = "set_auto_shutoff"

# Define schemas
SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Optional("temperature"): vol.All(vol.Coerce(int), vol.Range(min=40, max=230)),
    vol.Optional("percentage"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    vol.Optional("wait_until_reached", default=True): cv.boolean,
})

SET_BRIGHTNESS_SCHEMA = vol.Schema({
    vol.Required("brightness"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
})

SET_AUTO_SHUTOFF_SCHEMA = vol.Schema({
    vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=1, max=240)),
})


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up integration via YAML (if any)."""
    _LOGGER.debug("async_setup called for YAML setup")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration from config entry: %s", entry.entry_id)

    try:
        manager = VolcanoBTManager()
        _LOGGER.debug("Initialized VolcanoBTManager instance.")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = manager

        # Forward setup to platforms
        _LOGGER.debug("Forwarding entry setup to platforms: %s", PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register Services
        register_services(hass, manager)

        return True
    except Exception as e:
        _LOGGER.error("Error during async_setup_entry: %s", e, exc_info=True)
        return False


def register_services(hass: HomeAssistant, manager: VolcanoBTManager):
    """Register integration services."""

    async def handle_connect(call):
        _LOGGER.debug("Service 'connect' called.")
        if not manager._connected:
            await manager.async_user_connect()
        else:
            _LOGGER.info("Already connected to the device.")

    async def handle_disconnect(call):
        _LOGGER.debug("Service 'disconnect' called.")
        if manager._connected:
            await manager.async_user_disconnect()
        else:
            _LOGGER.info("Device already disconnected.")

    async def handle_pump_on(call):
        _LOGGER.debug("Service 'pump_on' called.")
        await manager.write_gatt_command(manager.UUID_PUMP_ON, payload=b"\x01")

    async def handle_pump_off(call):
        _LOGGER.debug("Service 'pump_off' called.")
        await manager.write_gatt_command(manager.UUID_PUMP_OFF, payload=b"\x00")

    async def handle_heat_on(call):
        _LOGGER.debug("Service 'heat_on' called.")
        await manager.write_gatt_command(manager.UUID_HEAT_ON, payload=b"\x01")

    async def handle_heat_off(call):
        _LOGGER.debug("Service 'heat_off' called.")
        await manager.write_gatt_command(manager.UUID_HEAT_OFF, payload=b"\x00")

    async def handle_set_temperature(call):
        temperature = call.data.get("temperature")
        percentage = call.data.get("percentage")
        wait = call.data.get("wait_until_reached", True)

        if percentage is not None:
            temperature = int(40 + (percentage / 100) * (230 - 40))
            _LOGGER.debug("Percentage %d%% converted to temperature %d°C", percentage, temperature)

        if temperature is None:
            _LOGGER.error("No valid temperature or percentage provided for set_temperature.")
            return

        _LOGGER.debug("Setting temperature to %d°C with wait=%s", temperature, wait)
        await manager.set_heater_temperature(temperature)
        if wait:
            await wait_for_temperature(hass, manager, temperature)

    async def handle_set_brightness(call):
        brightness = call.data.get("brightness")
        _LOGGER.debug("Setting brightness to %d", brightness)
        await manager.set_led_brightness(brightness)

    async def handle_set_auto_shutoff(call):
        minutes = call.data.get("minutes")
        _LOGGER.debug("Setting auto shutoff to %d minutes", minutes)
        await manager.set_auto_shutoff_setting(minutes)

    async def wait_for_temperature(hass: HomeAssistant, manager: VolcanoBTManager, target_temp: int):
        timeout = 300
        elapsed_time = 0
        _LOGGER.debug("Waiting for temperature to reach %d°C", target_temp)

        while elapsed_time < timeout:
            if manager.current_temperature is not None:
                if manager.current_temperature >= target_temp:
                    _LOGGER.info("Target temperature %d°C reached.", target_temp)
                    return
            await asyncio.sleep(0.5)
            elapsed_time += 0.5
        _LOGGER.warning("Timeout waiting for target temperature %d°C.", target_temp)

    hass.services.async_register(DOMAIN, SERVICE_CONNECT, handle_connect)
    hass.services.async_register(DOMAIN, SERVICE_DISCONNECT, handle_disconnect)
    hass.services.async_register(DOMAIN, SERVICE_PUMP_ON, handle_pump_on)
    hass.services.async_register(DOMAIN, SERVICE_PUMP_OFF, handle_pump_off)
    hass.services.async_register(DOMAIN, SERVICE_HEAT_ON, handle_heat_on)
    hass.services.async_register(DOMAIN, SERVICE_HEAT_OFF, handle_heat_off)
    hass.services.async_register(DOMAIN, SERVICE_SET_TEMPERATURE, handle_set_temperature, schema=SET_TEMPERATURE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_BRIGHTNESS, handle_set_brightness, schema=SET_BRIGHTNESS_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_AUTO_SHUTOFF, handle_set_auto_shutoff, schema=SET_AUTO_SHUTOFF_SCHEMA)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.stop()

    hass.services.async_remove(DOMAIN, SERVICE_CONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_DISCONNECT)
    hass.services.async_remove(DOMAIN, SERVICE_PUMP_ON)
    hass.services.async_remove(DOMAIN, SERVICE_PUMP_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_ON)
    hass.services.async_remove(DOMAIN, SERVICE_HEAT_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_SET_TEMPERATURE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_SET_AUTO_SHUTOFF)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
