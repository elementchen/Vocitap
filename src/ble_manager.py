import asyncio
import threading
import logging
import os
import time
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

log = logging.getLogger(__name__)

SERVICE_UUID     = "00001820-0000-1000-8000-00805f9b34fb"
CHAR_BTN1_MAP    = "00002a01-0000-1000-8000-00805f9b34fb"
CHAR_BTN2_MAP    = "00002a02-0000-1000-8000-00805f9b34fb"
CHAR_BTN3_MAP    = "00002a03-0000-1000-8000-00805f9b34fb"
CHAR_BTN_EVENT   = "00002a04-0000-1000-8000-00805f9b34fb"
CHAR_DEV_STATUS  = "00002a05-0000-1000-8000-00805f9b34fb"
CHAR_TX_POWER    = "00002a06-0000-1000-8000-00805f9b34fb"
CHAR_SLEEP_MODE  = "00002a07-0000-1000-8000-00805f9b34fb"
CHAR_BTN4_MAP    = "00002a08-0000-1000-8000-00805f9b34fb"

class BleManager:
    """Manages BLE connection to Vocitap hardware (ESP32_BT_MIC)."""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._client = None
        self._address = None
        self._connected = False
        
        # Characteristic handles
        self._ch = [None, None, None, None]
        self._ch_event = None
        self._ch_status = None
        self._ch_tx_power = None
        self._ch_sleep_mode = None
        
        # Callbacks
        self.on_button_event = None
        self.on_status_change = None
        self.on_device_status = None

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop: self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_coro(self, coro):
        if not self._loop: return None
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _scan_async(self, timeout=3.0):
        log.info("Scanning system for Vocitap/ESP32 HID device (Quick Scan)...")
        # 极速扫描：仅用 3 秒确认系统缓存中的设备
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad: ad.local_name and "ESP32" in ad.local_name,
            timeout=timeout,
        )
        if device:
            log.info(f"Scan Success: Found {device.name} [{device.address}]")
            return device.address
        return None

    def scan(self, callback, timeout=10.0):
        async def task():
            addr = await self._scan_async(timeout)
            if callback: callback(addr)
        self._run_coro(task())

    async def _connect_async(self, address):
        try:
            self._address = address
            log.info(f"Connecting to {address}...")
            self._client = BleakClient(address, disconnected_callback=self._on_disconnected_callback)
            
            await self._client.connect()
            log.info("BLE Connected, resolving services...")
            await asyncio.sleep(2.0) # 增加延迟以确保 Windows 完成服务表加载

            svc = None
            if self._client.services:
                log.info("Discovered services:")
                for s in self._client.services:
                    log.info(f"  - Service: {s.uuid}")
                    # 增强匹配：支持完整 UUID 和 16位简写
                    if s.uuid.lower() == SERVICE_UUID.lower() or "1820" in s.uuid.lower():
                        svc = s
                        break
            
            if not svc:
                log.error(f"Target Service {SERVICE_UUID} not found in discovered list.")
                await self._client.disconnect(); return False

            char_uuids = [CHAR_BTN1_MAP, CHAR_BTN2_MAP, CHAR_BTN3_MAP, CHAR_BTN4_MAP]
            if svc.characteristics:
                for i, uid in enumerate(char_uuids):
                    for c in svc.characteristics:
                        if c.uuid.lower() == uid: self._ch[i] = c; break

                for c in svc.characteristics:
                    if c.uuid.lower() == CHAR_BTN_EVENT: self._ch_event = c
                    elif c.uuid.lower() == CHAR_DEV_STATUS: self._ch_status = c
                    elif c.uuid.lower() == CHAR_TX_POWER: self._ch_tx_power = c
                    elif c.uuid.lower() == CHAR_SLEEP_MODE: self._ch_sleep_mode = c

            if self._ch_event: await self._client.start_notify(self._ch_event, self._internal_button_handler)
            if self._ch_status: await self._client.start_notify(self._ch_status, self._internal_status_handler)

            self._connected = True
            if self.on_status_change: self.on_status_change(True, address)
            return True
        except Exception as e:
            log.error(f"Connect failed for {address}: {e}")
            self._connected = False
            # 关键：连接失败时向逻辑层回传 False 和原地址，以便触发清空逻辑
            if self.on_status_change: self.on_status_change(False, address)
            return False

    def _on_disconnected_callback(self, client):
        self._connected = False
        if self.on_status_change: self.on_status_change(False, None)

    def connect(self, address):
        if self._connected: return
        self._run_coro(self._connect_async(address))

    async def _disconnect_async(self):
        self._connected = False
        if self._client:
            try:
                self._client.set_disconnected_callback(None)
                await self._client.disconnect()
            except: pass
        self._address = None
        if self.on_status_change: self.on_status_change(False, None)

    def disconnect(self):
        self._run_coro(self._disconnect_async())

    def _internal_button_handler(self, _sender, data):
        if not self._connected and self._client: self._connected = True
        if len(data) >= 2 and self.on_button_event: self.on_button_event(data[0], data[1])

    def _internal_status_handler(self, _sender, data):
        if not self._connected and self._client: self._connected = True
        if len(data) >= 2 and self.on_device_status: self.on_device_status(data[0], data[1])

    async def _write_mapping_async(self, idx, vk, mod):
        if not self.is_connected or not self._ch[idx]: return False
        try:
            await self._client.write_gatt_char(self._ch[idx], bytes([vk, mod]), response=True)
            return True
        except: return False

    def write_mapping(self, idx, vk, mod):
        self._run_coro(self._write_mapping_async(idx, vk, mod))

    async def _read_mapping_async(self, idx, callback):
        if not self.is_connected or not self._ch[idx]:
            if callback: callback(None)
            return
        try:
            data = await self._client.read_gatt_char(self._ch[idx])
            if callback and len(data) >= 2: callback((data[0], data[1]))
        except:
            if callback: callback(None)

    def read_mapping(self, idx, callback):
        self._run_coro(self._read_mapping_async(idx, callback))

    async def _read_tx_power_async(self, callback):
        if not self.is_connected or not self._ch_tx_power: return
        try:
            data = await self._client.read_gatt_char(self._ch_tx_power)
            if callback and len(data) >= 1: callback(data[0])
        except: pass

    def read_tx_power(self, callback):
        self._run_coro(self._read_tx_power_async(callback))

    async def _write_tx_power_async(self, level):
        if not self.is_connected or not self._ch_tx_power: return False
        try:
            await self._client.write_gatt_char(self._ch_tx_power, bytes([level]), response=True)
            return True
        except: return False

    def write_tx_power(self, level):
        self._run_coro(self._write_tx_power_async(level))

    async def _read_sleep_mode_async(self, callback):
        if not self.is_connected or not self._ch_sleep_mode: return
        try:
            data = await self._client.read_gatt_char(self._ch_sleep_mode)
            if callback and len(data) >= 1: callback(data[0])
        except: pass

    def read_sleep_mode(self, callback):
        self._run_coro(self._read_sleep_mode_async(callback))

    async def _write_sleep_mode_async(self, enabled):
        if not self.is_connected or not self._ch_sleep_mode: return False
        try:
            await self._client.write_gatt_char(self._ch_sleep_mode, bytes([enabled]), response=True)
            return True
        except: return False

    def write_sleep_mode(self, enabled):
        self._run_coro(self._write_sleep_mode_async(enabled))

    @property
    def is_connected(self):
        return self._connected
