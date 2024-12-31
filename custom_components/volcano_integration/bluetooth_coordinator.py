"""Bluetooth Coordinator for the Volcano Integration, using a continuous background loop."""
import asyncio
import logging

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"
UUID_TEMP = "10110001-5354-4f52-5a26-4249434b454c"
UUID_FAN_HEAT = "1010000c-5354-4f52-5a26-4249434b454c"

RECONNECT_INTERVAL = 3
POLL_INTERVAL = 1

class VolcanoBTManager:
    """
    Manages an ongoing background task to read temperature & subscribe to notifications
    on a 1-second loop.
    """

    def __init__(self):
        self._client = None
        self._connected = False

        self.current_temperature = None
        self.fan_heat_status = None
        self.bt_status = "DISCONNECTED"

        # Task control
        self._task = None
        self._stop_event = asyncio.Event()

        # List of sensors that want immediate updates
        self._sensors = []

    def register_sensor(self, sensor_entity):
        """Allow a sensor entity to register for immediate notifications."""
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        """Remove a sensor from the update list."""
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    def start(self, hass):
        """Start the background loop in Home Assistant's event loop."""
        _LOGGER.debug("VolcanoBTManager.start() -> creating background task.")
        self._stop_event.clear()
        self._task = hass.loop.create_task(self._run())

    def stop(self):
        """Stop the background loop by signaling the event and waiting for the task to end."""
        _LOGGER.debug("VolcanoBTManager.stop() -> stopping background task.")
        if self._task and not self._task.done():
            self._stop_event.set()

    async def _run(self):
        """Main loop: connect if needed, read temperature every second, handle reconnects."""
        _LOGGER.debug("Entering VolcanoBTManager._run() loop.")
        while not self._stop_event.is_set():
            if not self._connected:
                await self._connect()

            if self._connected:
                # Try reading temperature
                await self._read_temperature()

            # Wait 1 second, then do it again
            await asyncio.sleep(POLL_INTERVAL)

        _LOGGER.debug("Exiting VolcanoBTManager._run() loop -> disconnecting.")
        await self._disconnect()

    async def _connect(self):
        """Attempt to connect to the device."""
        try:
            self.bt_status = "CONNECTING"
            _LOGGER.info("Attempting connection to Bluetooth device %s", BT_DEVICE_ADDRESS)
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()

            self._connected = self._client.is_connected
            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = "CONNECTED"
                await self._subscribe_notifications()
            else:
                _LOGGER.warning("Connection to %s was not successful.", BT_DEVICE_ADDRESS)
                self.bt_status = "DISCONNECTED"
                await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            error_str = f"ERROR: {e}"
            _LOGGER.error("Bluetooth connect error: %s", error_str)
            self.bt_status = error_str
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _subscribe_notifications(self):
        """Subscribe to fan/heat notifications once we are connected."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            text = data.decode(errors="ignore")
            _LOGGER.debug("Fan/Heat notification: sender=%s, data=%s, text='%s'", sender, data, text)
            self.fan_heat_status = text
            self._notify_sensors()

        try:
            _LOGGER.debug("Subscribing to notifications on UUID %s", UUID_FAN_HEAT)
            await self._client.start_notify(UUID_FAN_HEAT, notification_handler)
        except BleakError as e:
            error_str = f"ERROR subscribing to notifications: {e}"
            _LOGGER.error(error_str)
            self.bt_status = error_str

    async def _read_temperature(self):
        """Read the temperature characteristic every second."""
        if not self._connected or not self._client:
            _LOGGER.debug("Not connected -> skipping temperature read.")
            return

        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            _LOGGER.debug("Read temperature raw bytes: %s", data.hex())

            if len(data) < 2:
                _LOGGER.warning("Temperature data too short: %d bytes", len(data))
                self.current_temperature = None
            else:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
                _LOGGER.debug("Parsed temperature = %.1f °C (raw=%d)", self.current_temperature, raw_16)

            # Notify sensors so they can push immediate update
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
            _LOGGER.debug("Disconnecting Bluetooth client.")
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)

        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"
        _LOGGER.info("Disconnected from device. Will retry on next connect cycle.")
