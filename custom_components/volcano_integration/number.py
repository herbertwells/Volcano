# number.py

"""Platform for number integration."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTime
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Volcano number entities for a config entry."""
    _LOGGER.debug("Setting up Volcano number entities for entry: %s", entry.entry_id)

    manager = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VolcanoAutoShutOffSettingNumber(manager, entry),
        VolcanoLEDBrightnessNumber(manager, entry),
        VolcanoHeaterTemperatureSetpointNumber(manager, entry),  # Added Heater Temperature Setpoint
    ]
    async_add_entities(entities)


class VolcanoAutoShutOffSettingNumber(NumberEntity):
    """Number entity to set Auto Shutoff Duration."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Auto Shutoff Setting"
        self._attr_unique_id = f"volcano_auto_shutoff_setting_{self._manager.bt_address}"
        self._attr_native_min_value = 30  # 30 minutes
        self._attr_native_max_value = 360  # 360 minutes
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_icon = "mdi:timer-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the Auto Shutoff Setting in minutes."""
        return self._manager.auto_shut_off_setting // 60 if self._manager.auto_shut_off_setting else 30

    @property
    def available(self):
        """Return True if the number entity is available."""
        return self._manager.bt_status == "CONNECTED"

    async def async_set_native_value(self, value: float) -> None:
        """Set the Auto Shutoff Setting."""
        minutes = int(value)
        _LOGGER.debug("Setting Auto Shutoff Setting to %s minutes", minutes)
        await self._manager.set_auto_shutoff_setting(minutes)
        self.async_write_ha_state()


class VolcanoLEDBrightnessNumber(NumberEntity):
    """Number entity to set LED Brightness."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano LED Brightness"
        self._attr_unique_id = f"volcano_led_brightness_{self._manager.bt_address}"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:brightness-5"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the LED Brightness percentage."""
        return self._manager.led_brightness if self._manager.led_brightness is not None else 50

    @property
    def available(self):
        """Return True if the number entity is available."""
        return self._manager.bt_status == "CONNECTED"

    async def async_set_native_value(self, value: float) -> None:
        """Set the LED Brightness."""
        brightness = int(value)
        _LOGGER.debug("Setting LED Brightness to %s%%", brightness)
        await self._manager.set_led_brightness(brightness)
        self.async_write_ha_state()


class VolcanoHeaterTemperatureSetpointNumber(NumberEntity):
    """Number entity to set Heater Temperature Setpoint."""

    def __init__(self, manager, config_entry):
        self._manager = manager
        self._config_entry = config_entry
        self._attr_name = "Volcano Heater Temperature Setpoint"
        self._attr_unique_id = f"volcano_heater_temperature_setpoint_{self._manager.bt_address}"
        self._attr_native_min_value = 40  # 40°C
        self._attr_native_max_value = 230  # 230°C
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._manager.bt_address)},
            "name": self._config_entry.data.get("device_name", "Volcano Vaporizer"),
            "manufacturer": "Storz & Bickel",
            "model": "Volcano Hybrid Vaporizer",
            "sw_version": self._manager.firmware_version or "1.0.0",
            "via_device": None,
        }

    @property
    def native_value(self):
        """Return the current Heater Temperature Setpoint."""
        return self._manager.heater_temperature_setpoint if self._manager.heater_temperature_setpoint else 100

    @property
    def available(self):
        """Return True if the number entity is available."""
        return self._manager.bt_status == "CONNECTED"

    async def async_set_native_value(self, value: float) -> None:
        """Set the Heater Temperature Setpoint."""
        temperature = int(value)
        _LOGGER.debug("Setting Heater Temperature Setpoint to %s°C", temperature)
        await self._manager.set_heater_temperature(temperature)
        self.async_write_ha_state()
