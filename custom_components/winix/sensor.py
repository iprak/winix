# """Winix Air Purfier Air Quality Sensor"""

# from datetime import timedelta
# from homeassistant.helpers.entity import Entity
# from homeassistant.components.sensor import DOMAIN

# import logging
# import voluptuous as vol

# from . import (
#     ATTR_AIR_QUALITY,
#     DOMAIN as WINIX_DOMAIN,
#     WinixDeviceDataWrapper,
#     WinixManager,
# )

# _LOGGER = logging.getLogger(__name__)
# SCAN_INTERVAL = timedelta(seconds=10)


# async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
#     manager: WinixManager = hass.data[WINIX_DOMAIN]

#     entities = []
#     for wrapper in manager.get_device_wrappers():
#         entities.append(WinixPurifier(wrapper, manager.get_prefix()))

#     async_add_entities(entities, False)
#     _LOGGER.info("Added %s sensors", len(entities))


# class WinixPurifier(Entity):
#     """Representation of a Winix Purifier air quality sensor"""

#     def __init__(self, wrapper: WinixDeviceDataWrapper, prefix: str) -> None:
#         """Initialize the sensor."""
#         self._wrapper = wrapper

#         if len(prefix) > 0:
#             self._id = f"{DOMAIN}.{prefix}_{wrapper.info.mac.lower()}"
#         else:
#             self._id = f"{DOMAIN}.{WINIX_DOMAIN}_{wrapper.info.mac.lower()}"

#     @property
#     def name(self) -> str:
#         """Return the name of the switch."""
#         return f"{self._wrapper.info.alias}"

#     @property
#     def entity_id(self) -> str:
#         """Return the unique id of the switch."""
#         return self._id

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._wrapper.air_qvalue()

#     @property
#     def device_state_attributes(self):
#         """Return the state attributes."""
#         attributes = {}

#         if self._wrapper.get_state() is not None:
#             attributes[ATTR_AIR_QUALITY] = self._wrapper.get_state().get("air_quality")

#         return attributes
