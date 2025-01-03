"""Platform for number integration - to set heater temperature (40–230 °C) and other adjustable parameters."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature, TIME_MINUTES

from . import DOMAIN
from .bluetooth_coordinator import BT_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)

MIN_TEMP = 40.0
MAX_TEMP = 230.0
DEFAULT_TEMP = 170.0
STEP = 1.0  # 1 °C increments

MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 100
DEFAULT_BRIGHTNESS = 50
BRIGHTNESS_STEP = 1

MIN_AUTO_SHUTOFF = 1  # Minimum of 1 minute
MAX_AUTO_SHUTOFF = 240  # Maximum of 4 hours
DEFAULT_AUTO_SHUTOFF = 15  # Default of 15 minutes
AUTO_SHUTOFF_STEP = 1


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano numbers for a config entry."""
    _LOGGER.debug("Setting up Volcano numbers for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoHeaterTempNumber(manager),
        VolcanoLEDBrightnessNumber(manager),
        VolcanoAutoShutOffSettingNumber(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseNumber(NumberEntity):
    """Base class for Volcano number entities."""

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
        """Entity is available only when Bluetooth is connected."""
        return self._manager.bt_status == "CONNECTED"

    async def async_added_to_hass(self):
        """Register the number entity for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister the number entity to stop receiving updates."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)


class VolcanoHeaterTempNumber(VolcanoBaseNumber):
    """Number entity for setting the Volcano's heater temperature (40–230 °C)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heater Temperature Setpoint"
        self._attr_unique_id = "volcano_heater_temperature_setpoint"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_min_value = MIN_TEMP
        self._attr_native_max_value = MAX_TEMP
        self._attr_native_step = STEP
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._temp_value = DEFAULT_TEMP

    @property
    def native_value(self):
        return self._temp_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_TEMP, min(value, MAX_TEMP))
        _LOGGER.debug(
            "User set heater temperature to %.1f °C -> clamped=%.1f", value, clamped_val
        )
        self._temp_value = clamped_val
        await self._manager.set_heater_temperature(clamped_val)
        self.async_write_ha_state()


class VolcanoLEDBrightnessNumber(VolcanoBaseNumber):
    """Number entity for adjusting the Volcano's LED brightness."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = "volcano_led_brightness"
        self._attr_icon = "mdi:brightness-6"
        self._attr_native_min_value = MIN_BRIGHTNESS
        self._attr_native_max_value = MAX_BRIGHTNESS
        self._attr_native_step = BRIGHTNESS_STEP
        self._attr_native_unit_of_measurement = "%"
        self._brightness_value = DEFAULT_BRIGHTNESS

    @property
    def native_value(self):
        return self._brightness_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_BRIGHTNESS, min(value, MAX_BRIGHTNESS))
        _LOGGER.debug(
            "User set LED brightness to %d%% -> clamped=%d%%", value, clamped_val
        )
        self._brightness_value = clamped_val
        await self._manager.set_led_brightness(clamped_val)
        self.async_write_ha_state()


class VolcanoAutoShutOffSettingNumber(VolcanoBaseNumber):
    """Number entity for adjusting the Volcano's auto shutoff setting."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Auto Shutoff Setting"
        self._attr_unique_id = "volcano_auto_shutoff_setting"
        self._attr_icon = "mdi:timer-off-outline"
        self._attr_native_min_value = MIN_AUTO_SHUTOFF
        self._attr_native_max_value = MAX_AUTO_SHUTOFF
        self._attr_native_step = AUTO_SHUTOFF_STEP
        self._attr_native_unit_of_measurement = TIME_MINUTES
        self._shutoff_value = DEFAULT_AUTO_SHUTOFF

    @property
    def native_value(self):
        return self._shutoff_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_AUTO_SHUTOFF, min(value, MAX_AUTO_SHUTOFF))
        _LOGGER.debug(
            "User set auto shutoff to %d minutes -> clamped=%d minutes", value, clamped_val
        )
        self._shutoff_value = clamped_val
        await self._manager.set_auto_shutoff_setting(clamped_val)
        self.async_write_ha_state()
