"""Config flow for Volcano Integration."""
import logging
from homeassistant import config_entries
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class VolcanoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("Config flow initiated for Volcano Integration.")
        try:
            # Automatically create the entry without requiring input
            return self.async_create_entry(title="Volcano Vaporizer", data={})
        except Exception as e:
            _LOGGER.error("Error creating config entry: %s", e)
            raise

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VolcanoOptionsFlowHandler(config_entry)

class VolcanoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Volcano Integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Volcano options."""
        _LOGGER.debug("Options flow initiated for Volcano Integration.")
        try:
            return self.async_create_entry(title="", data={})
        except Exception as e:
            _LOGGER.error("Error creating options entry: %s", e)
            raise
