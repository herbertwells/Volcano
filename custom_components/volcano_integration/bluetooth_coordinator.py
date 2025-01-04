import asyncio
import logging

from bleak import BleakClient, BleakError
from .const import (
    UUID_TEMP,
    UUID_PUMP_NOTIFICATIONS,
    UUID_PUMP_ON,
    UUID_PUMP_OFF,
    UUID_HEAT_ON,
    UUID_HEAT_OFF,
    UUID_HEATER_SETPOINT,
    BT_STATUS_DISCONNECTED,
    BT_STATUS_CONNECTING,
    BT_STATUS_CONNECTED,
    BT_STATUS_ERROR,
    UUID_BLE_FIRMWARE_VERSION,
    UUID_SERIAL_NUMBER,
)

_LOGGER = logging.getLogger(__name__)

# Timings
RECONNECT_INTERVAL = 3  # Seconds before attempting to reconnect
TEMP_POLL_INTERVAL = 1  # Seconds between temperature polls

# Pump patterns: (heat_byte, pump_byte)
VALID_PATTERNS = {
    (0x23, 0x00): ("ON", "OFF"),
    (0x00, 0x00): ("OFF", "OFF"),
    (0x00, 0x30): ("OFF", "ON"),
    (0x23, 0x30): ("ON", "ON"),
    (0x23, 0x06): ("ON", "ON (0x06)"),
    (0x23, 0x26): ("ON", "ON (0x26)"),
    (0x23, 0x02): ("ON", "ON (0x02)"),
    (0x23, 0x36): ("ON", "ON (0x36)"),
}


class VolcanoBTManager:
    """
    Manages Bluetooth communication with the Volcano device.
    """

    def __init__(self, bt_address: str):
        self.bt_address = bt_address
        self._client = None
        self._connected = False
        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self.ble_firmware_version = None  # New Attribute
        self.serial_number = None         # New Attribute
        self._bt_status = BT_STATUS_DISCONNECTED
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
        """Start the Bluetooth manager."""
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
        self.bt_status = BT_STATUS_DISCONNECTED

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
            _LOGGER.info("Attempting to connect to Bluetooth device %s...", self.bt_address)
            self.bt_status = BT_STATUS_CONNECTING
            self._client = BleakClient(self.bt_address)
            await self._client.connect()

            self._connected = self._client.is_connected
            if self._connected:
                _LOGGER.info("Bluetooth successfully connected to %s", self.bt_address)
                self.bt_status = BT_STATUS_CONNECTED
                # Read BLE Firmware Version and Serial Number before starting other operations
                await self._read_ble_firmware_version()
                await self._read_serial_number()
                await self._subscribe_pump_notifications()
            else:
                self.bt_status = BT_STATUS_DISCONNECTED
        except BleakError as e:
            if "slot Bluetooth" in str(e):
                _LOGGER.error("Critical slot Bluetooth error: %s", e)
            else:
                _LOGGER.warning("Bluetooth connection warning: %s -> Retrying...", e)
            self.bt_status = BT_STATUS_ERROR
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _read_ble_firmware_version(self):
        """Read the BLE Firmware Version characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read BLE Firmware Version - not connected.")
            return
        try:
            _LOGGER.debug("Reading BLE Firmware Version from UUID: %s", UUID_BLE_FIRMWARE_VERSION)
            data = await self._client.read_gatt_char(UUID_BLE_FIRMWARE_VERSION)
            self.ble_firmware_version = data.decode('utf-8').strip()
            _LOGGER.info("BLE Firmware Version: %s", self.ble_firmware_version)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading BLE Firmware Version: %s", e)
            self.ble_firmware_version = None

    async def _read_serial_number(self):
        """Read the Serial Number characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Serial Number - not connected.")
            return
        try:
            _LOGGER.debug("Reading Serial Number from UUID: %s", UUID_SERIAL_NUMBER)
            data = await self._client.read_gatt_char(UUID_SERIAL_NUMBER)
            self.serial_number = data.decode('utf-8').strip()
            _LOGGER.info("Serial Number: %s", self.serial_number)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Serial Number: %s", e)
            self.serial_number = None

    async def _subscribe_pump_notifications(self):
        """Subscribe to pump notifications."""
        if not self._connected:
            return

        def notification_handler(sender, data):
            """Handle incoming pump notifications."""
            _LOGGER.debug("Received pump notification from %s: %s", sender, data)
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                if (b1, b2) in VALID_PATTERNS:
                    self.heat_state, self.pump_state = VALID_PATTERNS[(b1, b2)]
                else:
                    self.heat_state = f"0x{b1:02X}"
                    self.pump_state = f"0x{b2:02X}"
                _LOGGER.debug("Parsed Heat State: %s, Pump State: %s", self.heat_state, self.pump_state)
            self._notify_sensors()

        try:
            _LOGGER.debug("Subscribing to pump notifications on UUID: %s", UUID_PUMP_NOTIFICATIONS)
            await self._client.start_notify(UUID_PUMP_NOTIFICATIONS, notification_handler)
            _LOGGER.info("Subscribed to pump notifications.")
        except BleakError as e:
            _LOGGER.warning("Error subscribing to notifications: %s", e)

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
            _LOGGER.debug("Reading temperature from UUID: %s", UUID_TEMP)
            data = await self._client.read_gatt_char(UUID_TEMP)
            if len(data) >= 2:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
                _LOGGER.debug("Read temperature: %s °C", self.current_temperature)
            else:
                self.current_temperature = None
                _LOGGER.warning("Received incomplete temperature data: %s", data)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s -> disconnect & retry...", e)
            self.bt_status = BT_STATUS_ERROR
            await self._disconnect()

    def _notify_sensors(self):
        """Notify all registered sensors that new data is available."""
        _LOGGER.debug("Notifying %d sensors of new data.", len(self._sensors))
        for sensor_entity in self._sensors:
            sensor_entity.schedule_update_ha_state(True)

    async def _disconnect(self):
        """Disconnect from the BLE device."""
        if self._client:
            try:
                _LOGGER.debug("Disconnecting from Bluetooth device %s...", self.bt_address)
                await self._client.disconnect()
                _LOGGER.info("Disconnected from Bluetooth device %s.", self.bt_address)
            except BleakError as e:
                _LOGGER.warning("Bluetooth disconnection warning: %s", e)
        self._client = None
        self._connected = False
        self.bt_status = BT_STATUS_DISCONNECTED

    async def write_gatt_command(self, write_uuid: str, payload: bytes = b""):
        """Write a payload to a GATT characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot write to %s - not connected.", write_uuid)
            return
        try:
            _LOGGER.debug("Writing to UUID: %s with payload: %s", write_uuid, payload)
            await self._client.write_gatt_char(write_uuid, payload)
            _LOGGER.info("Successfully wrote to UUID: %s", write_uuid)
        except BleakError as e:
            _LOGGER.error("Error writing to %s: %s", write_uuid, e)

    async def set_heater_temperature(self, temp_c: float):
        """Write the temperature setpoint to the heater's GATT characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set heater temperature - not connected.")
            return
        safe_temp = max(40.0, min(temp_c, 230.0))
        payload = int(safe_temp * 10).to_bytes(2, byteorder="little")
        try:
            _LOGGER.debug("Setting heater temperature to %s °C with payload: %s", safe_temp, payload)
            await self._client.write_gatt_char(UUID_HEATER_SETPOINT, payload)
            _LOGGER.info("Heater temperature set to %s °C.", safe_temp)
        except BleakError as e:
            _LOGGER.error("Error writing heater temperature: %s", e)
