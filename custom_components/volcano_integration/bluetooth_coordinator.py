"""bluetooth_coordinator.py - Volcano Integration for Home Assistant."""
import asyncio
import logging
from bleak import BleakClient, BleakError
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    BluetoothScanningMode,
    async_scanner_by_address,
    async_ble_device_from_address
)
from homeassistant.components.bluetooth.match import ADDRESS
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    BT_STATUS_DISCONNECTED,
    BT_STATUS_CONNECTING,
    BT_STATUS_CONNECTED,
    BT_STATUS_ERROR,
    VIBRATION_BIT_MASK,
    REGISTER1_UUID,          # Pump Notifications
    REGISTER2_UUID,          # [Specify Purpose]
    REGISTER3_UUID,          # Vibration Control
    UUID_TEMP,               # Current Temperature
    UUID_PUMP_NOTIFICATIONS, # Pump Notifications
    UUID_PUMP_ON,            # Pump On
    UUID_PUMP_OFF,           # Pump Off
    UUID_HEAT_ON,            # Heat On
    UUID_HEAT_OFF,           # Heat Off
    UUID_HEATER_SETPOINT,    # Heater Setpoint
    UUID_BLE_FIRMWARE_VERSION,    # BLE Firmware Version
    UUID_SERIAL_NUMBER,             # Serial Number
    UUID_FIRMWARE_VERSION,          # Volcano Firmware Version
    UUID_AUTO_SHUT_OFF,             # Auto Shutoff
    UUID_AUTO_SHUT_OFF_SETTING,     # Auto Shutoff Setting
    UUID_LED_BRIGHTNESS,            # LED Brightness
    UUID_HOURS_OF_OPERATION,        # Hours of Operation
    UUID_MINUTES_OF_OPERATION,      # Minutes of Operation
    UUID_VIBRATION,                 # Vibration Control
)

_LOGGER = logging.getLogger(__name__)

