"""Constants for Shure SLX-D integration."""

DOMAIN = "shure_slxd"
DEFAULT_PORT = 2202
DEFAULT_SCAN_INTERVAL = 30  # seconds
METERING_INTERVAL = 1000  # ms for audio levels

# Audio gain settings
GAIN_STEP_DB = 1  # Step size for gain up/down buttons
GAIN_MIN_DB = -18
GAIN_MAX_DB = 42

CONF_HOST = "host"
CONF_PORT = "port"
CONF_ENABLE_METERING = "enable_metering"
