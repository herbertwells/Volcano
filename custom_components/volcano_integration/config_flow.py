"""Config flow for Volcano Integration."""
import logging
from homeassistant import config_entries
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class VolcanoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("Initiating Volcano Integration config flow.")
        # Directly proceed to creating the entry
        return self.async_create_entry(title="Volcano Vaporizer", data={})

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
