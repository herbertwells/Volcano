"""Bluetooth Coordinator for the Volcano Integration."""

import asyncio
import logging

from bleak import BleakClient, BleakError

_LOGGER = logging.getLogger(__name__)

# Replace with your device's MAC address
BT_DEVICE_ADDRESS = "CE:9E:A6:43:25:F3"

# Timings
RECONNECT_INTERVAL = 3      # Seconds before attempting to reconnect
TEMP_POLL_INTERVAL = 1      # Seconds between temperature polls

# Pump patterns: (heat_byte, pump_byte)
VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
    (0x23, 0x06): ("BURST_STARTED", "ON"),
    (0x23, 0x26): ("BURST_ENDED", "ON"),
}


class VolcanoBTManager:
    """
    Manages Bluetooth communication with the Volcano device.

    Responsibilities:
      - Connects to the device.
      - Polls temperature every TEMP_POLL_INTERVAL seconds.
      - Subscribes to pump notifications.
      - Handles Pump and Heat On/Off commands.
      - Allows setting the heater temperature.
      - Manages connection status and reconnection logic.
      - Provides services for button actions and set_temperature.
    """

    def __init__(self):
        self._client = None
        self._connected = False
        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self._bt_status = "DISCONNECTED"  # Explicitly initialize as DISCONNECTED
        self._run_task = None
        self._temp_poll_task = None
        self._stop_event = asyncio.Event()
        self._sensors = []
        self.slot_bluetooth_error = False

    @property
    def bt_status(self):
        """Return the current Bluetooth status."""
        return self._bt_status

    @bt_status.setter
    def bt_status(self, value):
        """Set the Bluetooth status and notify sensors/buttons."""
        if self._bt_status != value:
            _LOGGER.debug("BT status changed from %s to %s", self._bt_status, value)
            self._bt_status = value
            self._notify_sensors()

    def register_sensor(self, sensor_entity):
        """Register a sensor to receive updates."""
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        """Unregister a sensor from receiving updates."""
        if sensor_entity in self._sensors:
            self._sensors.remove(sensor_entity)

    async def start(self):
        """Start the Bluetooth manager (only on user request)."""
        if not self._run_task or self._run_task.done():
            self._stop_event.clear()
            self._run_task = asyncio.create_task(self._run())
            self._temp_poll_task = asyncio.create_task(self._poll_temperature())

    async def stop(self):
        """Stop the Bluetooth manager."""
        if self._run_task and not self._run_task.done():
            self._stop_event.set()
            await self._run_task
        if self._temp_poll_task and not self._temp_poll_task.done():
            self._temp_poll_task.cancel()
            try:
                await self._temp_poll_task
            except asyncio.CancelledError:
                pass
        self.bt_status = "DISCONNECTED"  # Explicitly set status on stop

    async def async_user_connect(self):
        """Explicitly initiate a connection to the BLE device."""
        _LOGGER.debug("User requested connection to the Volcano device.")
        if self._connected:
            _LOGGER.info("Already connected to the device.")
            return
        await self.start()

    async def async_user_disconnect(self):
        """Explicitly disconnect from the BLE device."""
        _LOGGER.debug("User requested disconnection from the Volcano device.")
        if not self._connected:
            _LOGGER.info("Already disconnected from the device.")
            return
        await self.stop()

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
            self._client = BleakClient(BT_DEVICE_ADDRESS)
            await self._client.connect()

            self._connected = self._client.is_connected

            if self._connected:
                _LOGGER.info("Bluetooth connected to %s", BT_DEVICE_ADDRESS)
                self.bt_status = "CONNECTED"
                await self._subscribe_pump_notifications()
            else:
                self.bt_status = "DISCONNECTED"
        except BleakError as e:
            if "slot Bluetooth" in str(e):
                _LOGGER.error("Critical slot Bluetooth error: %s", e)
            else:
                _LOGGER.warning("Bluetooth connection warning: %s -> Retrying...", e)
            self.bt_status = "ERROR"
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _poll_temperature(self):
        """Poll temperature at regular intervals."""
        while not self._stop_event.is_set():
            if self._connected:
                await self._read_temperature()
            await asyncio.sleep(TEMP_POLL_INTERVAL)

    async def _read_temperature(self):
        """Read the temperature characteristic."""
        if not self._connected or not self._client:
            return
        try:
            data = await self._client.read_gatt_char(self.UUID_TEMP)
            if len(data) >= 2:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s -> disconnect & retry...", e)
            self.bt_status = "ERROR"
            await self._disconnect()

    def _notify_sensors(self):
        """Notify all registered sensors that new data is available."""
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        """Disconnect from the BLE device."""
        if self._client:
            try:
                await self._client.disconnect()
            except BleakError as e:
                _LOGGER.warning("Bluetooth disconnection warning: %s", e)
        self._client = None
        self._connected = False
        self.bt_status = "DISCONNECTED"

    async def write_gatt_command(self, write_uuid: str, payload: bytes = b""):
        """Write a payload to a GATT characteristic to control Pump/Heat."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot write to %s - not connected.", write_uuid)
            return

        try:
            _LOGGER.debug("Writing GATT char %s -> payload %s", write_uuid, payload.hex())
            await self._client.write_gatt_char(write_uuid, payload)
            _LOGGER.info("Successfully wrote to %s", write_uuid)
        except BleakError as e:
            _LOGGER.error("Error writing to %s: %s", write_uuid, e)

    async def set_heater_temperature(self, temp_c: float):
        """Write the temperature setpoint to the heater's GATT characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set heater temperature - not connected.")
            return

        safe_temp = max(40.0, min(temp_c, 230.0))
        setpoint_bytes = int(safe_temp * 10).to_bytes(2, byteorder="little")

        _LOGGER.debug("Writing heater temperature=%.1f °C -> raw=%s", safe_temp, setpoint_bytes.hex())
        try:
            await self._client.write_gatt_char(self.UUID_HEATER_SETPOINT, setpoint_bytes)
            _LOGGER.info("Heater setpoint updated to %.1f °C", safe_temp)
        except BleakError as e:
            _LOGGER.error("Error writing heater temp: %s", e)
