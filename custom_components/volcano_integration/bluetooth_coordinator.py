"""Bluetooth Coordinator for the Volcano Integration using DataUpdateCoordinator."""
import logging
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

# Static addresses/UUIDs
BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"    # Current Temperature
UUID_FAN_HEAT = "1010000c-5354-4f52-5a26-4249434b454c"  # Fan/Heat Notifications

# How often we poll for data (1 second)
UPDATE_INTERVAL = 1.0


class VolcanoCoordinator(DataUpdateCoordinator):
    """
    A DataUpdateCoordinator that:
    - Connects via Bleak
    - Reads Temperature and RSSI every 1 second
    - Subscribes to Fan/Heat notifications
    - Tracks and exposes BT status & errors
    """

    def __init__(self, hass: HomeAssistant):
        """Initialize the VolcanoCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="VolcanoCoordinator",
            update_interval=None,  # We'll handle timing in _async_update_data
        )
        self._client = None
        self._connected = False

        # We'll store updated info in self.data
        # Start with all None or defaults
        self.data = {
            "temperature": None,         # float (°C)
            "fan_heat_status": None,     # string from notifications
            "rssi": None,               # int dBm
            "bt_status": "DISCONNECTED"  # str with possible "CONNECTED", or "ERROR: ..."
        }

        # We subscribe to updates every 1s, but we rely on
        # self._schedule_refresh for the timing (below).
        self._unsub_refresh = None

    async def async_config_entry_first_refresh(self):
        """Called by __init__ right after creation, to do immediate refresh & schedule next."""
        # Do one immediate refresh
        await self.async_refresh()
        # Schedule future refreshes at 1-second intervals
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedule the next refresh in 1s, repeatedly."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        self._unsub_refresh = self.hass.loop.call_later(UPDATE_INTERVAL, self._scheduled_refresh)

    def _scheduled_refresh(self):
        """Callback when the 1s timer fires."""
        self.hass.async_create_task(self.async_refresh())

    async def async_refresh(self) -> None:
        """Override refresh to add scheduling logic."""
        await super().async_refresh()
        # After the refresh is done, schedule again
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None
        self._schedule_refresh()

    async def _async_update_data(self):
        """
        This is called by DataUpdateCoordinator to fetch the data.
        We have up to self.update_interval or manual scheduling.

        Return updated data dict or raise UpdateFailed.
        """
        # We'll do a single read operation (temp + RSSI).
        # If not connected, attempt to connect.

        if not self._connected:
            self.data["bt_status"] = "CONNECTING"
            try:
                _LOGGER.debug("Attempting Bluetooth connection to %s", BT_DEVICE_ADDRESS)
                self._client = BleakClient(BT_DEVICE_ADDRESS)
                await self._client.connect()
                self._connected = await self._client.is_connected()
                if self._connected:
                    _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                    self.data["bt_status"] = "CONNECTED"
                    # Subscribe once
                    await self._subscribe_fan_heat_notifications()
                else:
                    # Not connected
                    _LOGGER.warning("Connection to %s was not successful.", BT_DEVICE_ADDRESS)
                    self.data["bt_status"] = "DISCONNECTED"
                    raise UpdateFailed("Could not connect to device.")
            except BleakError as e:
                error_str = f"ERROR: {str(e)}"
                _LOGGER.error("Bluetooth connection error: %s", error_str)
                self.data["bt_status"] = error_str
                raise UpdateFailed(error_str)

        # If connected, try reading data. If it fails, we set an error status.
        if self._connected and self._client:
            try:
                async with async_timeout.timeout(5):
                    await self._read_temperature()
                    await self._read_rssi()
            except BleakError as e:
                error_str = f"ERROR: {str(e)}"
                _LOGGER.error("Bleak error while reading data: %s", error_str)
                self.data["bt_status"] = error_str
                # We'll attempt to disconnect so next update tries to reconnect
                await self._disconnect()
                # Raising UpdateFailed so coordinator logs error
                raise UpdateFailed(error_str)
            except Exception as ex:
                error_str = f"ERROR: {str(ex)}"
                _LOGGER.error("Unknown error while reading data: %s", error_str)
                self.data["bt_status"] = error_str
                await self._disconnect()
                raise UpdateFailed(error_str)

        return self.data

    async def _subscribe_fan_heat_notifications(self):
        """Set up notifications for the fan/heat characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            text = data.decode(errors="ignore")
            _LOGGER.debug("Fan/Heat notification: raw=%s, text='%s'", data, text)
            self.data["fan_heat_status"] = text

        try:
            _LOGGER.debug("Subscribing to notifications on UUID: %s", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
        except BleakError as e:
            error_str = f"ERROR: {str(e)}"
            _LOGGER.error("Failed to subscribe to notifications: %s", error_str)
            self.data["bt_status"] = error_str

    async def _disconnect(self):
        """Disconnect from the device so next update can try reconnect."""
        if self._client:
            _LOGGER.debug("Disconnecting from device.")
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)
        self._connected = False
        self.data["bt_status"] = "DISCONNECTED"

    async def _read_temperature(self):
        """Read the temperature characteristic."""
        if not self._client or not self._connected:
            raise BleakError("Client not connected.")

        data = await self._client.read_gatt_char(UUID_TEMP)
        _LOGGER.debug("Temperature raw (hex) = %s", data.hex())

        if len(data) < 2:
            _LOGGER.warning("Expected at least 2 bytes for temperature, got %d", len(data))
            self.data["temperature"] = None
            return

        # Parse first two bytes as an unsigned 16-bit integer in little-endian
        raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
        # Typically device is storing tenths of a degree
        temp_c = raw_16 / 10.0
        self.data["temperature"] = temp_c
        _LOGGER.debug("Parsed temperature = %.1f °C (raw_16=%d)", temp_c, raw_16)

    async def _read_rssi(self):
        """Attempt to read the device RSSI. Not all Bleak backends support get_rssi()."""
        if not self._client or not self._connected:
            raise BleakError("Client not connected.")

        # Some backends support BleakClient.get_rssi(), others do not.
        # If not supported, you may get an exception or always get None.
        try:
            rssi = await self._client.get_rssi()
            if rssi is not None:
                _LOGGER.debug("Read RSSI = %s dBm", rssi)
                self.data["rssi"] = rssi
            else:
                _LOGGER.debug("RSSI not supported on this backend.")
                self.data["rssi"] = None
        except NotImplementedError:
            _LOGGER.debug("get_rssi() not implemented on this platform.")
            self.data["rssi"] = None
        except BleakError as e:
            raise UpdateFailed(f"RSSI read error: {str(e)}")

    async def async_unload(self):
        """Clean up coordinator (disconnect, etc.) when integration is unloaded."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None
        await self._disconnect()
