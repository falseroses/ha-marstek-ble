#!/usr/bin/env python3
"""Probe a Marstek device (e.g. V500) over BLE from your computer.

Usage:
  pip3 install bleak
  python3 v500_probe.py            # scan 15 s, list nearby named devices
  python3 v500_probe.py <ADDRESS>  # connect, dump GATT, try Venus-E protocol

Paste the full output back to Claude.
"""
import asyncio, sys
from bleak import BleakScanner, BleakClient

SERVICE = "0000ff00-0000-1000-8000-00805f9b34fb"
TX = "0000ff01-0000-1000-8000-00805f9b34fb"
RX = "0000ff02-0000-1000-8000-00805f9b34fb"


def frame(cmd, payload=b""):
    f = bytearray([0x73, 0, 0x23, cmd]) + payload
    f[1] = len(f) + 1
    c = 0
    for b in f:
        c ^= b
    return bytes(f + bytes([c]))


async def scan():
    print("Scanning 15 s ... keep the V500 on and close the Marstek app on your phone.\n")
    found = await BleakScanner.discover(timeout=15, return_adv=True)
    rows = sorted(found.values(), key=lambda x: -(x[1].rssi or -999))
    for dev, adv in rows:
        name = adv.local_name or dev.name
        if not name:
            continue
        flag = "  <-- Marstek?" if name.upper().startswith(("MST", "MARSTEK", "V500")) else ""
        print(f"{dev.address}  rssi={adv.rssi:>4}  name={name!r}{flag}")
        if flag:
            print(f"      services={adv.service_uuids} mfr={ {k: v.hex() for k, v in adv.manufacturer_data.items()} }")
    print("\nNow run: python3 v500_probe.py <ADDRESS of the V500>")


async def probe(addr):
    got = []
    def on_notify(_, data):
        got.append(bytes(data))
        print(f"  <- {data.hex(' ')}")
        try:
            print(f"     ascii: {bytes(data[4:-1]).decode('ascii', 'replace')}")
        except Exception:
            pass

    async with BleakClient(addr, timeout=20) as c:
        print(f"Connected to {addr}\n--- GATT ---")
        for s in c.services:
            print(f"service {s.uuid}")
            for ch in s.characteristics:
                print(f"   char {ch.uuid}  {ch.properties}")
        if not any(s.uuid.lower() == SERVICE for s in c.services):
            print("\nNo 0xFF00 service -> different protocol from Venus E.")
            return
        await c.start_notify(RX, on_notify)
        for cmd, label in [(0x04, "device info"), (0x03, "runtime info"),
                           (0x14, "BMS data"), (0x0D, "system data"), (0x1A, "config")]:
            print(f"\n-> 0x{cmd:02X} {label}: {frame(cmd).hex(' ')}")
            await c.write_gatt_char(TX, frame(cmd), response=False)
            await asyncio.sleep(2.5)
        await c.stop_notify(RX)
    print(f"\nDone. {len(got)} notifications received.")


if __name__ == "__main__":
    asyncio.run(probe(sys.argv[1]) if len(sys.argv) > 1 else scan())
