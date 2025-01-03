"""Config flow for Volcano Integration."""
import logging
import asyncio

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from bleak import BleakScanner

_LOGGER = logging.getLogger(__name__)

class VolcanoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Initiating Volcano Integration config flow.")

        if user_input is not None:
            selected_device = user_input.get("selected_device")
            if selected_device:
                return self.async_create_entry(
                    title=selected_device["name"],
                    data={
                        "bt_address": selected_device["address"],
                        "device_name": selected_device["name"],
                    },
                )

        # Discover Bluetooth devices
        devices = await self._discover_bluetooth_devices()

        if not devices:
            return self.async_abort(reason="no_devices_found")

        # Create a list of devices for selection
        device_options = [
            (device.address, device.name or device.address) for device in devices
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_device_selection_schema(devices),
            errors={},
        )

    async def _discover_bluetooth_devices(self, timeout: int = 10):
        """Discover Bluetooth devices using BleakScanner."""
        _LOGGER.debug("Starting Bluetooth device discovery for %s seconds...", timeout)
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            _LOGGER.debug("Discovered %d Bluetooth devices.", len(devices))
            # Filter devices that match Volcano Vaporizer patterns (optional)
            # For now, return all devices
            return devices
        except Exception as e:
            _LOGGER.error("Error during Bluetooth device discovery: %s", e)
            return []

    def _get_device_selection_schema(self, devices):
        """Generate a selection schema based on discovered devices."""
        from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectOption

        options = [
            SelectOption(label=device.name or device.address, value=device)
            for device in devices
        ]

        selector = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"label": device.name or device.address, "value": device}
                    for device in devices
                ],
                mode="dropdown",
            )
        )

        return vol.Schema(
            {
                vol.Required(
                    "selected_device",
                    default=devices[0] if devices else None,
                ): selector
            }
        )

    async def async_step_import(self, import_data):
        """Handle configuration by YAML import."""
        return await self.async_step_user()

    @staticmethod
    async def async_get_options_flow(config_entry):
        """Options flow handler."""
        return VolcanoOptionsFlowHandler(config_entry)

class VolcanoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Volcano Integration options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Volcano options."""
        _LOGGER.debug("Initiating options flow.")
        return self.async_create_entry(title="", data=user_input or {})
