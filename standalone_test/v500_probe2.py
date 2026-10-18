#!/usr/bin/env python3
"""V500 probe, round 2: listen on every notify characteristic, try the known
read-only commands, then log runtime frames so we can map bytes to values.

Usage:
  python3 v500_probe2.py <ADDRESS> [monitor_seconds]   (default 90)

While the monitor runs, change ONE thing at a time and note the elapsed
second shown, e.g. plug a known load into AC out, unplug it, connect the
charger, use the USB ports, toggle AC output from the panel.
Everything is also saved to v500_log.txt.
"""
import asyncio, sys, time
from bleak import BleakClient

NOTIFY = ["0000ff01-0000-1000-8000-00805f9b34fb",
          "0000ff02-0000-1000-8000-00805f9b34fb",
          "0000ff06-0000-1000-8000-00805f9b34fb"]
TX = "0000ff01-0000-1000-8000-00805f9b34fb"
# Read-only queries used by the Venus E integration (no write/reboot commands)
READ_CMDS = [0x03, 0x04, 0x08, 0x0D, 0x13, 0x14, 0x1A, 0x1C, 0x22, 0x24, 0x28]

log = open("v500_log.txt", "a")
t0 = time.time()
last = {}


def out(s):
    print(s); log.write(s + "\n"); log.flush()


def frame(cmd, payload=b""):
    f = bytearray([0x73, 0, 0x23, cmd]) + payload
    f[1] = len(f) + 1
    c = 0
    for b in f:
        c ^= b
    return bytes(f + bytes([c]))


def handler(uuid):
    short = uuid[4:8]
    def cb(_, data):
        data = bytes(data)
        t = time.time() - t0
        prev = last.get((short, data[3] if len(data) > 3 else None))
        diff = ""
        if prev and len(prev) == len(data):
            ch = [i for i in range(len(data)) if data[i] != prev[i]]
            diff = "  changed@" + ",".join(f"{i}:{prev[i]:02x}->{data[i]:02x}" for i in ch) if ch else "  (same)"
        last[(short, data[3] if len(data) > 3 else None)] = data
        out(f"[{t:6.1f}s] {short} len={len(data)} {data.hex(' ')}{diff}")
        printable = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
        if sum(32 <= b < 127 for b in data) > len(data) * 0.6:
            out(f"           ascii: {printable}")
    return cb


async def main(addr, secs):
    async with BleakClient(addr, timeout=20) as c:
        out(f"=== connected {addr} mtu={getattr(c, 'mtu_size', '?')}")
        for u in NOTIFY:
            try:
                await c.start_notify(u, handler(u))
                out(f"subscribed {u[4:8]}")
            except Exception as e:
                out(f"subscribe {u[4:8]} failed: {e}")
        out("\n=== passive listen 5 s (does it push on its own?)")
        await asyncio.sleep(5)
        out("\n=== command sweep")
        for cmd in READ_CMDS:
            out(f"-> 0x{cmd:02X}")
            await c.write_gatt_char(TX, frame(cmd), response=False)
            await asyncio.sleep(2.5)
        out(f"\n=== monitor: polling 0x03 every 2 s for {secs} s - change loads now")
        end = time.time() + secs
        while time.time() < end:
            await c.write_gatt_char(TX, frame(0x03), response=False)
            await asyncio.sleep(2)
    out("=== done")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 90))
