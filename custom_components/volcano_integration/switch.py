"""Platform for switch integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from . import DOMAIN
from .const import (
    UUID_PUMP_ON,
    UUID_PUMP_OFF,
    UUID_HEAT_ON,
    UUID_HEAT_OFF,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano switches for a config entry."""
    _LOGGER.debug("Setting up Volcano switches for entry: %s", entry.entry_id)

    # Retrieve the Bluetooth manager from Home Assistant's data registry
    manager = hass.data[DOMAIN][entry.entry_id]

    # Define the switch entities to be added
    entities = [
        VolcanoAutoShutOffSwitch(manager, entry),
        VolcanoVibrationSwitch(manager, entry),
        VolcanoHeatSwitch(manager, entry),  # New switch for Heat
        VolcanoPumpSwitch(manager, entry),  # New switch for Pump
    ]
    async_add_entities(entities)


class VolcanoBaseSwitch(SwitchEntity):
    """Base switch for the Volcano integration."""

    def __init__(self, manager, config_entry):
        """Initialize the base switch."""
        self._manager = manager
        self._config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def available(self):
        """Return True if Bluetooth is connected."""
        return self._manager.bt_status == "CONNECTED"

    async def async_added_to_hass(self):
        """Register for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister from manager."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)


class VolcanoAutoShutOffSwitch(VolcanoBaseSwitch):
    """Switch entity to enable/disable Auto Shutoff."""

    def __init__(self, manager, config_entry):
        """Initialize the Auto Shutoff switch."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Auto Shutoff"
        self._attr_unique_id = f"volcano_auto_shut_off_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:timer"
        self._attr_entity_category = EntityCategory.CONFIG  # Categorized under Configuration

    @property
    def is_on(self):
        """Return True if auto shutoff is enabled."""
        return self._manager.auto_shut_off == "ON"

    async def async_turn_on(self, **kwargs):
        """Enable Auto Shutoff."""
        _LOGGER.debug("Turning on Auto Shutoff.")
        await self._manager.set_auto_shutoff(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Disable Auto Shutoff."""
        _LOGGER.debug("Turning off Auto Shutoff.")
        await self._manager.set_auto_shutoff(False)
        self.async_write_ha_state()


class VolcanoVibrationSwitch(VolcanoBaseSwitch):
    """Switch to enable/disable the Volcano's vibration feature."""

    def __init__(self, manager, config_entry):
        """Initialize the Vibration switch."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Vibration"
        self._attr_unique_id = f"volcano_vibration_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:vibrate"  # Icon representing vibration
        self._attr_entity_category = EntityCategory.CONFIG  # Categorized under Configuration

    @property
    def is_on(self):
        """Return True if vibration is enabled."""
        return self._manager.vibration == "ON"

    async def async_turn_on(self, **kwargs):
        """Enable vibration."""
        _LOGGER.debug("Turning on vibration.")
        await self._manager.set_vibration(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Disable vibration."""
        _LOGGER.debug("Turning off vibration.")
        await self._manager.set_vibration(False)
        self.async_write_ha_state()


class VolcanoHeatSwitch(VolcanoBaseSwitch):
    """Switch to control the Heat (combine Heat On/Off)."""

    def __init__(self, manager, config_entry):
        """Initialize the Heat switch."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Heat"
        self._attr_unique_id = f"volcano_heat_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:fire"

    @property
    def is_on(self):
        """Return True if heat is enabled."""
        return self._manager.heat_state == "ON"

    async def async_turn_on(self, **kwargs):
        """Turn Heat On."""
        _LOGGER.debug("Turning on Heat.")
        await self._manager.write_gatt_command(UUID_HEAT_ON, payload=b"\x01")
        self._manager.heat_state = "ON"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn Heat Off."""
        _LOGGER.debug("Turning off Heat.")
        await self._manager.write_gatt_command(UUID_HEAT_OFF, payload=b"\x00")
        self._manager.heat_state = "OFF"
        self.async_write_ha_state()


class VolcanoPumpSwitch(VolcanoBaseSwitch):
    """Switch to control the Pump (combine Pump On/Off)."""

    def __init__(self, manager, config_entry):
        """Initialize the Pump switch."""
        super().__init__(manager, config_entry)
        self._attr_name = "Volcano Pump"
        self._attr_unique_id = f"volcano_pump_switch_{self._manager.bt_address}"
        self._attr_icon = "mdi:air-purifier"

    @property
    def is_on(self):
        """Return True if pump is enabled."""
        return self._manager.pump_state == "ON"

    async def async_turn_on(self, **kwargs):
        """Turn Pump On."""
        _LOGGER.debug("Turning on Pump.")
        await self._manager.write_gatt_command(UUID_PUMP_ON, payload=b"\x01")
        self._manager.pump_state = "ON"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn Pump Off."""
        _LOGGER.debug("Turning off Pump.")
        await self._manager.write_gatt_command(UUID_PUMP_OFF, payload=b"\x00")
        self._manager.pump_state = "OFF"
        self.async_write_ha_state()
