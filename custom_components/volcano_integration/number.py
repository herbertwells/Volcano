"""Platform for number integration - to set heater temperature (40–230 °C)
   and now LED Brightness (0–100), plus Auto Shutoff Setting in minutes."""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory  # For Diagnostics
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_TEMP = 40.0
MAX_TEMP = 230.0
DEFAULT_TEMP = 170.0
STEP = 1.0  # 1 °C increments

MIN_AUTO_SHUTOFF = 30
MAX_AUTO_SHUTOFF = 360
DEFAULT_AUTO_SHUTOFF = 60
STEP_AUTO_SHUTOFF = 1

MIN_LED_BRIGHTNESS = 0
MAX_LED_BRIGHTNESS = 100
STEP_LED_BRIGHTNESS = 1

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano number entities for a config entry."""
    _LOGGER.debug("Setting up Volcano numbers for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    # Ensure the heater temp, brightness, and new auto shutoff setting entities are created.
    entities = [
        VolcanoHeaterTempNumber(manager, entry),
        VolcanoLEDBrightnessNumber(manager, entry),
        VolcanoAutoShutOffMinutesNumber(manager, entry),  # New entity for Auto Shutoff Setting
    ]
    async_add_entities(entities)


class VolcanoHeaterTempNumber(NumberEntity):
    """Number entity for setting the Volcano's heater temperature (40–230 °C)."""

    def __init__(self, manager, config_entry):
        super().__init__()
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
        self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._temp_value = self._manager.current_temperature if self._manager.bt_status == BT_STATUS_CONNECTED else DEFAULT_TEMP

    @property
    def native_value(self):
        return self._temp_value

    @property
    def available(self):
        return True  # Always available

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_TEMP, min(value, MAX_TEMP))
        _LOGGER.debug(
            "User set heater temperature to %.1f °C -> clamped=%.1f",
            value,
            clamped_val,
        )
        self._temp_value = clamped_val
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


class VolcanoLEDBrightnessNumber(NumberEntity):
    """Number entity for setting the Volcano's LED Brightness (0–100)."""

    def __init__(self, manager, config_entry):
        super().__init__()
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = f"volcano_led_brightness_number_{self._manager.bt_address}"
        self._attr_icon = "mdi:brightness-5"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }
        # LED Brightness range 0–100
        self._attr_native_min_value = MIN_LED_BRIGHTNESS
        self._attr_native_max_value = MAX_LED_BRIGHTNESS
        self._attr_native_step = STEP_LED_BRIGHTNESS
        self._attr_unit_of_measurement = "%"

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            return self._manager.led_brightness
        return MAX_LED_BRIGHTNESS  # Default brightness when disconnected

    @property
    def available(self):
        return True  # Always available

    async def async_set_native_value(self, value: float) -> None:
        brightness_int = int(max(MIN_LED_BRIGHTNESS, min(value, MAX_LED_BRIGHTNESS)))
        _LOGGER.debug(
            "User set LED Brightness to %.1f -> clamped=%d",
            value,
            brightness_int,
        )
        await self._manager.set_led_brightness(brightness_int)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register LED brightness for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister LED brightness entity to stop receiving updates."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)


class VolcanoAutoShutOffMinutesNumber(NumberEntity):
    """Number entity for setting the Volcano's Auto Shutoff Setting (in minutes)."""

    def __init__(self, manager, config_entry):
        super().__init__()
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Auto Shutoff Setting"
        self._attr_unique_id = f"volcano_auto_shutoff_minutes_{self._manager.bt_address}"
        self._attr_icon = "mdi:timer-cog"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }
        # Auto Shutoff Setting range: 30–360 minutes
        self._attr_native_min_value = MIN_AUTO_SHUTOFF
        self._attr_native_max_value = MAX_AUTO_SHUTOFF
        self._attr_native_step = STEP_AUTO_SHUTOFF
        self._attr_unit_of_measurement = "min"

    @property
    def native_value(self):
        if self._manager.bt_status == BT_STATUS_CONNECTED:
            return self._manager.auto_shut_off_setting
        return DEFAULT_AUTO_SHUTOFF  # Default setting when disconnected

    @property
    def available(self):
        return True  # Always available

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(max(MIN_AUTO_SHUTOFF, min(value, MAX_AUTO_SHUTOFF)))
        _LOGGER.debug("User set Auto Shutoff to %d minutes", minutes)
        await self._manager.set_auto_shutoff_setting(minutes)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister to stop receiving updates."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)
