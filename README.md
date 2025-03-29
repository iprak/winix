
![GitHub Release](https://img.shields.io/github/v/release/iprak/winix)
[![License](https://img.shields.io/packagist/l/phplicengine/bitly)](https://packagist.org/packages/phplicengine/bitly)
<a href="https://buymeacoffee.com/leolite1q" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" height="20px"></a>

## Summary

A custom component to interact with Winix [C545](https://www.winixamerica.com/product/certified-refurbished-c545-air-purifier/) and [C610](https://www.winixamerica.com/product/c610/) air purifiers.

This has also been reported to work with these models: [AM90](https://www.winixamerica.com/product/am90/), [HR1000](https://www.amazon.com/Winix-HR1000-5-Stage-Enabled-Cleaner/dp/B01FWS0HSY), [C909](https://www.costco.com/winix-c909-4-stage-air-purifier-with-wi-fi-%2526-plasmawave-technology.product.100842491.html), [T800](https://winixeurope.eu/air-purifiers/winix-t800-wifi/) but with potentially limited functionality.

## Installation

This can be installed by copying all the files from `custom_components/winix/` to `<config directory>/custom_components/winix/`. Next add Winix integration from `Add Integration` and use your credentials from Winix mobile app.

- C545 will generate 4 entities.
- C610 will generate 6 entities.

![image](https://user-images.githubusercontent.com/6459774/212468308-e6e855ac-ad26-4405-b683-246ccf4c8ccc.png)

- The `Air QValue` sensor reports the qValue reported by Winix purifier. This value is related to air quality although I am not exactly sure what it represents.
- The `AQI` sensor matches the led light on the purifier.
  - Good (Blue) = 1
  - Fair (Amber) = 2
  - Poor (Red) = 3
- The `Filter Life` sensor represents the left filter life and is based on an initial life of 9 months.

- The fan entity supports speed and preset modes

![image](https://user-images.githubusercontent.com/6459774/212468432-0b37cd09-af5b-418c-855d-a12c8b21efc3.png)

- The device data is fetched every 30 seconds.
- There are 4 services `winix.plasmawave_off, winix.plasmawave_on, plasmawave_toggle and remove_stale_entities` in addition to the default fan services `fan.speed, fan.toggle, fan.turn_off, fan.turn_on, fan.set_preset_mode`.
  - `remove_stale_entities` can be used to remove entities which appear unavaialble when the associated device is removed from the account.

### Note

- If purifiers are added/removed, then you would have to reload the integration.

- Winix **does not support** simultaneous login from multiple devices. If you logged into the mobile app after configuring HomeAssistant, then the HomeAssistant session gets flagged as invalid and vice-versa.

## Breaking Changes

- [1.1.0](https://github.com/iprak/winix/releases) changed the sensor implementation. The aqi sensor id might be different now.

- [1.0.0](https://github.com/iprak/winix/releases) introduces config flow and previous yaml based setup is no longer supported. You would want to delete that setup and proceed to setup the intgeration as mentioned in `Installation` section.
