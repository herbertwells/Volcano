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

class VolcanoPumpOnButton(ButtonEntity):
    """A button to turn the pump on."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Pump On"
        self._attr_unique_id = "volcano_pump_on_button"
        self._attr_icon = "mdi:fan"

    async def async_press(self) -> None:
        """Called when user presses the Pump On button."""
        _LOGGER.debug("VolcanoPumpOnButton: pressed by user.")
        await self._manager.write_gatt("10110013-5354-4f52-5a26-4249434b454c", b'\x01')

class VolcanoPumpOffButton(ButtonEntity):
    """A button to turn the pump off."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Pump Off"
        self._attr_unique_id = "volcano_pump_off_button"
        self._attr_icon = "mdi:fan-off"

    async def async_press(self) -> None:
        """Called when user presses the Pump Off button."""
        _LOGGER.debug("VolcanoPumpOffButton: pressed by user.")
        await self._manager.write_gatt("10110014-5354-4f52-5a26-4249434b454c", b'\x00')

class VolcanoHeatOnButton(ButtonEntity):
    """A button to turn the heat on."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Heat On"
        self._attr_unique_id = "volcano_heat_on_button"
        self._attr_icon = "mdi:fire"

    async def async_press(self) -> None:
        """Called when user presses the Heat On button."""
        _LOGGER.debug("VolcanoHeatOnButton: pressed by user.")
        await self._manager.write_gatt("1011000f-5354-4f52-5a26-4249434b454c", b'\x01')

class VolcanoHeatOffButton(ButtonEntity):
    """A button to turn the heat off."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Heat Off"
        self._attr_unique_id = "volcano_heat_off_button"
        self._attr_icon = "mdi:fire-off"

    async def async_press(self) -> None:
        """Called when user presses the Heat Off button."""
        _LOGGER.debug("VolcanoHeatOffButton: pressed by user.")
        await self._manager.write_gatt("10110010-5354-4f52-5a26-4249434b454c", b'\x00')
