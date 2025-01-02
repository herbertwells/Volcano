"""Config flow for Volcano Integration."""
import logging
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class VolcanoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("Starting config flow for Volcano Integration.")
        if user_input is not None:
            _LOGGER.debug("Received user input: %s", user_input)
            try:
                return self.async_create_entry(title="Volcano Vaporizer", data=user_input)
            except Exception as e:
                _LOGGER.error("Error during entry creation: %s", e)
                raise

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="Volcano Vaporizer"): str,
                vol.Required("mac_address"): vol.All(
                    vol.Upper,
                    vol.Match(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"),
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VolcanoOptionsFlowHandler(config_entry)

class VolcanoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Volcano Integration options."""

    def __init__(self, config_entry):
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Volcano options."""
        _LOGGER.debug("Options flow init with user input: %s", user_input)
        try:
            return self.async_create_entry(title="", data=user_input or {})
        except Exception as e:
            _LOGGER.error("Error during options entry creation: %s", e)
            raise
