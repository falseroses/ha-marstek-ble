"""Constants for the Marstek BLE integration."""

DOMAIN = "marstek_ble"

CONF_POLL_INTERVAL = "poll_interval"
CONF_MEDIUM_POLL_INTERVAL = "medium_poll_interval"

# BLE Service and Characteristic UUIDs
SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
CHAR_WRITE_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"

# Device name prefixes for discovery
# MST_ACCP_ = Hardware v2 (Venus E)
# MST_VNSE3_ = Hardware v3
# HM_V500_ = Marstek V500 portable power station (solar generator)
V500_PREFIX = "HM_V500_"
DEVICE_PREFIXES = ("MST_ACCP_", "MST_VNSE3_", V500_PREFIX)

MODEL_VENUS_E = "Venus E"
MODEL_VENUS_E_V3 = "Venus E 3.0"
MODEL_V500 = "V500"

# The V500 answers slower than the Venus E (~2-2.5 s per request).
RESPONSE_TIMEOUT_DEFAULT = 2.0
RESPONSE_TIMEOUT_V500 = 4.0


def is_v500(name: str | None) -> bool:
    """Return True if the BLE name belongs to a Marstek V500."""
    return bool(name) and name.upper().startswith(V500_PREFIX)


def model_from_name(name: str | None) -> str:
    """Derive a human readable model from the advertised BLE name."""
    upper = (name or "").upper()
    if upper.startswith(V500_PREFIX):
        return MODEL_V500
    if upper.startswith("MST_VNSE3_"):
        return MODEL_VENUS_E_V3
    return MODEL_VENUS_E

# Update intervals (seconds)
UPDATE_INTERVAL_FAST = 1  # Runtime info, BMS data
UPDATE_INTERVAL_MEDIUM = 60  # System data, WiFi, config
UPDATE_INTERVAL_SLOW = 300  # Timer info, logs

DEFAULT_POLL_INTERVAL = UPDATE_INTERVAL_FAST
DEFAULT_MEDIUM_POLL_INTERVAL = UPDATE_INTERVAL_MEDIUM
MIN_POLL_INTERVAL = 1
MAX_POLL_INTERVAL = 60
MIN_MEDIUM_POLL_INTERVAL = 5
MAX_MEDIUM_POLL_INTERVAL = 300

# Backoff intervals (seconds) applied after successive failures.
BACKOFF_INTERVALS = (
    UPDATE_INTERVAL_FAST,  # Baseline (no backoff)
    5,
    15,
    30,
    60,
)

# Command codes
CMD_RUNTIME_INFO = 0x03
CMD_DEVICE_INFO = 0x04
CMD_EPS_MODE = 0x05
CMD_AC_INPUT = 0x06
CMD_GENERATOR = 0x07
CMD_WIFI_SSID = 0x08
CMD_BUZZER = 0x09
CMD_WORK_MODE = 0x09  # Manual mode
CMD_AI_MODE = 0x0A  # AI Optimization mode (SETTINGS_INFO)
# Note: 0x0D is dual-purpose - reads system data, writes charge mode
CMD_CHARGE_MODE = 0x0D
CMD_SYSTEM_DATA = 0x0D
CMD_AUTO_MODE = 0x0E  # Self-Consumption mode (also OUTPUT_CONTROL)
CMD_OUTPUT_CONTROL = 0x0E
CMD_TIMER_INFO = 0x13
CMD_BMS_DATA = 0x14
CMD_POWER_MODE = 0x15
CMD_AC_POWER = 0x16
CMD_TOTAL_POWER = 0x17
CMD_CONFIG_DATA = 0x1A
CMD_LOGS = 0x1C
CMD_CT_POLLING_RATE_WRITE = 0x20
CMD_CT_POLLING_RATE = 0x22
CMD_METER_IP = 0x21
CMD_NETWORK_INFO = 0x24
CMD_REBOOT = 0x25
CMD_LOCAL_API_STATUS = 0x28

# Frame structure
FRAME_START = 0x73
FRAME_TYPE = 0x23

# Marstek V500 control (captured from the Marstek iOS app over BLE):
#   73 06 24 02 01 52  -> AC output ON
#   73 06 24 02 00 53  -> AC output OFF
# Note the frame type byte 0x24 (write) instead of 0x23; the V500 does not
# answer these frames, the new state shows up in the next 0x03 runtime frame.
FRAME_TYPE_V500_WRITE = 0x24
CMD_V500_AC_OUTPUT = 0x02
