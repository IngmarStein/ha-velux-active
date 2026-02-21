"""Constants for the Velux ACTIVE integration."""

DOMAIN = "velux_active"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# Well-known app credentials (public, embedded in the Velux ACTIVE mobile app)
DEFAULT_CLIENT_ID = "5931426da127d981e76bdd3f"
DEFAULT_CLIENT_SECRET = "6ae2d89d15e767ae5c56b456b452d319"

AUTH_URL = "https://app.velux-active.com/oauth2/token"
HOMES_DATA_URL = "https://app.velux-active.com/api/homesdata"
HOME_STATUS_URL = "https://app.velux-active.com/syncapi/v1/homestatus"
SET_STATE_URL = "https://app.velux-active.com/syncapi/v1/setstate"
SET_PERSONS_AWAY_URL = "https://app.velux-active.com/api/setpersonsaway"

MODULE_TYPE_BRIDGE = "NXG"
MODULE_TYPE_ROLLER_SHUTTER = "NXO"
MODULE_TYPE_DEPARTURE_SWITCH = "NXD"
MODULE_TYPE_SENSOR = "NXS"

UPDATE_INTERVAL = 60  # seconds
