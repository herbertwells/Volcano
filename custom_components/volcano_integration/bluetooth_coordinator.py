"""Bluetooth Coordinator/Manager for the Volcano Integration."""
import asyncio
import logging
from bleak import BleakClient, BleakError

# Constants
BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"

# GATT Characteristic UUIDs
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"  # Current Temp
UUID_FAN_HEAT = "1010000c-5354-4f52-5a26-4249434b454c"  # Fan/Heat Notifications

# Reconnect interval in seconds
RECONNECT_INTERVAL = 3

_LOGGER = logging.getLogger(__name__)


class VolcanoBTManager:
    """Manages asynchronous connection to the Volcano device over Bluetooth.

    - Reads temperature every second.
    - Subscribes to notifications for Fan/Heat control changes.
    """

    def __init__(self):
        self._client = None
        self._connected = False

        # We will store the latest read values here:
        self.current_temperature = None
        self.fan_heat_status = None

        # We create a background task to manage connection and data flow
        self._task = None

    def start(self, hass):
        """Start background tasks in Home Assistant event loop."""
        _LOGGER.debug("Starting the VolcanoBTManager background task.")
        self._task = hass.loop.create_task(self._run())

    def stop(self):
        """Stop background tasks."""
        _LOGGER.debug("Stopping the VolcanoBTManager background task.")
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self):
        """Background loop to keep the device connected and gather data."""
        while True:
            # Ensure we're connected or attempt to connect
            if not self._connected:
                await self._connect()

            if self._connected:
                # Read temperature
                await self._read_temperature()

            # Sleep for 1 second between reads
            await asyncio.sleep(1)

    async def _connect(self):
        """Attempt to connect to the Bluetooth device."""
        try:
            _LOGGER.info("Attempting Bluetooth connection to device: %s", BT_DEVICE_ADDRESS)
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()
            self._connected = await self._client.is_connected()

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)

                # Start listening to notifications
                await self._subscribe_notifications()

            else:
                _LOGGER.warning("Connection to %s was not successful.", BT_DEVICE_ADDRESS)

        except BleakError as e:
            _LOGGER.error("Error connecting to device: %s | Retrying in %s seconds", e, RECONNECT_INTERVAL)
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_notifications(self):
        """Subscribe to Fan/Heat characteristic notifications."""
        if not self._connected or self._client is None:
            _LOGGER.error("Cannot subscribe to notifications - client not connected.")
            return

        # Notification callback
        def notification_handler(sender: int, data: bytearray):
            """Handle incoming notifications."""
            string_data = data.decode(errors="ignore")
            _LOGGER.debug("Received notification from %s: raw=%s, text='%s'", sender, data, string_data)
            self.fan_heat_status = string_data

        try:
            _LOGGER.info("Subscribing to notifications for UUID: %s", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
        except BleakError as e:
            _LOGGER.error("Failed to subscribe to notifications: %s", e)

    async def _read_temperature(self):
        """Read the Current Temperature characteristic."""
        if not self._connected or self._client is None:
            _LOGGER.warning("Not connected. Will attempt reconnect.")
            await self._disconnect()
            return

        try:
            # Attempt reading the temperature characteristic
            data = await self._client.read_gatt_char(UUID_TEMP)
            _LOGGER.debug("Temperature raw data: %s", data)

            # Parse raw bytes - just an example parse (assuming single float or int).
            # Adjust parse as per actual device data format.
            if len(data) == 2:
                # Example: 16-bit integer
                self.current_temperature = int.from_bytes(data, byteorder="little", signed=True)
            else:
                # Fallback for unknown data length - just log and store as None
                _LOGGER.warning("Unexpected temperature data length: %d", len(data))
                self.current_temperature = None

            _LOGGER.debug("Parsed temperature: %s", self.current_temperature)

        except BleakError as e:
            _LOGGER.error("Error reading temperature characteristic: %s", e)
            # Disconnect and attempt to reconnect
            await self._disconnect()

    async def _disconnect(self):
        """Disconnect and mark as disconnected."""
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
