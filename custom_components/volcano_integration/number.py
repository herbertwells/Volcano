"""number.py - Volcano Integration for Home Assistant."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from .const import (
    DOMAIN,
    MIN_TEMP,
    MAX_TEMP,
    DEFAULT_TEMP,
    STEP,
    UUID_HEATER_SETPOINT,
    UUID_LED_BRIGHTNESS,
    UUID_AUTO_SHUT_OFF_SETTING,
    BT_STATUS_CONNECTED,
)

_LOGGER = logging.getLogger(__name__)

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
        """Initialize the Heater Temperature number entity."""
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
            "sw_version": "1.0.0",
            "via_device": None,
        }

        self._attr_native_min_value = MIN_TEMP
        self._attr_native_max_value = MAX_TEMP
        self._attr_native_step = STEP
        self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._temp_value = DEFAULT_TEMP

    @property
    def native_value(self):
        """Return the current temperature setpoint."""
        return self._temp_value

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

    async def async_set_native_value(self, value: float) -> None:
        """Set the heater temperature."""
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
        """Initialize the LED Brightness number entity."""
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = f"volcano_led_brightness_number_{self._manager.bt_address}"
        self._attr_icon = "mdi:brightness-5"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": "1.0.0",
            "via_device": None,
        }
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # LED Brightness range 0–100
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_unit_of_measurement = "%"

        self._brightness = self._manager.led_brightness if self._manager.led_brightness is not None else 0

    @property
    def native_value(self):
        """Return the current LED brightness."""
        return self._brightness

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

    async def async_set_native_value(self, value: float) -> None:
        """Set the LED brightness."""
        brightness_int = int(max(0, min(value, 100)))
        _LOGGER.debug(
            "User set LED Brightness to %.1f -> clamped=%d",
            value,
            brightness_int,
        )
        self._brightness = brightness_int
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
        """Initialize the Auto Shutoff Setting number entity."""
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
            "sw_version": "1.0.0",
            "via_device": None,
        }
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # Updated range: 1–240 minutes
        self._attr_native_min_value = MIN_AUTO_SHUTOFF
        self._attr_native_max_value = MAX_AUTO_SHUTOFF
        self._attr_native_step = 1
        self._attr_unit_of_measurement = "min"

        self._minutes = self._manager.auto_shut_off_setting if self._manager.auto_shut_off_setting is not None else DEFAULT_AUTO_SHUTOFF

    @property
    def native_value(self):
        """Return the current auto shutoff minutes from the manager."""
        return self._minutes

    @property
    def available(self):
        """Available only when Bluetooth is connected."""
        return self._manager.bt_status == BT_STATUS_CONNECTED

    async def async_set_native_value(self, value: float) -> None:
        """Write the new auto shutoff time in minutes to the device."""
        minutes = int(value)
        _LOGGER.debug("User set Auto Shutoff to %d minutes", minutes)
        self._minutes = minutes
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
