# LedFX for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![CodeQL](https://img.shields.io/badge/CODEQL-Passing-30C854.svg?style=for-the-badge)](https://github.com/dmamontov/hass-miwifi/actions?query=CodeQL)
[![Telegram](https://img.shields.io/badge/Telegram-channel-34ABDF.svg?style=for-the-badge)](https://t.me/hass_miwifi)

Component for deep integration [LedFx](https://github.com/LedFx/LedFx) from [Home Assistant](https://www.home-assistant.io/).

## Table of Contents
- [FAQ](#faq)
- [Install](#install)
- [Config](#config)
- [Performance](#performance)

## FAQ
**Q. What versions were tested on?**

**A.** So far only [0.10.7](https://github.com/LedFx/LedFx/releases/tag/v0.10.7)

**Q. Does it support audio settings?**

**A.** Yes, it supports

**Q. Can I change the effect settings?**

**A.** You can, for this, enable the appropriate mode from the [PRO] section. The required objects will only be available when supported by the effect.

**Q. Is Basic Auth supported?**

**A.** Yes, [OPTIONAL] support.

## Install
The easiest way to install the `LedFx` integration is with [HACS](https://hacs.xyz/). First install [HACS](https://hacs.xyz/) if you don’t have it yet. After installation you can find this integration in the [HACS](https://hacs.xyz/) store under integrations.

Alternatively, you can install it manually. Just copy and paste the content of the hass-ledfx/custom_components folder in your config/custom_components directory. As example, you will get the sensor.py file in the following path: /config/custom_components/ledfx/sensor.py. The disadvantage of a manual installation is that you won’t be notified about updates.
## Config
**Via GUI**

`Settings` > `Integrations` > `Plus` > `MiWiFi`

For authorization, use the ip of your router and its password

❗ Via YAML (legacy way) not supported

## Performance
![](/images/performance.gif)

1. Install [lovelace-auto-entities](https://github.com/thomasloven/lovelace-auto-entities) from HACS
2. Install [light-entity-card](https://github.com/ljmerza/light-entity-card) from HACS
3. Add new Lovelace card before that replacing `<your_device_id>`: [example](https://gist.github.com/dmamontov/34d252351d9eda98f53b2d6180771f12)
