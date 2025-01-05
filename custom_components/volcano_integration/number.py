"""Platform for number integration - to set heater temperature (40–230 °C)."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define constants for temperature range and step
MIN_TEMP = 40.0
MAX_TEMP = 230.0
DEFAULT_TEMP = 170.0
STEP = 1.0  # 1 °C increments


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano temperature number for a config entry."""
    _LOGGER.debug("Setting up Volcano number for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [VolcanoHeaterTempNumber(manager, entry)]
    async_add_entities(entities)


class VolcanoHeaterTempNumber(NumberEntity):
    """Number entity for setting the Volcano's heater temperature (40–230 °C)."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Heater Temperature Setpoint"
        self._attr_unique_id = f"volcano_heater_temperature_setpoint_{self._manager.bt_address}"
        self._attr_icon = "mdi:thermometer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

        self._attr_native_min_value = MIN_TEMP
        self._attr_native_max_value = MAX_TEMP
        self._attr_native_step = STEP
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Return the current Heater Temperature Setpoint."""
        return self._manager.heater_temperature_setpoint if self._manager.heater_temperature_setpoint else DEFAULT_TEMP

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == "CONNECTED"

    async def async_set_native_value(self, value: float) -> None:
        """Set the Heater Temperature Setpoint."""
        clamped_val = max(MIN_TEMP, min(value, MAX_TEMP))
        _LOGGER.debug("User set heater temperature to %.1f °C -> clamped=%.1f", value, clamped_val)
        await self._manager.set_heater_temperature(clamped_val)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register the temperature setpoint for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister the temperature setpoint to stop receiving updates."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)
