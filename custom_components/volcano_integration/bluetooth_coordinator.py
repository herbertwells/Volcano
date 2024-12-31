"""Bluetooth Coordinator/Manager for the Volcano Integration."""
import asyncio
import logging

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

# Static GATT/Bluetooth Info
BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"    # Current Temperature
UUID_FAN_HEAT = "1010000c-5354-4f52-5a26-4249434b454c"  # Fan/Heat Notifications

RECONNECT_INTERVAL = 3
TEMP_POLL_INTERVAL = 1


class VolcanoBTManager:
    """Manages asynchronous connection to the Volcano device over Bluetooth."""

    def __init__(self):
        self._client = None
        self._connected = False

        # Store raw data (as a string) for current temperature
        self.current_temperature_raw = None

        # Store the last notification string for fan/heat
        self.fan_heat_status = None

        self._task = None

    def start(self, hass):
        """Start the background loop in Home Assistant's event loop."""
        _LOGGER.debug("Starting the VolcanoBTManager background task.")
        if not self._task:
            self._task = hass.loop.create_task(self._run())

    def stop(self):
        """Stop the background task."""
        _LOGGER.debug("Stopping the VolcanoBTManager background task.")
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self):
        """Background loop: connect if needed, read temperature, etc."""
        while True:
            if not self._connected:
                await self._connect()

            if self._connected:
                await self._read_temperature()

            await asyncio.sleep(TEMP_POLL_INTERVAL)

    async def _connect(self):
        """Attempt to connect to the Bluetooth device."""
        try:
            _LOGGER.info("Attempting Bluetooth connection to: %s", BT_DEVICE_ADDRESS)
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()
            self._connected = await self._client.is_connected()

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                await self._subscribe_notifications()
            else:
                _LOGGER.warning("Connection to %s was not successful.", BT_DEVICE_ADDRESS)

        except BleakError as e:
            _LOGGER.error("Error connecting to device: %s | Retrying in %s seconds", e, RECONNECT_INTERVAL)
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_notifications(self):
        """Subscribe to the fan/heat notifications."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to notifications - client not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            string_data = data.decode(errors="ignore")
            _LOGGER.debug("Received notification from %s: raw=%s, text='%s'", sender, data, string_data)
            self.fan_heat_status = string_data

        try:
            _LOGGER.info("Subscribing to notifications on UUID: %s", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
        except BleakError as e:
            _LOGGER.error("Failed to subscribe to notifications: %s", e)

    async def _read_temperature(self):
        """Read the 'Current Temperature' characteristic as raw data."""
        if not self._connected or not self._client:
            _LOGGER.warning("Not connected. Will attempt reconnect.")
            await self._disconnect()
            return

        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            # Store it as a hex string (or however you'd like)
            self.current_temperature_raw = data.hex()
            _LOGGER.debug("Temperature raw data (hex): %s", self.current_temperature_raw)

        except BleakError as e:
            _LOGGER.error("Error reading temperature characteristic: %s", e)
            await self._disconnect()

    async def _disconnect(self):
        """Disconnect and schedule a retry."""
        if self._client:
            _LOGGER.info("Disconnecting from Bluetooth device.")
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)

        self._client = None
        self._connected = False
        _LOGGER.info("Disconnected. Will retry in %s seconds.", RECONNECT_INTERVAL)
        await asyncio.sleep(RECONNECT_INTERVAL)
