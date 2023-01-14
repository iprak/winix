# Summary

A custom component to interact with Winix [C545](https://www.winixamerica.com/product/certified-refurbished-c545-air-purifier/) Air Purifier. This has also been reported to work with models [AM90](https://www.winixamerica.com/product/am90/) and [HR1000](https://www.amazon.com/Winix-HR1000-5-Stage-Enabled-Cleaner/dp/B01FWS0HSY).

# Installation

This can be installed by copying all the files from `custom_components/winix/` to `<config directory>/custom_components/winix/`. Next add Winix integration from `Add Integration` and use your credentials from Winix mobile app.

- You should now see one device and 4 entities being created.

![image](https://user-images.githubusercontent.com/6459774/212468308-e6e855ac-ad26-4405-b683-246ccf4c8ccc.png)

- The `Filter Life` sensor represents the left filter life and is based on an initial life of 9 months.

- The fan entity supports speed and preset modes

![image](https://user-images.githubusercontent.com/6459774/212468432-0b37cd09-af5b-418c-855d-a12c8b21efc3.png)

- The device data is fetched every 30 seconds.
- There are 3 new services `winix.plasmawave_off, winix.plasmawave_on, plasmawave_toggle` in addition to the default fan services `fan.speed, fan.toggle, fan.turn_off, fan.turn_on, fan.set_preset_mode`.

## Note
- If purifiers are added/removed, then you would want to restart HomeAssistant.

- Winix **does not support** simultaneous login from multiple devices. If you logged into the mobile app after configuring HomeAssistant, then the HomeAssistant session gets flagged as invalid and vice-versa.

# Breaking Changes

- [1.1.0](https://github.com/iprak/winix/releases) changed the sensor implementation. The aqi sensor id might be different now.

- [1.0.0](https://github.com/iprak/winix/releases) introduces config flow and previous yaml based setup is no longer supported. You would want to delete that setup and proceed to setup the intgeration as mentioned in `Installation` section.
