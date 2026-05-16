import asyncio
import threading
import logging
import os
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

log = logging.getLogger(__name__)

SERVICE_UUID     = "00001820-0000-1000-8000-00805f9b34fb"
CHAR_BTN1_MAP    = "00002a01-0000-1000-8000-00805f9b34fb"
CHAR_BTN2_MAP    = "00002a02-0000-1000-8000-00805f9b34fb"
CHAR_BTN3_MAP    = "00002a03-0000-1000-8000-00805f9b34fb"
CHAR_BTN_EVENT   = "00002a04-0000-1000-8000-00805f9b34fb"
CHAR_DEV_STATUS  = "00002a05-0000-1000-8000-00805f9b34fb"

class BleManager:
    """Manages BLE connection to Vocitap hardware (ESP32_BT_MIC)."""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._client = None
        self._address = None
        self._connected = False
        
        # Characteristic handles
        self._ch = [None, None, None]
        self._ch_event = None
        self._ch_status = None
        
        # Callbacks
        self.on_button_event = None # callback(button_id: int, state: int)
        self.on_status_change = None # callback(connected: bool, address: str)
        self.on_device_status = None # callback(hfp: int, audio: int)

    def start(self):
        """Start the asyncio event loop in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_coro(self, coro):
        if not self._loop:
            return None
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _scan_async(self, timeout=10.0):
        log.info("Scanning for ESP32 devices...")
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad: ad.local_name and "ESP32" in ad.local_name,
            timeout=timeout,
        )
        return device.address if device else None

    def scan(self, callback, timeout=10.0):
        """Asynchronously scan for devices and call callback with address."""
        async def task():
            addr = await self._scan_async(timeout)
            if callback:
                callback(addr)
        self._run_coro(task())

    async def _connect_async(self, address):
        try:
            self._client = BleakClient(address)
            await self._client.connect()
            log.info(f"Connected to {address}")
            await asyncio.sleep(1.0) # Wait for services

            svc = None
            for s in self._client.services:
                if s.uuid.lower() == SERVICE_UUID:
                    svc = s
                    break
            
            if not svc:
                log.error("Vocitap service not found on device")
                await self._client.disconnect()
                return False

            # Resolve characteristics
            char_uuids = [CHAR_BTN1_MAP, CHAR_BTN2_MAP, CHAR_BTN3_MAP]
            for i, uid in enumerate(char_uuids):
                for c in svc.characteristics:
                    if c.uuid.lower() == uid:
                        self._ch[i] = c
                        break

            for c in svc.characteristics:
                if c.uuid.lower() == CHAR_BTN_EVENT:
                    self._ch_event = c
                elif c.uuid.lower() == CHAR_DEV_STATUS:
                    self._ch_status = c

            if self._ch_event:
                await self._client.start_notify(self._ch_event, self._internal_button_handler)
            if self._ch_status:
                await self._client.start_notify(self._ch_status, self._internal_status_handler)

            self._connected = True
            self._address = address
            if self.on_status_change:
                self.on_status_change(True, address)
            return True
        except Exception as e:
            log.error(f"Connect failed: {e}")
            self._connected = False
            if self.on_status_change:
                self.on_status_change(False, None)
            return False

    def connect(self, address):
        self._run_coro(self._connect_async(address))

    async def _disconnect_async(self):
        if self._client:
            await self._client.disconnect()
        self._connected = False
        if self.on_status_change:
            self.on_status_change(False, None)

    def disconnect(self):
        self._run_coro(self._disconnect_async())

    def _internal_button_handler(self, _sender, data):
        if len(data) >= 2 and self.on_button_event:
            self.on_button_event(data[0], data[1])

    def _internal_status_handler(self, _sender, data):
        if len(data) >= 2 and self.on_device_status:
            self.on_device_status(data[0], data[1])

    async def _write_mapping_async(self, idx, vk, mod):
        if not self._connected or not self._ch[idx]:
            return False
        try:
            await self._client.write_gatt_char(self._ch[idx], bytes([vk, mod]), response=True)
            return True
        except Exception as e:
            log.error(f"Write mapping failed: {e}")
            return False

    def write_mapping(self, idx, vk, mod):
        self._run_coro(self._write_mapping_async(idx, vk, mod))

    async def _read_mapping_async(self, idx, callback):
        if not self._connected or not self._ch[idx]:
            if callback: callback(None)
            return
        try:
            data = await self._client.read_gatt_char(self._ch[idx])
            if callback:
                if len(data) >= 2:
                    callback((data[0], data[1]))
                else:
                    callback(None)
        except Exception as e:
            log.error(f"Read mapping failed: {e}")
            if callback: callback(None)

    def read_mapping(self, idx, callback):
        self._run_coro(self._read_mapping_async(idx, callback))

    @property
    def is_connected(self):
        return self._connected
