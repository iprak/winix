
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

The integration provides sensors and controls for the purifier:

  <img height="400" alt="image" src="https://github.com/user-attachments/assets/441943fa-9835-4405-8668-78fc15f4003a" />

Sensor entities are created according to the device model, so the available sensors vary. Supported models may expose PM1.0, PM2.5, or PM10 measurements and their corresponding `Good`, `Fair`, `Poor`, or `Very Poor` level; gas sensor readings and levels; ambient brightness; RPM; or CO2. The `Air Purification Index` sensor is available on supported models and reports a percentage. The older `Air QValue` and `AQI` sensors are no longer created.

| Model IDs | Model-specific sensors |
| --------- | ---------------------- |
| `T500_AU`, `ZEROS_EU`, `T500_EU`, `ZEROS_GB`, `T500_GB`, `ZEROS_ID`, `T500_ID`, `TOWER_Q`, `ZEROS_TW`, `T500_TW` | PM10, PM10 Level, Ambient Brightness |
| `C610_AU`, `C5_AU`, `A400_US`, `C610_US`, `C545`, `C909`, `T500_US`, `9800`, `AZSUUS`, `C5_ID`, `T500_JP`, `C5`, `XLC`, `NK105` | Gas Sensor, Gas Sensor Level, Ambient Brightness |
| `T800_AU`, `T1000_AU`, `T800_ID`, `T1000_KR`, `XQLASER`, `XQ20`, `XQ`, `T800_TW`, `TOWERXQ_WA`, `XQPRO_WA` | PM2.5, PM2.5 Level, Gas Sensor, Gas Sensor Level, Ambient Brightness |
| `5520_AU`, `5530_US`, `5520_US`, `5510_US` | Gas Sensor, Gas Sensor Level, Ambient Brightness, RPM |
| `C710_US` | PM2.5, PM2.5 Level, Ambient Brightness, Air Purification Index |
| `T800_US`, `T800_EU`, `T800_GB`, `T800_JP` | PM2.5, PM2.5 Level, Ambient Brightness |
| `T1000_PPS` | PM2.5, PM2.5 Level, Gas Sensor, Gas Sensor Level, Ambient Brightness, CO2 |
| `PRIMEKOR`, `MASTERKOR` | PM1.0, PM1.0 Level, PM2.5, PM2.5 Level, PM10, PM10 Level, Gas Sensor, Gas Sensor Level, Ambient Brightness |
| `AZPUEU`, `TITAN`, `HERA`, `T1` | PM10, PM10 Level, Gas Sensor, Gas Sensor Level, Ambient Brightness |
| `AC100`, `AC101` | Indoor Temperature, Outdoor Temperature, Indoor Fan Speed, Outdoor Fan Speed, Current Compressor Speed, Power Consumption |


- `Filter Life` and `Max Filter Life` are additionally created for all air purifiers. The `Filter Life` sensor reports the remaining filter life as a percentage. Its calculation uses the model's filter lifetime, which is 9 months by default and may differ by model. The sensor also exposes `operating_hours` and `filter_replace_date` attributes. `Max Filter Life` reports that lifetime in hours.
- Tower Prime APRM833-JWK exposes its Super Clean mode as the highest fan-speed percentage.

- The fan entity supports speed and preset modes.
- The `Child Lock` switch toggles the device's child lock, exposed only on devices that report support for the feature.
- The integration registers four custom services: `winix.plasmawave_off`, `winix.plasmawave_on`, `winix.plasmawave_toggle`, and `winix.remove_stale_entities`. Standard Home Assistant fan controls are also available.
  - `winix.remove_stale_entities` removes unavailable Winix entities and their associated devices from Home Assistant's registries.
- If the device supports brightness adjustment, a selection entity is available. The brightness level can only be adjusted while the purifier is running.


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

### General Notes

- For all device types, the data is fetched every 30 seconds.
- If devices are added/removed, then you would have to reload the integration.

- Winix **does not support** simultaneous login from multiple devices. If you logged into the mobile app after configuring HomeAssistant, then the HomeAssistant session gets flagged as invalid and vice-versa.

  - To maintain access to both the app and Home Assistant, you can set up a second account. Use this second account for Home Assistant while keeping your main account logged in on your mobile app.

    Create a second Winix account with no devices linked. Then from your main account, navigate to `Device Settings > Device Sharing > Add a user` and invite the second account.


## Language Support

Entity names and states are displayed in the language configured in Home Assistant. English and Korean are verified; German, French, Dutch, and Japanese are machine-translated. Corrections are welcome via pull request.

## Breaking Changes

- Sensor entities are now defined per device model. The older `Air QValue` and `AQI` sensors have been removed and replaced with model-specific sensors; update any automations or dashboards that refer to the old entities.
- [1.1.0](https://github.com/iprak/winix/releases) changed the sensor implementation; older sensor entities may have different IDs.

- [1.0.0](https://github.com/iprak/winix/releases) introduced config flow; the previous YAML-based setup is no longer supported. Remove the old setup and configure the integration as described in the `Installation` section.
