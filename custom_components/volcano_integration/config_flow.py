"""Config flow for the Volcano Integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VolcanoIntegrationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcano Integration."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step for the user to 'Submit'."""
        if user_input is not None:
            # We don't actually need user-provided data, since everything is static.
            return self.async_create_entry(title="Volcano Integration", data={})

        # Show an empty form with just a Submit button
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),  # no fields
        )
