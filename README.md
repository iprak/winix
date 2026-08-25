
![GitHub Release](https://img.shields.io/github/v/release/iprak/winix)
[![License](https://img.shields.io/packagist/l/phplicengine/bitly)](https://packagist.org/packages/phplicengine/bitly)
<a href="https://buymeacoffee.com/leolite1q" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" height="20px"></a>

## Summary

A custom component to interact with Winix air purifiers, dehumidifiers, and air conditioners.

Air purifiers: confirmed on [C545](https://www.winixamerica.com/product/certified-refurbished-c545-air-purifier/), [C610](https://www.winixamerica.com/product/c610/), and [Tower Prime APRM833-JWK](https://www.winix.com/product/1211); reported to work on [AM90](https://www.winixamerica.com/product/am90/), [HR1000](https://www.amazon.com/Winix-HR1000-5-Stage-Enabled-Cleaner/dp/B01FWS0HSY), [C909](https://www.costco.com/winix-c909-4-stage-air-purifier-with-wi-fi-%2526-plasmawave-technology.product.100842491.html), [T800](https://winixeurope.eu/air-purifiers/winix-t800-wifi/), [T810](https://www.winixamerica.com/product/t810/), [5510](http://winixamerica.com/product/5510/), [5520](http://winixamerica.com/product/5520/), [9800](https://www.winixamerica.com/product/9800/), [T500](https://www.winixamerica.com/product/t500/)…
Dehumidifiers: confirmed on [DXWE210](https://www.winix.com/product/1689) (Korean page). Other models in the `DXW*21*` family are likely compatible.

## Installation

This can be installed by copying all the files from `custom_components/winix/` to `<config directory>/custom_components/winix/`. Next add Winix integration from `Add Integration` and use your credentials from Winix mobile app.

### Air Purifier

#### Sensors

| Model | Example sensors |
| ----- | ------- |
| C545  | <img height="400" alt="image" src="https://github.com/user-attachments/assets/441943fa-9835-4405-8668-78fc15f4003a" /> |
| C610  | <img height="400" alt="image" src="https://github.com/user-attachments/assets/da1a13a6-ba3e-4fb1-bde7-6c12ed53d607" /> |


- The `Air QValue` sensor reports the qValue reported by Winix purifier. This value is related to air quality although I am not exactly sure what it represents.
- The `AQI` sensor matches the led light on the purifier.
  - Good (Blue) = 1
  - Fair (Amber) = 2
  - Poor (Red) = 3
- The `Filter Life` sensor represents the left filter life and is based on an initial life of 9 months.
- The `PM 2.5` sensor is exposed only on devices that report particulate readings (e.g., T800).
- Tower Prime APRM833-JWK exposes its Super Clean mode as the highest fan-speed percentage.

- The fan entity supports speed and preset modes
- The `Child Lock` switch toggles the device's child lock, exposed only on devices that report support for the feature.

![image](https://user-images.githubusercontent.com/6459774/212468432-0b37cd09-af5b-418c-855d-a12c8b21efc3.png)

- The device data is fetched every 30 seconds.
- There are 4 services `winix.plasmawave_off, winix.plasmawave_on, plasmawave_toggle and remove_stale_entities` in addition to the default fan services `fan.speed, fan.toggle, fan.turn_off, fan.turn_on, fan.set_preset_mode`.
  - `remove_stale_entities` can be used to remove entities which appear unavaialble when the associated device is removed from the account.


#### Brightness Level
If the purifiers support this feature, then you will see a selection list under the device.

- Winix only supports updating the brightness level when the purifier is running.
- The last brightness level is exposed as the attribute `last_brightness_level` on the fan.


### Dehumidifier

- DXWE210 will generate 7 entities.

<img width="200" alt="dehumidifier_entities" src="https://github.com/user-attachments/assets/351e9887-8d8b-4ad7-a360-77662e991473" />

- The `humidifier` entity is the primary control for the dehumidifier device.
  - Powers the device on or off.
    - Treats the `auto-dry` power state as off. It is represented by the `Auto Dry` binary sensor.
  - Sets the operating mode: `Auto`, `Manual`, `Clothes`, `Shoes`, `Quiet`, or `Continuous`.
  - Sets the target humidity, in the 35–70 % range with 5 % steps.
  - Reports the current humidity from the device's sensor.
- The `Fan Speed` select sets the fan to `low`, `high`, or `turbo`.
- The `Auto Dry` binary sensor reflects the internal drying cycle, which runs while the device is powered off.
- The `Water Tank` binary sensor reports a problem state when the tank is full or detached.
- The `Timer` number entity sets an off-timer between 0 and 24 hours.
- The `Child Lock` switch toggles the device's child lock, exposed only on devices that report support for the feature.
- The `UV Sanitize` switch toggles UV sanitization, exposed only on devices that report support for the feature.

### Air Conditioner

- Supports the [AC100](https://www.winix.com/product/list/006) window/portable air conditioner (`productGroup: "Acn01"`).
- The `climate` entity is the primary control for the air conditioner.
  - Powers the device on/off.
  - Sets the operating mode: `Auto`, `Cool`, `Fan only`, or `Dry`. (The device has no heating capability, so `Heat` is intentionally not exposed.)
  - Sets the target temperature, 18–30 °C in 1 °C steps.
  - Reports the current room temperature from the device's sensor.
- The fan mode supports speeds `1`–`5` plus `turbo`.
- Swing mode toggles left-right oscillation.
- Real-time power consumption is exposed as a separate `sensor` entity (device_class `power`).

### Note

- If devices are added/removed, then you would have to reload the integration.

- Winix **does not support** simultaneous login from multiple devices. If you logged into the mobile app after configuring HomeAssistant, then the HomeAssistant session gets flagged as invalid and vice-versa.

  - To maintain access to both the app and Home Assistant, you can set up a second account. Use this second account for Home Assistant while keeping your main account logged in on your mobile app.

    Create a second Winix account with no devices linked. Then from your main account, navigate to `Device Settings > Device Sharing > Add a user` and invite the second account.


## Language Support

Entity names and states are displayed in the language configured in Home Assistant. English and Korean are verified; German, French, Dutch, and Japanese are machine-translated. Corrections are welcome via pull request.

## Breaking Changes

- [1.1.0](https://github.com/iprak/winix/releases) changed the sensor implementation. The aqi sensor id might be different now.

- [1.0.0](https://github.com/iprak/winix/releases) introduces config flow and previous yaml based setup is no longer supported. You would want to delete that setup and proceed to setup the intgeration as mentioned in `Installation` section.
