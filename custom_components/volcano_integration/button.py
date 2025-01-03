"""Platform for button integration - Adds fan, heat, and custom control buttons."""
import logging
from homeassistant.components.button import ButtonEntity
from . import DOMAIN
from .bluetooth_coordinator import BT_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano buttons for a config entry."""
    _LOGGER.debug("Setting up Volcano buttons for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoConnectButton(manager),
        VolcanoDisconnectButton(manager),
        VolcanoPumpOnButton(manager),
        VolcanoPumpOffButton(manager),
        VolcanoHeatOnButton(manager),
        VolcanoHeatOffButton(manager),
        VolcanoSetLEDBrightnessButton(manager),
        VolcanoSetAutoShutOffButton(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseButton(ButtonEntity):
    """Base button for the Volcano integration that references the BT manager."""

    def __init__(self, manager):
        super().__init__()
        self._manager = manager
        self._attr_device_info = {
            "identifiers": {(DOMAIN, BT_DEVICE_ADDRESS)},
            "name": "Volcano Vaporizer",
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
        }

    @property
    def available(self):
        """Default availability for buttons."""
        return self._manager.bt_status == "CONNECTED"


class VolcanoConnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to connect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Connect"
        self._attr_unique_id = "volcano_connect_button"
        self._attr_icon = "mdi:bluetooth-connect"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoConnectButton pressed.")
        await self._manager.async_user_connect()


class VolcanoDisconnectButton(VolcanoBaseButton):
    """A button to force the Volcano integration to disconnect BLE."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Disconnect"
        self._attr_unique_id = "volcano_disconnect_button"
        self._attr_icon = "mdi:bluetooth-off"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoDisconnectButton pressed.")
        await self._manager.async_user_disconnect()


class VolcanoPumpOnButton(VolcanoBaseButton):
    """A button to turn Pump ON by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump On"
        self._attr_unique_id = "volcano_pump_on_button"
        self._attr_icon = "mdi:air-purifier"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoPumpOnButton pressed.")
        await self._manager.write_gatt_command(self._manager.UUID_PUMP_ON, payload=b"\x01")


class VolcanoPumpOffButton(VolcanoBaseButton):
    """A button to turn Pump OFF by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Pump Off"
        self._attr_unique_id = "volcano_pump_off_button"
        self._attr_icon = "mdi:air-purifier-off"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoPumpOffButton pressed.")
        await self._manager.write_gatt_command(self._manager.UUID_PUMP_OFF, payload=b"\x00")


class VolcanoHeatOnButton(VolcanoBaseButton):
    """A button to turn Heat ON by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat On"
        self._attr_unique_id = "volcano_heat_on_button"
        self._attr_icon = "mdi:fire"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoHeatOnButton pressed.")
        await self._manager.write_gatt_command(self._manager.UUID_HEAT_ON, payload=b"\x01")


class VolcanoHeatOffButton(VolcanoBaseButton):
    """A button to turn Heat OFF by writing to a GATT characteristic."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heat Off"
        self._attr_unique_id = "volcano_heat_off_button"
        self._attr_icon = "mdi:fire-off"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.debug("VolcanoHeatOffButton pressed.")
        await self._manager.write_gatt_command(self._manager.UUID_HEAT_OFF, payload=b"\x00")


class VolcanoSetLEDBrightnessButton(VolcanoBaseButton):
    """A button to set LED brightness."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Set LED Brightness"
        self._attr_unique_id = "volcano_set_led_brightness_button"
        self._attr_icon = "mdi:led-on"

    async def async_press(self):
        """Handle button press."""
        brightness = int(input("Enter LED Brightness (0-100): "))
        payload = brightness.to_bytes(1, byteorder="little")
        _LOGGER.debug("Setting LED Brightness to %d.", brightness)
        await self._manager.write_gatt_command(self._manager.UUID_LED_BRIGHTNESS, payload)


class VolcanoSetAutoShutOffButton(VolcanoBaseButton):
    """A button to set Auto Shut Off time."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Set Auto Shut Off"
        self._attr_unique_id = "volcano_set_auto_shutoff_button"
        self._attr_icon = "mdi:timer-settings"

    async def async_press(self):
        """Handle button press."""
        minutes = int(input("Enter Auto Shut Off time (minutes): "))
        seconds = (minutes * 60).to_bytes(2, byteorder="little")
        _LOGGER.debug("Setting Auto Shut Off to %d minutes (%d seconds).", minutes, minutes * 60)
        await self._manager.write_gatt_command(self._manager.UUID_AUTO_SHUT_OFF_SETTING, seconds)