"""Platform for number integration - to set heater temperature (40–230 °C) and other adjustable parameters."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature, TIME_MINUTES

from . import DOMAIN
from .bluetooth_coordinator import BT_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)

MIN_TEMP = 40.0
MAX_TEMP = 230.0
DEFAULT_TEMP = 170.0
STEP = 1.0  # 1 °C increments

MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 100
DEFAULT_BRIGHTNESS = 50
BRIGHTNESS_STEP = 1

MIN_AUTO_SHUTOFF = 1  # Minimum of 1 minute
MAX_AUTO_SHUTOFF = 240  # Maximum of 4 hours
DEFAULT_AUTO_SHUTOFF = 15  # Default of 15 minutes
AUTO_SHUTOFF_STEP = 1


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano numbers for a config entry."""
    _LOGGER.debug("Setting up Volcano numbers for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoHeaterTempNumber(manager),
        VolcanoLEDBrightnessNumber(manager),
        VolcanoAutoShutOffSettingNumber(manager),
    ]
    async_add_entities(entities)


class VolcanoBaseNumber(NumberEntity):
    """Base class for Volcano number entities."""

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
        """Entity is available only when Bluetooth is connected."""
        return self._manager.bt_status == "CONNECTED"

    async def async_added_to_hass(self):
        """Register the number entity for state updates."""
        _LOGGER.debug("%s added to Home Assistant.", self._attr_name)
        self._manager.register_sensor(self)

    async def async_will_remove_from_hass(self):
        """Unregister the number entity to stop receiving updates."""
        _LOGGER.debug("%s removed from Home Assistant.", self._attr_name)
        self._manager.unregister_sensor(self)


class VolcanoHeaterTempNumber(VolcanoBaseNumber):
    """Number entity for setting the Volcano's heater temperature (40–230 °C)."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Heater Temperature Setpoint"
        self._attr_unique_id = "volcano_heater_temperature_setpoint"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_min_value = MIN_TEMP
        self._attr_native_max_value = MAX_TEMP
        self._attr_native_step = STEP
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._temp_value = DEFAULT_TEMP

    @property
    def native_value(self):
        return self._temp_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_TEMP, min(value, MAX_TEMP))
        _LOGGER.debug(
            "User set heater temperature to %.1f °C -> clamped=%.1f", value, clamped_val
        )
        self._temp_value = clamped_val
        await self._manager.set_heater_temperature(clamped_val)
        self.async_write_ha_state()


class VolcanoLEDBrightnessNumber(VolcanoBaseNumber):
    """Number entity for adjusting the Volcano's LED brightness."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = "volcano_led_brightness"
        self._attr_icon = "mdi:brightness-6"
        self._attr_native_min_value = MIN_BRIGHTNESS
        self._attr_native_max_value = MAX_BRIGHTNESS
        self._attr_native_step = BRIGHTNESS_STEP
        self._attr_native_unit_of_measurement = "%"
        self._brightness_value = DEFAULT_BRIGHTNESS

    @property
    def native_value(self):
        return self._brightness_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_BRIGHTNESS, min(value, MAX_BRIGHTNESS))
        _LOGGER.debug(
            "User set LED brightness to %d%% -> clamped=%d%%", value, clamped_val
        )
        self._brightness_value = clamped_val
        await self._manager.set_led_brightness(clamped_val)
        self.async_write_ha_state()


class VolcanoAutoShutOffSettingNumber(VolcanoBaseNumber):
    """Number entity for adjusting the Volcano's auto shutoff setting."""

    def __init__(self, manager):
        super().__init__(manager)
        self._attr_name = "Volcano Auto Shutoff Setting"
        self._attr_unique_id = "volcano_auto_shutoff_setting"
        self._attr_icon = "mdi:timer-off-outline"
        self._attr_native_min_value = MIN_AUTO_SHUTOFF
        self._attr_native_max_value = MAX_AUTO_SHUTOFF
        self._attr_native_step = AUTO_SHUTOFF_STEP
        self._attr_native_unit_of_measurement = TIME_MINUTES
        self._shutoff_value = DEFAULT_AUTO_SHUTOFF

    @property
    def native_value(self):
        return self._shutoff_value

    async def async_set_native_value(self, value: float) -> None:
        clamped_val = max(MIN_AUTO_SHUTOFF, min(value, MAX_AUTO_SHUTOFF))
        _LOGGER.debug(
            "User set auto shutoff to %d minutes -> clamped=%d minutes", value, clamped_val
        )
        self._shutoff_value = clamped_val
        await self._manager.set_auto_shutoff_setting(clamped_val)
        self.async_write_ha_state()
