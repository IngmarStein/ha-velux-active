# Velux ACTIVE – Home Assistant Integration

<p align="center">
  <img src="logo.png" alt="Velux ACTIVE" width="200">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A native Home Assistant integration for the **Velux ACTIVE** KIX 300 system. It communicates directly with the Velux cloud API (the same reverse-engineered protocol used by the official mobile app) without requiring the Apple HomeKit ecosystem.

---

## Why use this instead of HomeKit?

Velux ACTIVE devices can be paired with Apple HomeKit out of the box. That works well in an Apple-centric setup, but has several limitations compared to this integration:

| Feature | HomeKit (built-in HA) | This integration |
|---|---|---|
| **Requires Apple ecosystem** | Yes (iPhone/iPad for initial pairing) | No |
| **Works with Android / web** | Limited | ✅ Full HA UI |
| **Room sensors exposed** | ✅ CO₂, humidity, temperature | ✅ CO₂, humidity, temperature, illuminance, air-quality index |
| **HA automations & scripts** | Basic | ✅ Full access |
| **Position feedback** | Limited | ✅ Current position from API |
| **Stop command** | ❌ No | ✅ Yes |
| **Connection type** | Local (WiFi) | Cloud polling (60 s default) |
| **Works without internet** | ✅ Yes | ❌ No |

**In summary:** use HomeKit if you want local, low-latency control from Apple devices. Use this integration if you want full Home Assistant capabilities (automations, scripts, dashboards), the complete sensor set (illuminance, air-quality index), or don't use Apple hardware.

---

## Supported devices

| Type code | Description | HA platform |
|---|---|---|
| **NXO** | Roller shutter / window actuator | `cover` |
| **NXG** | KIX 300 bridge (gateway) | – (coordinator) |
| **NXS** | Indoor climate sensor | `sensor` |
| **NXD** | Departure switch | – |

### Cover entities (NXO)
Each roller shutter or window actuator becomes a `cover` entity with full support for:
- Open / Close / Stop
- Set position (0 % = fully closed, 100 % = fully open)
- Current position read-back
- Availability tracking (marks unavailable when device is unreachable)

### Sensor entities (NXS / room data)
For each room that reports sensor data, the following sensors are created (only the ones that are actually reported by the API):

| Sensor | Unit | Device class |
|---|---|---|
| CO₂ | ppm | `co2` |
| Humidity | % | `humidity` |
| Temperature | °C | `temperature` |
| Illuminance | lx | `illuminance` |
| Air Quality Index | – | – |

---

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=IngmarStein&repository=ha-velux-active&category=integration)

1. Open HACS → **Integrations** → ⋮ menu → **Custom repositories**.
2. Add `https://github.com/IngmarStein/ha-velux-active` with category **Integration**.
3. Search for **Velux ACTIVE** and install it.
4. Restart Home Assistant.

### Manual installation

1. Copy the `custom_components/velux_active` folder into your HA `custom_components` directory.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Velux ACTIVE**.
3. Enter the **email address and password** you use for the Velux ACTIVE mobile app.
4. If your account has more than one home, select the one you want to add.

The integration creates one config entry per Velux home. To add multiple homes, repeat the setup.

### Options

After setup you can adjust the **polling interval** (default: 60 seconds, min: 10 s, max: 3600 s) via the integration's *Configure* button.

---

## Technical background

The integration uses the same REST API as the official Velux ACTIVE mobile app, which is largely compatible with the [Netatmo API](https://dev.netatmo.com/). The protocol has been reverse-engineered and is documented at [velux-protocol.md](https://github.com/nougad/velux-cli/blob/master/velux-protocol.md) (third-party resource; contents may change).

Authentication is OAuth 2.0 password grant using the well-known client credentials embedded in the Velux ACTIVE app. Tokens are automatically refreshed; if the refresh token expires the integration will re-authenticate using the stored username/password.

Key endpoints:
- `POST https://app.velux-active.com/oauth2/token` – authenticate / refresh
- `POST https://app.velux-active.com/api/homesdata` – list homes and modules
- `POST https://app.velux-active.com/syncapi/v1/homestatus` – poll current state
- `POST https://app.velux-active.com/syncapi/v1/setstate` – control devices

The design is informed by studying the [Netatmo integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/netatmo) in Home Assistant core and the [pyatmo](https://github.com/jabesq-org/pyatmo) library on which it is based.

---

## Troubleshooting

**"Someone has logged into your VELUX ACTIVE account" emails** – This is normal. Whenever Home Assistant is restarted and the integration creates a new session with the Velux API, Velux may send an automated security alert to your email address. Currently, there is no known way to disable these alerts from the Velux side.

**"Invalid credentials"** – Check your email/password in the Velux ACTIVE app. The app and this integration share the same account.

**Devices unavailable** – The KIX 300 bridge must be powered on and connected to the internet. Check the bridge LED status.

**Sensors missing** – Room sensors are only created for measurements that are actually reported by the API. If a sensor type is missing, check whether it is visible in the Velux ACTIVE app.

**Slow response** – The integration polls the cloud every 60 seconds by default. You can reduce this in the integration options, but be aware of API rate limits.

---

## License

[Apache License 2.0](LICENSE)
