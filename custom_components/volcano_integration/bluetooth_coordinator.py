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
    - Reads Temperature (and optionally RSSI) every ~1 second
    - Subscribes to Fan/Heat notifications
    - Tracks and exposes BT status & errors
    """

    def __init__(self, hass: HomeAssistant):
        """Initialize the VolcanoCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="VolcanoCoordinator",
            update_interval=None,  # We'll handle timing manually
        )
        self._client = None
        self._connected = False

        # We'll store updated info in self.data
        self.data = {
            "temperature": None,          # float (°C)
            "fan_heat_status": None,      # string from notifications
            "rssi": None,                 # int dBm (or None if unsupported)
            "bt_status": "DISCONNECTED",  # str: "CONNECTED", "DISCONNECTED", or "ERROR: ..."
        }

        # We'll schedule updates every second manually
        self._unsub_refresh = None

    async def async_config_entry_first_refresh(self):
        """
        Called by __init__ right after creation, to do immediate refresh & schedule next.
        """
        _LOGGER.debug("async_config_entry_first_refresh() called.")
        await self.async_refresh()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """
        Schedule the next refresh in 1s.
        If there's already a TimerHandle, cancel it before creating a new one.
        """
        _LOGGER.debug("Entered _schedule_refresh().")
        if self._unsub_refresh:
            _LOGGER.debug("Cancelling existing timer handle.")
            self._unsub_refresh.cancel()
            self._unsub_refresh = None

        _LOGGER.debug("Scheduling next refresh in %s second(s).", UPDATE_INTERVAL)
        self._unsub_refresh = self.hass.loop.call_later(
            UPDATE_INTERVAL,
            self._scheduled_refresh
        )

    def _scheduled_refresh(self):
        """Callback when the 1s timer fires. Create a task to refresh, then re-schedule."""
        _LOGGER.debug("_scheduled_refresh() fired -> calling async_refresh().")
        self.hass.async_create_task(self.async_refresh())

    async def async_refresh(self) -> None:
        """Override refresh to add scheduling logic (1 second)."""
        _LOGGER.debug("async_refresh() started -> calling super().async_refresh().")
        await super().async_refresh()
        _LOGGER.debug("async_refresh() done -> re-scheduling next update.")
        if self._unsub_refresh:
            _LOGGER.debug("Cancelling old timer before scheduling again.")
            self._unsub_refresh.cancel()
            self._unsub_refresh = None
        self._schedule_refresh()

    async def _async_update_data(self):
        """
        Called by DataUpdateCoordinator to fetch fresh data.
        We do single read ops (temp & optional RSSI). If not connected, attempt to connect.
        """
        _LOGGER.debug("Entering _async_update_data(): connected=%s, bt_status=%s",
                      self._connected, self.data["bt_status"])

        if not self._connected:
            self.data["bt_status"] = "CONNECTING"
            try:
                _LOGGER.debug("Creating BleakClient and connecting to %s.", BT_DEVICE_ADDRESS)
                self._client = BleakClient(BT_DEVICE_ADDRESS)
                await self._client.connect()

                # `is_connected` is now a property in HaBleakClientWrapper
                self._connected = self._client.is_connected
                if self._connected:
                    _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                    self.data["bt_status"] = "CONNECTED"
                    # Subscribe once
                    await self._subscribe_fan_heat_notifications()
                else:
                    _LOGGER.warning("Connection to %s was not successful.", BT_DEVICE_ADDRESS)
                    self.data["bt_status"] = "DISCONNECTED"
                    raise UpdateFailed("Could not connect to device.")
            except BleakError as e:
                error_str = f"ERROR: {str(e)}"
                _LOGGER.error("Bluetooth connection error: %s", error_str)
                self.data["bt_status"] = error_str
                raise UpdateFailed(error_str)

        # If connected, try reading data:
        if self._connected and self._client:
            try:
                async with async_timeout.timeout(5):
                    _LOGGER.debug("Reading temperature from device.")
                    await self._read_temperature()

                    _LOGGER.debug("Trying to read RSSI (may be unsupported).")
                    try:
                        await self._read_rssi()
                    except AttributeError as ae:
                        _LOGGER.debug("RSSI not supported on this backend (%s). Setting to None.", ae)
                        self.data["rssi"] = None

            except BleakError as e:
                error_str = f"ERROR: {str(e)}"
                _LOGGER.error("Bleak error while reading data: %s", error_str)
                self.data["bt_status"] = error_str
                await self._disconnect()
                raise UpdateFailed(error_str)
            except Exception as ex:
                error_str = f"ERROR: {str(ex)}"
                _LOGGER.error("Unknown error while reading data: %s", error_str)
                self.data["bt_status"] = error_str
                await self._disconnect()
                raise UpdateFailed(error_str)

        _LOGGER.debug("Leaving _async_update_data() -> returning data: %s", self.data)
        return self.data

    async def _subscribe_fan_heat_notifications(self):
        """Set up notifications for the fan/heat characteristic."""
        _LOGGER.debug("Entered _subscribe_fan_heat_notifications().")
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            text = data.decode(errors="ignore")
            _LOGGER.debug("Fan/Heat notification: raw=%s, text='%s'", data, text)
            self.data["fan_heat_status"] = text

        try:
            _LOGGER.debug("start_notify(%s) for fan/heat.", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
        except BleakError as e:
            error_str = f"ERROR: {str(e)}"
            _LOGGER.error("Failed to subscribe to notifications: %s", error_str)
            self.data["bt_status"] = error_str

    async def _read_temperature(self):
        """Read the temperature characteristic."""
        _LOGGER.debug("Entered _read_temperature().")
        if not self._client or not self._connected:
            raise BleakError("Client not connected.")

        data = await self._client.read_gatt_char(UUID_TEMP)
        _LOGGER.debug("Temperature raw (hex) = %s", data.hex())

        if len(data) < 2:
            _LOGGER.warning("Expected >= 2 bytes for temperature, got %d", len(data))
            self.data["temperature"] = None
            return

        # Parse first 2 bytes as an unsigned 16-bit integer in little-endian
        raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
        # Typically device is storing tenths of a degree
        temp_c = raw_16 / 10.0
        self.data["temperature"] = temp_c
        _LOGGER.debug("Parsed temperature = %.1f °C (raw_16=%d)", temp_c, raw_16)

    async def _read_rssi(self):
        """
        Attempt to read device RSSI. 
        Some Bleak backends or HaBleakClientWrapper might not implement get_rssi().
        We'll handle AttributeError if it's missing.
        """
        _LOGGER.debug("Entered _read_rssi().")
        if not self._client or not self._connected:
            raise BleakError("Client not connected.")

        rssi = await self._client.get_rssi()  # May raise AttributeError or BleakError
        if rssi is not None:
            _LOGGER.debug("Read RSSI = %s dBm", rssi)
            self.data["rssi"] = rssi
        else:
            _LOGGER.debug("RSSI returned None -> not supported or unknown.")
            self.data["rssi"] = None

    async def _disconnect(self):
        """Disconnect from the device so next update can try reconnect."""
        _LOGGER.debug("_disconnect() called. Setting bt_status=DISCONNECTED.")
        if self._client:
            _LOGGER.debug("Disconnecting from device.")
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)
        self._connected = False
        self.data["bt_status"] = "DISCONNECTED"
        _LOGGER.debug("Done _disconnect(): connected=%s, bt_status=%s",
                      self._connected, self.data["bt_status"])

    async def async_unload(self):
        """
        Clean up coordinator (cancel timer, disconnect, etc.) on unload.
        Called from __init__.py async_unload_entry or on shutdown.
        """
        _LOGGER.debug("async_unload() called, canceling timer & disconnecting.")
        if self._unsub_refresh:
            _LOGGER.debug("Canceling refresh timer in async_unload().")
            self._unsub_refresh.cancel()
            self._unsub_refresh = None
        await self._disconnect()
        _LOGGER.debug("Finished async_unload().")
