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
    UUID_FIRMWARE_VERSION,
    UUID_AUTO_SHUT_OFF,
    UUID_AUTO_SHUT_OFF_SETTING,
    UUID_LED_BRIGHTNESS,
    UUID_HOURS_OF_OPERATION,
    UUID_MINUTES_OF_OPERATION,
    UUID_VIBRATION,
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

        # Existing attributes
        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self.ble_firmware_version = None
        self.serial_number = None
        self.firmware_version = None
        self.auto_shut_off = None             # "ON" or "OFF" (or "Enabled"/"Disabled")
        self.auto_shut_off_setting = None     # Minutes (or possibly None)
        self.led_brightness = None
        self.hours_of_operation = None
        self.minutes_of_operation = None
        self.vibration = None  # "ON" or "OFF" once read

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
        """Register a sensor or entity to receive updates."""
        if sensor_entity not in self._sensors:
            self._sensors.append(sensor_entity)

    def unregister_sensor(self, sensor_entity):
        """Unregister a sensor or entity from receiving updates."""
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
        from bleak import BleakClient, BleakError
        import asyncio

        try:
            _LOGGER.info("Attempting to connect to Bluetooth device %s...", self.bt_address)
            self.bt_status = BT_STATUS_CONNECTING
            self._client = BleakClient(self.bt_address)

            # Connect with a longer timeout if needed
            await self._client.connect(timeout=30.0)

            self._connected = self._client.is_connected
            if self._connected:
                _LOGGER.info("Bluetooth successfully connected to %s", self.bt_address)
                self.bt_status = BT_STATUS_CONNECTED

                # Read all required characteristics before starting other operations
                await self._read_ble_firmware_version()
                await self._read_serial_number()
                await self._read_firmware_version()
                await self._read_auto_shut_off()
                await self._read_auto_shut_off_setting()
                await self._read_led_brightness()
                await self._read_hours_of_operation()
                await self._read_minutes_of_operation()
                await self._read_vibration()
                await self._subscribe_pump_notifications()

            else:
                self.bt_status = BT_STATUS_DISCONNECTED

        except asyncio.TimeoutError:
            _LOGGER.error("Bluetooth connection timed out to %s", self.bt_address)
            self.bt_status = BT_STATUS_ERROR
            await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            if isinstance(e.__cause__, asyncio.TimeoutError):
                _LOGGER.error("Bluetooth connection timed out (Bleak) to %s: %s", self.bt_address, e)
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
            data = await self._client.read_gatt_char(UUID_BLE_FIRMWARE_VERSION)
            self.ble_firmware_version = data.decode("utf-8").strip()
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
            data = await self._client.read_gatt_char(UUID_SERIAL_NUMBER)
            self.serial_number = data.decode("utf-8").strip()
            _LOGGER.info("Serial Number: %s", self.serial_number)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Serial Number: %s", e)
            self.serial_number = None

    async def _read_firmware_version(self):
        """Read the Volcano Firmware Version characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Firmware Version - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_FIRMWARE_VERSION)
            self.firmware_version = data.decode("utf-8").strip()
            _LOGGER.info("Firmware Version: %s", self.firmware_version)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Firmware Version: %s", e)
            self.firmware_version = None

    async def _read_auto_shut_off(self):
        """Read the Auto Shutoff characteristic (0x00=OFF, 0x01=ON)."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Auto Shutoff - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_AUTO_SHUT_OFF)
            if data:
                self.auto_shut_off = "ON" if data[0] == 1 else "OFF"
            else:
                self.auto_shut_off = None
            _LOGGER.info("Auto Shutoff: %s", self.auto_shut_off)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Auto Shutoff: %s", e)
            self.auto_shut_off = None

    async def _read_auto_shut_off_setting(self):
        """Read the Auto Shutoff Setting characteristic (2-byte: seconds)."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Auto Shutoff Setting - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_AUTO_SHUT_OFF_SETTING)
            if len(data) >= 2:
                total_seconds = int.from_bytes(data[:2], byteorder="little")
                self.auto_shut_off_setting = total_seconds // 60
                _LOGGER.info("Auto Shutoff Setting: %d minutes", self.auto_shut_off_setting)
            else:
                self.auto_shut_off_setting = None
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Auto Shutoff Setting: %s", e)
            self.auto_shut_off_setting = None

    async def _read_led_brightness(self):
        """Read the LED Brightness characteristic (0–100)."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read LED Brightness - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_LED_BRIGHTNESS)
            if data:
                self.led_brightness = data[0]
            else:
                self.led_brightness = None
            _LOGGER.info("LED Brightness: %s%%", self.led_brightness)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading LED Brightness: %s", e)
            self.led_brightness = None

    async def _read_hours_of_operation(self):
        """Read the Hours of Operation characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Hours of Operation - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_HOURS_OF_OPERATION)
            if len(data) >= 2:
                self.hours_of_operation = int.from_bytes(data[:2], byteorder="little")
            else:
                self.hours_of_operation = None
            _LOGGER.info("Hours of Operation: %s hours", self.hours_of_operation)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Hours of Operation: %s", e)
            self.hours_of_operation = None

    async def _read_minutes_of_operation(self):
        """Read the Minutes of Operation characteristic."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read Minutes of Operation - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_MINUTES_OF_OPERATION)
            if len(data) >= 2:
                self.minutes_of_operation = int.from_bytes(data[:2], byteorder="little")
            else:
                self.minutes_of_operation = None
            _LOGGER.info("Minutes of Operation: %s minutes", self.minutes_of_operation)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading Minutes of Operation: %s", e)
            self.minutes_of_operation = None

    
    async def _read_vibration(self):
        """Read the vibration characteristic (0x00=OFF, 0x01=ON)."""
        if not self._connected or not self._client:
            _LOGGER.error("Cannot read vibration - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_VIBRATION)
            if data:
                self.vibration = "ON" if data[0] == 1 else "OFF"
            else:
                self.vibration = None
            _LOGGER.info("Vibration: %s", self.vibration)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading vibration: %s", e)
            self.vibration = None


    async def _subscribe_pump_notifications(self):
        """Subscribe to pump notifications."""
        if not self._connected:
            return

        def notification_handler(sender, data):
            _LOGGER.debug("Received pump notification from %s: %s", sender, data)
            if len(data) >= 2:
                b1, b2 = data[0], data[1]
                if (b1, b2) in VALID_PATTERNS:
                    self.heat_state, self.pump_state = VALID_PATTERNS[(b1, b2)]
                else:
                    self.heat_state = f"0x{b1:02X}"
                    self.pump_state = f"0x{b2:02X}"
            self._notify_sensors()

        try:
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
        """Read the temperature characteristic (2-byte: .1°C)."""
        if not self._connected or not self._client:
            return
        try:
            data = await self._client.read_gatt_char(UUID_TEMP)
            if len(data) >= 2:
                raw_16 = int.from_bytes(data[:2], byteorder="little", signed=False)
                self.current_temperature = raw_16 / 10.0
            else:
                self.current_temperature = None
                _LOGGER.warning("Received incomplete temperature data: %s", data)
            self._notify_sensors()
        except BleakError as e:
            _LOGGER.error("Error reading temperature: %s -> disconnect & retry...", e)
            self.bt_status = BT_STATUS_ERROR
            await self._disconnect()

    def _notify_sensors(self):
        """Notify all registered sensors/entities that new data is available."""
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
            await self._client.write_gatt_char(UUID_HEATER_SETPOINT, payload)
            _LOGGER.info("Heater temperature set to %s °C.", safe_temp)
        except BleakError as e:
            _LOGGER.error("Error writing heater temperature: %s", e)

    async def set_led_brightness(self, brightness: int):
        """Write the LED Brightness characteristic (0–100)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set LED Brightness - not connected.")
            return
        clamped_brightness = max(0, min(brightness, 100))
        payload = clamped_brightness.to_bytes(1, byteorder="little")
        try:
            await self._client.write_gatt_char(UUID_LED_BRIGHTNESS, payload)
            self.led_brightness = clamped_brightness
            self._notify_sensors()
            _LOGGER.info("LED Brightness set to %d", clamped_brightness)
        except BleakError as e:
            _LOGGER.error("Error writing LED brightness: %s", e)

    #
    # NEW: set_auto_shutoff(enabled) -> writes 0x00 or 0x01 to the same UUID
    #
    async def set_auto_shutoff(self, enabled: bool):
        """Enable/Disable Auto Shutoff by writing 0x01 (on) or 0x00 (off)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set Auto Shutoff - not connected.")
            return
        payload = b"\x01" if enabled else b"\x00"
        try:
            await self._client.write_gatt_char(UUID_AUTO_SHUT_OFF, payload)
            self.auto_shut_off = "ON" if enabled else "OFF"
            self._notify_sensors()
            _LOGGER.info("Auto Shutoff set to %s", self.auto_shut_off)
        except BleakError as e:
            _LOGGER.error("Error writing auto shutoff: %s", e)

    #
    # NEW: set_auto_shutoff_setting(minutes) -> writes 2-byte little-endian of (minutes*60)
    #
    async def set_auto_shutoff_setting(self, minutes: int):
        """Write the Auto Shutoff Setting in minutes (converted to seconds)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set Auto Shutoff Setting - not connected.")
            return

        # You can clamp the range if desired, e.g. 5..240 minutes
        # minutes = max(5, min(minutes, 240))

        total_seconds = minutes * 60
        payload = total_seconds.to_bytes(2, byteorder="little")

        try:
            await self._client.write_gatt_char(UUID_AUTO_SHUT_OFF_SETTING, payload)
            self.auto_shut_off_setting = minutes
            self._notify_sensors()
            _LOGGER.info("Auto Shutoff Setting set to %d minutes", minutes)
        except BleakError as e:
            _LOGGER.error("Error writing auto shutoff setting: %s", e)

    #
    # NEW: set_vibration(enabled)
    #
    async def set_vibration(self, enabled: bool):
        """Set vibration by writing a 4-byte bitmask."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set vibration - not connected.")
            return
    
        # Use 0x0400 for ON, 0x10400 for OFF
        value = 0x400 if enabled else 0x10400
    
        # Convert to 4 bytes, little-endian
        payload = value.to_bytes(4, byteorder="little")
    
        try:
            _LOGGER.debug(
                "Writing vibration: %s -> payload: %s",
                hex(value),
                payload.hex()
            )
            await self._client.write_gatt_char(UUID_VIBRATION, payload)
    
            # If it succeeds, store the new state
            self.vibration = "ON" if enabled else "OFF"
            self._notify_sensors()
            _LOGGER.info("Vibration set to %s", self.vibration)
        except BleakError as e:
            _LOGGER.error("Error writing vibration: %s", e)
    
