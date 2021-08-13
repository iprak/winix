"""The Winix C545 Air Purifier component."""


from datetime import timedelta
import logging

from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from custom_components.winix.manager import WinixManager

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
MIN_SCAN_INTERVAL = timedelta(seconds=30)
SUPPORTED_PLATFORMS = ["fan", "sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=MIN_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config):
    """Set up the component."""
    domain_config = config[DOMAIN]
    scan_interval = domain_config.get(CONF_SCAN_INTERVAL, MIN_SCAN_INTERVAL)

    if scan_interval < MIN_SCAN_INTERVAL:
        _LOGGER.info(
            "scan interval increased to %s from %s",
            MIN_SCAN_INTERVAL,
            scan_interval,
        )
        scan_interval = MIN_SCAN_INTERVAL

    _LOGGER.debug("Creating locator with scan interval of %s", scan_interval)
    manager = hass.data[DOMAIN] = WinixManager(hass, domain_config, scan_interval)
    await hass.async_add_executor_job(manager.login)
    return True
