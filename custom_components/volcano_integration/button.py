"""Platform for button integration. Adds Pump/Heat On/Off in addition to Connect/Disconnect."""
import logging

from homeassistant.components.button import ButtonEntity
from . import DOMAIN
from .bluetooth_coordinator import (
    UUID_PUMP_ON, UUID_PUMP_OFF,
    UUID_HEAT_ON, UUID_HEAT_OFF
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano buttons for a config entry."""
    _LOGGER.debug("Setting up Volcano buttons for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoConnectButton(manager),
        VolcanoDisconnectButton(manager),

        # NEW Pump/Heat GATT write buttons
        VolcanoPumpOnButton(manager),
        VolcanoPumpOffButton(manager),
        VolcanoHeatOnButton(manager),
        VolcanoHeatOffButton(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseButton(ButtonEntity):
    """Base button for the Volcano integration that references the BT manager."""

    def __init__(self, manager):
        self._manager = manager

    @property
    def available(self):
        """We can keep these always available so user can try them anytime."""
        return True


class VolcanoConnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to connect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Connect"
        self._attr_unique_id = "volcano_connect_button"

    async def async_press(self) -> None:
        """Called when user presses the Connect button in HA."""
        _LOGGER.debug("VolcanoConnectButton: pressed by user.")
        await self._manager.async_user_connect()


class VolcanoDisconnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to disconnect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Disconnect"
        self._attr_unique_id = "volcano_disconnect_button"

    async def async_press(self) -> None:
        """Called when user presses the Disconnect button in HA."""
        _LOGGER.debug("VolcanoDisconnectButton: pressed by user.")
        await self._manager.async_user_disconnect()


# ---------------------------------------------------------------------------
#  NEW Pump On/Off
# ---------------------------------------------------------------------------
class VolcanoPumpOnButton(VolcanoBaseButton):
    """A button to turn Pump ON by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump On"
        self._attr_unique_id = "volcano_pump_on_button"

    async def async_press(self) -> None:
        """Called when user presses the Pump On button."""
        _LOGGER.debug("VolcanoPumpOnButton: pressed by user.")
        await self._manager.write_gatt_command(UUID_PUMP_ON)


class VolcanoPumpOffButton(VolcanoBaseButton):
    """A button to turn Pump OFF by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump Off"
        self._attr_unique_id = "volcano_pump_off_button"

    async def async_press(self) -> None:
        """Called when user presses the Pump Off button."""
        _LOGGER.debug("VolcanoPumpOffButton: pressed by user.")
        await self._manager.write_gatt_command(UUID_PUMP_OFF)


# ---------------------------------------------------------------------------
#  NEW Heat On/Off
# ---------------------------------------------------------------------------
class VolcanoHeatOnButton(VolcanoBaseButton):
    """A button to turn Heat ON by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat On"
        self._attr_unique_id = "volcano_heat_on_button"

    async def async_press(self) -> None:
        """Called when user presses the Heat On button."""
        _LOGGER.debug("VolcanoHeatOnButton: pressed by user.")
        await self._manager.write_gatt_command(UUID_HEAT_ON)


class VolcanoHeatOffButton(VolcanoBaseButton):
    """A button to turn Heat OFF by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat Off"
        self._attr_unique_id = "volcano_heat_off_button"

    async def async_press(self) -> None:
        """Called when user presses the Heat Off button."""
        _LOGGER.debug("VolcanoHeatOffButton: pressed by user.")
        await self._manager.write_gatt_command(UUID_HEAT_OFF)
