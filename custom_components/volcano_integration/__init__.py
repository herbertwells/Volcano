"""Volcano Integration for Home Assistant."""
import logging
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .bluetooth_coordinator import VolcanoBTManager
from .const import (
    DOMAIN,
    UUID_PUMP_ON,
    UUID_PUMP_OFF,
    UUID_HEAT_ON,
    UUID_HEAT_OFF,
    UUID_LED_BRIGHTNESS,
    UUID_AUTO_SHUT_OFF,
    UUID_AUTO_SHUT_OFF_SETTING,
    UUID_VIBRATION,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "number", "switch"]  # Removed "button"

# Define service names
SERVICE_CONNECT = "connect"
SERVICE_DISCONNECT = "disconnect"
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_LED_BRIGHTNESS = "set_led_brightness"
SERVICE_SET_AUTO_SHUTOFF = "set_auto_shutoff"
SERVICE_SET_AUTO_SHUTOFF_SETTING = "set_auto_shutoff_setting"
SERVICE_SET_VIBRATION = "set_vibration"

# Define schemas
SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Optional("temperature"): vol.All(vol.Coerce(int), vol.Range(min=40, max=230)),
    vol.Optional("percentage"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    vol.Optional("wait_until_reached", default=True): cv.boolean,
})

SET_LED_BRIGHTNESS_SCHEMA = vol.Schema({
    vol.Required("brightness"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
})

SET_AUTO_SHUTOFF_SCHEMA = vol.Schema({
    vol.Required("enabled"): cv.boolean,
})

SET_AUTO_SHUTOFF_SETTING_SCHEMA = vol.Schema({
    vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=30, max=360)),
})

SET_VIBRATION_SCHEMA = vol.Schema({
    vol.Required("enabled"): cv.boolean,
})


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up integration via YAML (if any)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Volcano Integration from a config entry."""
    _LOGGER.debug("Setting up Volcano Integration from config entry: %s", entry.entry_id)

    bt_address = entry.data.get("bt_address")
    device_name = entry.data.get("device_name", "Volcano Vaporizer")

    manager = VolcanoBTManager(bt_address)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = manager

    # Forward setup to sensor, number, and switch platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register Services (optional if you still want services in addition to switches)
    async def handle_set_temperature(call):
        """Handle the set_temperature service."""
        temperature = call.data.get("temperature")
        percentage = call.data.get("percentage")
        wait = call.data.get("wait_until_reached", True)

        if percentage is not None:
            # Convert percentage to temperature (0% -> 40°C, 100% -> 230°C)
            temperature = int(40 + (percentage / 100) * (230 - 40))
            _LOGGER.debug(f"Percentage {percentage}% converted to temperature {temperature}°C")

        if temperature is None:
            _LOGGER.error("No valid temperature or percentage provided for set_temperature.")
            return

        _LOGGER.debug(f"Service 'set_temperature' called with temperature={temperature}, wait={wait}")
        await manager.set_heater_temperature(temperature)
        if wait:
            await wait_for_temperature(hass, manager, temperature)

    async def handle_set_led_brightness(call):
        """Handle the set_led_brightness service."""
        brightness = call.data.get("brightness")
        _LOGGER.debug(f"Service 'set_led_brightness' called with brightness={brightness}%")
        await manager.set_led_brightness(brightness)

    async def handle_set_auto_shutoff(call):
        """Handle the set_auto_shutoff service."""
        enabled = call.data.get("enabled")
        _LOGGER.debug(f"Service 'set_auto_shutoff' called with enabled={enabled}")
        await manager.set_auto_shutoff(enabled)

    async def handle_set_auto_shutoff_setting(call):
        """Handle the set_auto_shutoff_setting service."""
        minutes = call.data.get("minutes")
        _LOGGER.debug(f"Service 'set_auto_shutoff_setting' called with minutes={minutes}")
        await manager.set_auto_shutoff_setting(minutes)

    async def handle_set_vibration(call):
        """Handle the set_vibration service."""
        enabled = call.data.get("enabled")
        _LOGGER.debug(f"Service 'set_vibration' called with enabled={enabled}")
        await manager.set_vibration(enabled)

    async def wait_for_temperature(hass: HomeAssistant, manager: VolcanoBTManager, target_temp: int):
        """Wait until the current temperature reaches or exceeds the target temperature."""
        timeout = 300  # 5 minutes
        elapsed_time = 0
        _LOGGER.debug(f"Waiting for temperature to reach {target_temp}°C with timeout {timeout}s")
        while elapsed_time < timeout:
            if manager.current_temperature is not None:
                _LOGGER.debug(
                    f"Current temperature is {manager.current_temperature}°C; target is {target_temp}°C"
                )
                if manager.current_temperature >= target_temp:
                    _LOGGER.info(f"Target temperature {target_temp}°C reached.")
                    return
            else:
                _LOGGER.warning("Current temperature is None; retrying...")
            await asyncio.sleep(0.5)  # Poll every 500 ms
            elapsed_time += 0.5
        _LOGGER.warning(f"Timeout reached while waiting for temperature {target_temp}°C.")

    # Register each service with Home Assistant (optional)
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TEMPERATURE, handle_set_temperature, schema=SET_TEMPERATURE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_LED_BRIGHTNESS, handle_set_led_brightness, schema=SET_LED_BRIGHTNESS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_AUTO_SHUTOFF, handle_set_auto_shutoff, schema=SET_AUTO_SHUTOFF_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_AUTO_SHUTOFF_SETTING, handle_set_auto_shutoff_setting, schema=SET_AUTO_SHUTOFF_SETTING_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_VIBRATION, handle_set_vibration, schema=SET_VIBRATION_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Volcano Integration."""
    _LOGGER.debug("Unloading Volcano Integration entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.stop()

    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_SET_TEMPERATURE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_LED_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_SET_AUTO_SHUTOFF)
    hass.services.async_remove(DOMAIN, SERVICE_SET_AUTO_SHUTOFF_SETTING)
    hass.services.async_remove(DOMAIN, SERVICE_SET_VIBRATION)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