RECONNECT_INTERVAL = 3
TEMP_POLL_INTERVAL = 1

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

    def __init__(self, hass: HomeAssistant, bt_address: str):
        """Initialize the manager."""
        self.hass = hass
        self.bt_address = bt_address
        self._client = None
        self._connected = False
        self._scanner = None

        # Device Attributes
        self.current_temperature = None
        self.heat_state = None
        self.pump_state = None
        self.ble_firmware_version = None
        self.serial_number = None
        self.firmware_version = None
        self.auto_shut_off = None
        self.auto_shut_off_setting = None
        self.led_brightness = None
        self.hours_of_operation = None
        self.minutes_of_operation = None
        self.vibration = None

        self._bt_status = BT_STATUS_DISCONNECTED
        self._run_task = None
        self._temp_poll_task = None
        self._stop_event = asyncio.Event()
        self._sensors = []

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
        """Start the Bluetooth manager (reconnect loop, etc.)."""
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

            # Get scanner for this device's address
            self._scanner = async_scanner_by_address(self.hass, self.bt_address)
            if not self._scanner:
                _LOGGER.error("No Bluetooth scanner available for address %s", self.bt_address)
                self.bt_status = BT_STATUS_ERROR
                return

            # Get BLE device using Home Assistant's bluetooth utilities
            ble_device = await async_ble_device_from_address(
                self.hass, 
                self.bt_address,
                connectable=True
            )
            if not ble_device:
                _LOGGER.error("Could not find BLE device at address %s", self.bt_address)
                self.bt_status = BT_STATUS_ERROR
                return

            # Create BleakClient using the discovered BLE device
            self._client = BleakClient(ble_device)
            await self._client.connect(timeout=30.0)

            self._connected = self._client.is_connected
            if self._connected:
                _LOGGER.info("Bluetooth successfully connected to %s", self.bt_address)
                self.bt_status = BT_STATUS_CONNECTED

                # Read all required characteristics
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

        except asyncio.TimeoutError as e:
            _LOGGER.warning("Bluetooth connection timed out to %s: %s", self.bt_address, e)
            self.bt_status = BT_STATUS_ERROR
            await asyncio.sleep(RECONNECT_INTERVAL)

        except BleakError as e:
            _LOGGER.warning("Bluetooth connection error: %s -> Retrying...", e)
            self.bt_status = BT_STATUS_ERROR
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _read_ble_firmware_version(self):
        """Read the BLE Firmware Version characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read BLE Firmware Version - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_BLE_FIRMWARE_VERSION)
            self.ble_firmware_version = data.decode("utf-8").strip()
            _LOGGER.info("BLE Firmware Version: %s", self.ble_firmware_version)
            self._notify_sensors()
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading BLE Firmware Version: %s", e)
            else:
                _LOGGER.warning("Error reading BLE Firmware Version: %s", e)
            self.ble_firmware_version = None

    async def _read_serial_number(self):
        """Read the Serial Number characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Serial Number - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_SERIAL_NUMBER)
            self.serial_number = data.decode("utf-8").strip()
            _LOGGER.info("Serial Number: %s", self.serial_number)
            self._notify_sensors()
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Serial Number: %s", e)
            else:
                _LOGGER.warning("Error reading Serial Number: %s", e)
            self.serial_number = None

    async def _read_firmware_version(self):
        """Read the Volcano Firmware Version characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Firmware Version - not connected.")
            return
        try:
            data = await self._client.read_gatt_char(UUID_FIRMWARE_VERSION)
            self.firmware_version = data.decode("utf-8").strip()
            _LOGGER.info("Firmware Version: %s", self.firmware_version)
            self._notify_sensors()
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Firmware Version: %s", e)
            else:
                _LOGGER.warning("Error reading Firmware Version: %s", e)
            self.firmware_version = None

    async def _read_auto_shut_off(self):
        """Read the Auto Shutoff characteristic (0x00=OFF, 0x01=ON)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Auto Shutoff - not connected.")
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Auto Shutoff: %s", e)
            else:
                _LOGGER.warning("Error reading Auto Shutoff: %s", e)
            self.auto_shut_off = None

    async def _read_auto_shut_off_setting(self):
        """Read the Auto Shutoff Setting characteristic (2-byte: seconds)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Auto Shutoff Setting - not connected.")
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Auto Shutoff Setting: %s", e)
            else:
                _LOGGER.warning("Error reading Auto Shutoff Setting: %s", e)
            self.auto_shut_off_setting = None

    async def _read_led_brightness(self):
        """Read the LED Brightness characteristic (0–100)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read LED Brightness - not connected.")
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading LED Brightness: %s", e)
            else:
                _LOGGER.warning("Error reading LED Brightness: %s", e)
            self.led_brightness = None

    async def _read_hours_of_operation(self):
        """Read the Hours of Operation characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Hours of Operation - not connected.")
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Hours of Operation: %s", e)
            else:
                _LOGGER.warning("Error reading Hours of Operation: %s", e)
            self.hours_of_operation = None

    async def _read_minutes_of_operation(self):
        """Read the Minutes of Operation characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read Minutes of Operation - not connected.")
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading Minutes of Operation: %s", e)
            else:
                _LOGGER.warning("Error reading Minutes of Operation: %s", e)
            self.minutes_of_operation = None

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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while subscribing to pump notifications: %s", e)
            else:
                _LOGGER.warning("Error subscribing to pump notifications: %s", e)

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
                _LOGGER.debug("Temperature read: %.1f°C", self.current_temperature)
            else:
                self.current_temperature = None
                _LOGGER.warning("Received incomplete temperature data: %s", data)
            self._notify_sensors()
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading temperature: %s", e)
            else:
                _LOGGER.warning("Error reading temperature: %s -> disconnect & retry...", e)
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
                if "No adapter found" in str(e) or "adapter" in str(e).lower():
                    _LOGGER.error("Missing bluetooth adapter during disconnection: %s", e)
                else:
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while writing to %s: %s", write_uuid, e)
            else:
                _LOGGER.warning("Error writing to %s: %s", write_uuid, e)

    async def set_heater_temperature(self, temp_c: float):
        """Write the temperature setpoint to the heater's GATT characteristic."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set heater temperature - not connected.")
            return
        safe_temp = max(40.0, min(temp_c, 230.0))
        payload = int(safe_temp * 10).to_bytes(2, byteorder="little")
        try:
            await self._client.write_gatt_char(UUID_HEATER_SETPOINT, payload)
            _LOGGER.info("Heater temperature set to %.1f °C.", safe_temp)
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while writing heater temperature: %s", e)
            else:
                _LOGGER.warning("Error writing heater temperature: %s", e)

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
            _LOGGER.info("LED Brightness set to %d%%", clamped_brightness)
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while writing LED brightness: %s", e)
            else:
                _LOGGER.warning("Error writing LED brightness: %s", e)

    async def set_auto_shutoff(self, enabled: bool):
        """Enable/Disable Auto Shutoff by writing 0x01 (ON) or 0x00 (OFF)."""
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
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while writing Auto Shutoff: %s", e)
            else:
                _LOGGER.warning("Error writing Auto Shutoff: %s", e)

    async def set_auto_shutoff_setting(self, minutes: int):
        """Write the Auto Shutoff Setting in minutes (converted to seconds)."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set Auto Shutoff Setting - not connected.")
            return

        total_seconds = minutes * 60
        payload = total_seconds.to_bytes(2, byteorder="little")

        try:
            await self._client.write_gatt_char(UUID_AUTO_SHUT_OFF_SETTING, payload)
            self.auto_shut_off_setting = minutes
            self._notify_sensors()
            _LOGGER.info("Auto Shutoff Setting set to %d minutes", minutes)
        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while writing Auto Shutoff Setting: %s", e)
            else:
                _LOGGER.warning("Error writing Auto Shutoff Setting: %s", e)

    async def set_vibration(self, enabled: bool):
        """Set vibration by modifying only the vibration bit in the control register."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot set vibration - not connected.")
            return

        try:
            control_data = await self._client.read_gatt_char(REGISTER3_UUID)
            _LOGGER.debug("Current control register (REGISTER3_UUID): %s (len=%d)", control_data.hex(), len(control_data))

            if len(control_data) < 4:
                _LOGGER.warning("Received incomplete control register data: %s", control_data.hex())
                return

            control_value = int.from_bytes(control_data[:4], byteorder="little")
            _LOGGER.debug("Control register as integer: 0x{0:08x}".format(control_value))

            if enabled:
                new_control_value = control_value | VIBRATION_BIT_MASK
            else:
                new_control_value = control_value & (~VIBRATION_BIT_MASK)

            new_control_data = new_control_value.to_bytes(4, byteorder="little")
            _LOGGER.debug("Writing new control register: %s", new_control_data.hex())

            await self._client.write_gatt_char(REGISTER3_UUID, new_control_data)
            _LOGGER.info("Vibration write operation completed.")

            await self._read_vibration()

            self.vibration = "ON" if enabled else "OFF"
            self._notify_sensors()
            _LOGGER.info("Vibration set to %s", self.vibration)

        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while setting vibration: %s", e)
            else:
                _LOGGER.warning("Error setting vibration: %s", e)

    async def _read_vibration(self):
        """Read the vibration state from the control register."""
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot read vibration - not connected.")
            return
        try:
            control_data = await self._client.read_gatt_char(REGISTER3_UUID)
            _LOGGER.debug("Vibration read raw data: %s (len=%d)", control_data.hex(), len(control_data))

            if len(control_data) < 4:
                _LOGGER.warning("Received incomplete control register data for vibration: %s", control_data.hex())
                self.vibration = None
            else:
                control_value = int.from_bytes(control_data[:4], byteorder="little")
                _LOGGER.debug("Control register as integer: 0x{0:08x}".format(control_value))
                if control_value & VIBRATION_BIT_MASK:
                    self.vibration = "ON"
                else:
                    self.vibration = "OFF"

            _LOGGER.info("Vibration (read): %s", self.vibration)
            self._notify_sensors()

        except BleakError as e:
            if "No adapter found" in str(e) or "adapter" in str(e).lower():
                _LOGGER.error("Missing bluetooth adapter while reading vibration: %s", e)
            else:
                _LOGGER.warning("Error reading vibration: %s", e)
            self.vibration = None
