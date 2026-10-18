#!/usr/bin/env python3
"""V500 monitor / experiment tool (round 3).

  python3 v500_monitor.py <ADDRESS> [seconds]          # passive monitor (default 240 s)
  python3 v500_monitor.py <ADDRESS> --try-output       # opt-in: test command 0x0E
  python3 v500_monitor.py <ADDRESS> --ac=on|--ac=off   # switch AC output (cmd 0x02, type 0x24)

Monitor mode only sends the read command 0x03 every 2 s. Each frame shows the
decoded known values plus any change in still-unknown bytes. Log: v500_log3.txt

--try-output sends the Venus E / B2500 "output control" command 0x0E with
payload 00 and then 01, 8 s apart, and shows what changes. Unplug anything
important from the V500 first. Nothing else is written.
"""
import asyncio, struct, sys, time
from bleak import BleakClient

TX = "0000ff01-0000-1000-8000-00805f9b34fb"
NOTIFY = ["0000ff01-0000-1000-8000-00805f9b34fb",
          "0000ff02-0000-1000-8000-00805f9b34fb",
          "0000ff06-0000-1000-8000-00805f9b34fb"]
KNOWN = {5, 15, 16, 17, 18, 19, 20, 23, 24, 29, 49, 50}
log = open("v500_log3.txt", "a")
t0 = time.time()
prev = {}


def out(s):
    print(s, flush=True); log.write(s + "\n"); log.flush()


def frame(cmd, payload=b"", ftype=0x23):
    f = bytearray([0x73, 0, ftype, cmd]) + payload
    f[1] = len(f) + 1
    c = 0
    for b in f:
        c ^= b
    return bytes(f + bytes([c]))


def handler(uuid):
    short = uuid[4:8]
    def cb(_, d):
        d = bytes(d); t = time.time() - t0
        cmd = d[3] if len(d) > 3 else None
        if cmd == 0x03 and len(d) >= 51:
            u = lambda o: struct.unpack_from("<H", d, o)[0]
            known = (f"SOC={u(17)/100:.2f}% cap={u(15)}Wh out={u(23)}W "
                     f"acin={d[29]} in={u(19)}W acout={d[5]} rated={u(49)}W")
            p = prev.get(cmd)
            unk = ""
            if p and len(p) == len(d):
                ch = [i for i in range(len(d)) if d[i] != p[i] and i not in KNOWN]
                unk = " | UNKNOWN changed " + ",".join(f"{i}:{p[i]:02x}->{d[i]:02x}" for i in ch) if ch else ""
            prev[cmd] = d
            out(f"[{t:6.1f}s] {known}{unk}")
            out(f"          raw {d.hex(' ')}")
        else:
            out(f"[{t:6.1f}s] {short} cmd={cmd if cmd is None else hex(cmd)} len={len(d)} {d.hex(' ')}")
    return cb


async def poll(c, secs):
    end = time.time() + secs
    while time.time() < end:
        await c.write_gatt_char(TX, frame(0x03), response=False)
        await asyncio.sleep(2)


async def main(addr, secs, try_output, ac=None):
    async with BleakClient(addr, timeout=20) as c:
        out(f"=== connected {addr}  mode={'try-output' if try_output else 'monitor'}")
        for u in NOTIFY:
            try:
                await c.start_notify(u, handler(u))
            except Exception as e:
                out(f"subscribe {u[4:8]} failed: {e}")
        if ac is not None:
            await poll(c, 6)
            p = b"\x01" if ac == "on" else b"\x00"
            out(f"\n>>> AC {ac}: {frame(0x02, p, 0x24).hex(' ')}")
            await c.write_gatt_char(TX, frame(0x02, p, 0x24), response=False)
            await poll(c, 10)
        elif not try_output:
            await poll(c, secs)
        else:
            await poll(c, 8)
            for p in (b"\x00", b"\x01"):
                out(f"\n>>> sending 0x0E payload {p.hex()} : {frame(0x0E, p).hex(' ')}")
                await c.write_gatt_char(TX, frame(0x0E, p), response=False)
                await poll(c, 10)
    out("=== done")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    a = sys.argv[1]
    try_out = "--try-output" in sys.argv
    nums = [int(x) for x in sys.argv[2:] if x.isdigit()]
    ac = next((x.split("=")[1] for x in sys.argv if x.startswith("--ac=")), None)
    asyncio.run(main(a, nums[0] if nums else 240, try_out, ac))
