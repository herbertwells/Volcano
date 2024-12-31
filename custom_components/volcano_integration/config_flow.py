"""Config flow for the Volcano Integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class VolcanoIntegrationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step for the user to 'Submit'."""
        if user_input is not None:
            # Everything is static, just create the entry with no extra data
            return self.async_create_entry(title="Volcano Integration", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),  # empty form
        )
