"""Platform for button integration."""

import logging

from homeassistant.components.button import ButtonEntity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up buttons for Volcano Integration."""
    manager = hass.data[DOMAIN][entry.entry_id]
    entities = [
        VolcanoConnectButton(manager),
        VolcanoDisconnectButton(manager),
        VolcanoPumpOnButton(manager),
        VolcanoPumpOffButton(manager),
        VolcanoHeatOnButton(manager),
        VolcanoHeatOffButton(manager),
    ]
    async_add_entities(entities)

class VolcanoConnectButton(ButtonEntity):
    """A button to connect to the Volcano device."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Connect"
        self._attr_unique_id = "volcano_connect_button"
        self._attr_icon = "mdi:bluetooth"

    async def async_press(self) -> None:
        """Called when user presses the Connect button."""
        _LOGGER.debug("VolcanoConnectButton: pressed by user.")
        await self._manager.start()

class VolcanoDisconnectButton(ButtonEntity):
    """A button to disconnect from the Volcano device."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Disconnect"
        self._attr_unique_id = "volcano_disconnect_button"
        self._attr_icon = "mdi:bluetooth-off"

    async def async_press(self) -> None:
        """Called when user presses the Disconnect button."""
        _LOGGER.debug("VolcanoDisconnectButton: pressed by user.")
        await self._manager.stop()

# Similarly, implement Pump On/Off and Heat On/Off buttons
# Ensure they call the appropriate methods in VolcanoBTManager
