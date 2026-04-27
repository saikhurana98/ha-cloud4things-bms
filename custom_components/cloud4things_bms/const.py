DOMAIN = "cloud4things_bms"
CONF_API_URL = "api_url"
CONF_ACCESS_TOKEN = "access_token"
CONF_INTENT = "intent"
CONF_INTENT_ID = "intent_id"
CONF_SKILL = "skill"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_API_URL = "https://apiaarurobot.cloud4things.com/api/request"
DEFAULT_INTENT = "BMS-METER-DASHBOARD-ANDROID"
DEFAULT_INTENT_ID = "BUILDING-MANAGEMENT-SYSTEM-BMS-METER-DASHBOARD-ANDROID"
DEFAULT_SKILL = "BUILDING-MANAGEMENT-SYSTEM"
DEFAULT_SCAN_INTERVAL = 60

SENSOR_UNIT_MAP = {
    "kwh": "kWh",
    "kw": "kW",
    "w": "W",
    "wh": "Wh",
    "v": "V",
    "a": "A",
    "pf": None,
    "hz": "Hz",
    "%": "%",
}

SENSOR_DEVICE_CLASS_MAP = {
    "energy": "energy",
    "power": "power",
    "voltage": "voltage",
    "current": "current",
    "frequency": "frequency",
}
