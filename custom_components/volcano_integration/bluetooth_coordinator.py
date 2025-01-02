"""Bluetooth Coordinator for the Volcano Integration.

Refactored for improved connection stability, error handling, and task management.
"""
import asyncio
import logging
from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"

# Timings
RECONNECT_INTERVAL_INITIAL = 3  # Initial retry interval in seconds
MAX_RECONNECT_INTERVAL = 30    # Max retry interval in seconds
TEMP_POLL_INTERVAL = 1         # Seconds between temperature polls

# Pump patterns: (heat_byte, pump_byte)
VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
    (0x23, 0x06): ("ON - TARGET MET (BURSTING)", "ON"),  # Start of burst
    (0x23, 0x26): ("ON - TARGET MET", "ON"),    # End of burst
    (0x23, 0x36): ("ON - OVER TARGET", "ON"),   # Over target temperature
}

class VolcanoBTManager:
    """
    Manages Bluetooth communication with the Volcano device.
    """

    def __init__(self):
        self._client = None
        self._connected = False

        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self.temperature_target_status = "Unavailable"

        self.bt_status = "DISCONNECTED"

        self._run_task = None
        self._temp_poll_task = None
        self._stop_event = asyncio.Event()
        self._sensors = []

        self.reconnect_interval = RECONNECT_INTERVAL_INITIAL

    def register_sensor(self, sensor_entity):
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    async def start(self):
        if not self._run_task or self._run_task.done():
            self._stop_event.clear()
            self.reconnect_interval = RECONNECT_INTERVAL_INITIAL
            self._run_task = asyncio.create_task(self._run())
            self._temp_poll_task = asyncio.create_task(self._poll_temperature())

    async def stop(self):
        if self._run_task and not self._run_task.done():
            self._stop_event.set()
            await self._run_task
        if self._temp_poll_task and not self._temp_poll_task.done():
            self._temp_poll_task.cancel()
            try:
                await self._temp_poll_task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        """Main loop to manage Bluetooth connection."""
        _LOGGER.debug("Entering VolcanoBTManager._run() loop.")
        while not self._stop_event.is_set():
            if not self._connected:
                await self._connect()

            await asyncio.sleep(1)

        _LOGGER.debug("Exiting VolcanoBTManager._run() -> disconnecting.")
        await self._disconnect()

    async def _connect(self):
        """Attempt to connect to the BLE device."""
        try:
            _LOGGER.info("Connecting to Bluetooth device %s...", BT_DEVICE_ADDRESS)
            self.bt_status = "CONNECTING"

            async with BleakClient(BT_DEVICE_ADDRESS) as client:
                self._client = client
                self._connected = client.is_connected

                if self._connected:
                    _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                    self.bt_status = "CONNECTED"
                    self.reconnect_interval = RECONNECT_INTERVAL_INITIAL  # Reset interval
                    await self._subscribe_pump_notifications()
                else:
                    raise BleakError("Failed to establish a connection.")
        except BleakError as e:
            _LOGGER.error("Bluetooth connect error: %s", e)
            _LOGGER.debug("Retrying connection in %d seconds", self.reconnect_interval)
            self.bt_status = "DISCONNECTED"
            await asyncio.sleep(self.reconnect_interval)
            self.reconnect_interval = min(
                self.reconnect_interval * 2, MAX_RECONNECT_INTERVAL
            )

    async def _subscribe_pump_notifications(self):
        if not self._connected or not self._client:
            _LOGGER.error("Cannot subscribe to pump notifications: not connected.")
            return

        def notification_handler(sender: int, data: bytearray):
            _LOGGER.debug("Pump notification raw: %s", data.hex())
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                _LOGGER.debug("Received bytes: 0x%02x 0x%02x", b1, b2)

                if (b1, b2) in VALID_PATTERNS:
                    heat_val, pump_val = VALID_PATTERNS[(b1, b2)]
                    self.heat_state = heat_val
                    self.pump_state = pump_val
                    _LOGGER.info("Parsed pump notification -> heat: %s, pump: %s", heat_val, pump_val)
                else:
                    _LOGGER.warning("Unknown pump pattern: (0x%02x, 0x%02x)", b1, b2)
            else:
                _LOGGER.warning("Received incomplete notification data.")
            self._notify_sensors()

        try:
            _LOGGER.info("Subscribing to pump notifications.")
            await self._client.start_notify("1010000c-5354-4f52-5a26-4249434b454c", notification_handler)
            _LOGGER.debug("Pump notifications subscription successful.")
        except BleakError as e:
            _LOGGER.error("Error subscribing to notifications: %s", e)

    async def _poll_temperature(self):
        while not self._stop_event.is_set():
            if self._connected:
                await self._read_temperature()
            else:
                _LOGGER.debug("Skipping temperature poll: not connected.")
            await asyncio.sleep(TEMP_POLL_INTERVAL)

    async def _read_temperature(self):
        if not self._connected or not self._client:
            _LOGGER.debug("Not connected -> skipping temperature read.")
            return

        try:
            _LOGGER.debug("Attempting to read temperature from UUID 10110001-5354-4f52-5a26-4249434b454c.")
            data = await self._client.read_gatt_char("10110001-5354-4f52-5a26-4249434b454c")
            if len(data) >= 2:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
                _LOGGER.info("Current temperature: %.1f °C", self.current_temperature)
            else:
                _LOGGER.warning("Temperature data too short: %d bytes", len(data))

            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s", e)
            self.bt_status = "ERROR"
            await self._disconnect()

    def _notify_sensors(self):
        _LOGGER.debug("Notifying %d sensors of updated state.", len(self._sensors))
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        if self._client:
            _LOGGER.debug("Disconnecting from device %s.", BT_DEVICE_ADDRESS)
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.error("Error during disconnect: %s", e)
        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"
        _LOGGER.info("Disconnected from device %s.", BT_DEVICE_ADDRESS)

    async def async_user_connect(self):
        _LOGGER.debug("User initiated Bluetooth connection.")
        await self.start()

    async def async_user_disconnect(self):
        _LOGGER.debug("User initiated Bluetooth disconnection.")
        await self.stop()
        self.bt_status = "DISCONNECTED"
        self._notify_sensors()
