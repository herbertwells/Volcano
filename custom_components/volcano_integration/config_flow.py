"""config_flow.py - Volcano Integration for Home Assistant."""
import logging
import asyncio

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import DOMAIN
from bleak import BleakScanner

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading config_flow module")  # Add this line at the top

REFRESH_OPTION_VALUE = "REFRESH_DEVICE_LIST"

@config_entries.HANDLERS.register(DOMAIN)
class VolcanoConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Volcano Integration."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step of the config flow."""
        _LOGGER.debug("Initiating Volcano Integration config flow.")

        if user_input is not None:
            selected_address = user_input.get("selected_device")

            if selected_address == REFRESH_OPTION_VALUE:
                _LOGGER.debug("User requested to refresh device list.")
                return await self.async_step_user()

            selected_device = self._discovered_devices.get(selected_address)

            if selected_device:
                return self.async_create_entry(
                    title=selected_device.name or selected_address,
                    data={
                        "bt_address": selected_address,
                        "device_name": selected_device.name or "Volcano Vaporizer",
                    },
                )
            else:
                return self.async_abort(reason="device_not_found")

        # Discover Bluetooth devices
        devices = await self._discover_bluetooth_devices()

        if not devices:
            return self.async_abort(reason="no_devices_found")

        # Map devices by address for easy lookup
        self._discovered_devices = {device.address: device for device in devices}

        # Create a list of dictionaries for the selector
        options = [
            {"label": device.name or device.address, "value": device.address}
            for device in devices
        ]

        # Add a 'Refresh device list' option
        options.append({"label": "Refresh Device List", "value": REFRESH_OPTION_VALUE})

        selector = SelectSelector(
            SelectSelectorConfig(
                options=options,
                mode=SelectSelectorMode.DROPDOWN,
                custom_value=False,
            )
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_device"): selector
                }
            ),
            errors={},
        )

    async def _discover_bluetooth_devices(self, timeout: int = 10):
        """Discover Bluetooth devices using BleakScanner."""
        _LOGGER.debug("Starting Bluetooth device discovery for %s seconds...", timeout)
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            _LOGGER.debug("Discovered %d Bluetooth devices.", len(devices))
            # Optionally, filter devices by name or other criteria here
            return devices
        except Exception as e:
            _LOGGER.error("Error during Bluetooth device discovery: %s", e)
            return []

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

def verify_registration():
    """Verify that the config flow is properly registered."""
    _LOGGER.debug("Verifying config flow registration for domain: %s", DOMAIN)
    from homeassistant.config_entries import HANDLERS
    if DOMAIN in HANDLERS:
        _LOGGER.debug("Config flow successfully registered")
    else:
        _LOGGER.error("Config flow registration failed!")

verify_registration()  # Add this at the bottom of the file
