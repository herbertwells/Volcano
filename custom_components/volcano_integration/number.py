"""Platform for number integration - to set heater temperature (40–230 °C)."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_TEMP = 40.0
MAX_TEMP = 230.0
STEP = 1.0  # 1 °C increments, or you can do 0.5 if desired

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano temperature number for a config entry."""
    _LOGGER.debug("Setting up Volcano number for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [VolcanoHeaterTempNumber(manager)]
    async_add_entities(entities)


class VolcanoHeaterTempNumber(NumberEntity):
    """Number entity for setting the Volcano's heater temperature (40–230 °C)."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Volcano Heater Temperature Setpoint"
        self._attr_unique_id = "volcano_heater_setpoint"
        self._attr_entity_category = EntityCategory.CONFIG

        # Set the allowed range
        self._attr_min_value = MIN_TEMP
        self._attr_max_value = MAX_TEMP
        self._attr_step = STEP
        self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._temp_value = 40.0  # default to min or anything you like

    @property
    def native_value(self):
        """
        Return the current setpoint we *think* we have. 
        If the device doesn't confirm, we only track our last set value.
        """
        return self._temp_value

    async def async_set_native_value(self, value: float) -> None:
        """
        Called when the user moves the slider or sets a value from 40–230 in HA UI.
        We clamp it and call manager.set_heater_temperature(value).
        """
        clamped_val = max(MIN_TEMP, min(value, MAX_TEMP))
        _LOGGER.debug(
            "User set heater temperature to %.1f °C -> clamped=%.1f",
            value, clamped_val
        )
        self._temp_value = clamped_val

        # Fire the BLE write to the device
        await self._manager.set_heater_temperature(clamped_val)

        # We can store this locally; the device doesn't confirm the setpoint 
        # unless you read it back from a GATT char. 
        self.async_write_ha_state()

    @property
    def available(self):
        """Only available if BLE is connected."""
        return (self._manager.bt_status == "CONNECTED")
