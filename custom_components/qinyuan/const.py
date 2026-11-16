"""Constants for Qinyuan Water Purifier integration."""

DOMAIN = "qinyuan"

CONF_AUTH_TOKEN = "auth_token"
CONF_IOT_TOKEN = "iot_token"
CONF_APP_SECRET = "app_secret"
CONF_DEVICE_ID = "device_id"

DEFAULT_POLL_INTERVAL = 60  # seconds

# Status mapping for WorkState
WORK_STATE_MAP = {
    0: "待机",
    1: "正常",
    2: "制水",
    3: "冲洗",
    4: "缺水",
    5: "满水",
}
