"""Bluetooth Coordinator for the Volcano Integration, with both temperature polling and fan/heat notifications."""
import asyncio
import logging

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

# The static Bluetooth MAC address
BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"

# GATT Characteristic UUIDs
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"     # Current Temperature
UUID_FAN_HEAT = "1010000c-5354-4f52-5a26-4249434b454c" # Fan/Heat Notifications

# Connection/Retry Intervals
RECONNECT_INTERVAL = 3          # Wait 3 seconds before reconnect attempts
POLL_INTERVAL = 0.5             # Poll temperature every 0.5 seconds (twice per second)

class VolcanoBTManager:
    """
    Manages an ongoing background task to:
    - Connect to the BLE device
    - Poll the temperature every 0.5 seconds
    - Subscribe to fan/heat notifications
    - Expose `current_temperature` and `fan_heat_status` to sensor entities
    - Provide a `bt_status` (CONNECTED, DISCONNECTED, ERROR, etc.)
    """

    def __init__(self):
        self._client = None
        self._connected = False

        # Public data read by sensor.py
        self.current_temperature = None
        self.fan_heat_status = None
        self.bt_status = "DISCONNECTED"

        # Async tasks
        self._task = None
        self._stop_event = asyncio.Event()

        # Keep track of sensor entities to notify about new data
        self._sensors = []

    def register_sensor(self, sensor_entity):
        """Allow a sensor entity to register for immediate notifications."""
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        """Unregister a previously registered sensor."""
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    def start(self, hass):
        """
        Start the background loop in Home Assistant's event loop.
        This continuously attempts to connect, reads temperature every 0.5s,
        and listens for fan/heat notifications.
        """
        _LOGGER.debug("VolcanoBTManager.start() -> creating background task.")
        self._stop_event.clear()
        self._task = hass.loop.create_task(self._run())

    def stop(self):
        """
        Stop the background loop by signaling our event,
        which will disconnect and clean up on exit.
        """
        _LOGGER.debug("VolcanoBTManager.stop() -> stopping background task.")
        if self._task and not self._task.done():
            self._stop_event.set()

    async def _run(self):
        """Main loop: connect if needed, poll temperature, handle reconnects, etc."""
        _LOGGER.debug("Entering VolcanoBTManager._run() loop.")
        while not self._stop_event.is_set():
            if not self._connected:
                await self._connect()

            if self._connected:
                # Poll temperature
                await self._read_temperature()

            # Sleep 0.5 seconds, then loop
            await asyncio.sleep(POLL_INTERVAL)

        _LOGGER.debug("Exiting VolcanoBTManager._run() -> disconnecting.")
        await self._disconnect()

    async def _connect(self):
        """Attempt to connect to the device."""
        try:
            _LOGGER.info("Connecting to Bluetooth device %s...", BT_DEVICE_ADDRESS)
            self.bt_status = "CONNECTING"

            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()

            # Bleak >= 0.20 => is_connected is a property
            self._connected = self._client.is_connected

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = "CONNECTED"
                # Subscribe to fan/heat notifications
                await self._subscribe_notifications()
            else:
                _LOGGER.warning(
                    "Connection to %s was not successful. Retrying in %s sec...",
                    BT_DEVICE_ADDRESS,
                    RECONNECT_INTERVAL
                )
                self.bt_status = "DISCONNECTED"
                await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            err_str = f"ERROR: {e}"
            _LOGGER.error(
                "Bluetooth connect error to %s: %s -> Retrying in %s sec...",
                BT_DEVICE_ADDRESS,
                err_str,
                RECONNECT_INTERVAL
            )
            self.bt_status = err_str
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_notifications(self):
        """Subscribe to fan/heat notifications once we are connected."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to fan/heat notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            """Called whenever the device pushes data on the Fan/Heat UUID."""
            text = data.decode(errors="ignore")
            _LOGGER.debug(
                "Fan/Heat notification -> sender=%s, raw_data=%s, text='%s'",
                sender, data, text
            )
            self.fan_heat_status = text
            self._notify_sensors()

        try:
            _LOGGER.info("Subscribing to fan/heat notifications on UUID %s", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
            _LOGGER.debug("Fan/Heat subscription active.")
        except BleakError as e:
            err_str = f"ERROR subscribing to fan/heat: {e}"
            _LOGGER.error(err_str)
            self.bt_status = err_str

    async def _read_temperature(self):
        """Read the temperature characteristic."""
        if not self._connected or not self._client:
            _LOGGER.debug("Not connected -> skipping temperature read.")
            return

        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            _LOGGER.debug("Read temperature raw bytes: %s", data.hex())

            if len(data) < 2:
                _LOGGER.warning("Temperature data too short: %d byte(s)", len(data))
                self.current_temperature = None
            else:
                # Parse first 2 bytes as 16-bit little-endian => /10
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
                _LOGGER.debug(
                    "Parsed temperature = %.1f °C (raw=%d)",
                    self.current_temperature,
                    raw_16
                )

            self._notify_sensors()

        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s. Disconnect & retry soon.", e)
            self.bt_status = f"ERROR: {e}"
            await self._disconnect()

    def _notify_sensors(self):
        """
        Informs any registered sensors that new data is available.
        They can call `async_write_ha_state()` to update the UI immediately.
        """
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        """Disconnect from the device so we can attempt to reconnect next cycle."""
        if self._client:
            _LOGGER.debug("Disconnecting from device %s.", BT_DEVICE_ADDRESS)
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)

        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"
        _LOGGER.info("Disconnected from device %s. Will retry later.", BT_DEVICE_ADDRESS)
