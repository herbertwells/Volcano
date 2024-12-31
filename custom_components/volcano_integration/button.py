"""Platform for button integration. Provides Connect/Disconnect buttons."""
import logging

from homeassistant.components.button import ButtonEntity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano buttons for a config entry."""
    _LOGGER.debug("Setting up Volcano buttons for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoConnectButton(manager),
        VolcanoDisconnectButton(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseButton(ButtonEntity):
    """Base button for the Volcano integration that references the BT manager."""

    def __init__(self, manager):
        self._manager = manager

    @property
    def available(self):
        """We can keep these always available so user can force connect/disconnect at any time."""
        return True


class VolcanoConnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to connect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Connect"
        self._attr_unique_id = "volcano_connect_button"

    async def async_press(self) -> None:
        """Called when user presses the Connect button in HA."""
        _LOGGER.debug("%s: Connect button pressed by user.", type(self).__name__)
        await self._manager.async_user_connect()


class VolcanoDisconnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to disconnect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Disconnect"
        self._attr_unique_id = "volcano_disconnect_button"

    async def async_press(self) -> None:
        """Called when user presses the Disconnect button in HA."""
        _LOGGER.debug("%s: Disconnect button pressed by user.", type(self).__name__)
        await self._manager.async_user_disconnect()
