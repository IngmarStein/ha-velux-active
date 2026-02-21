# Project Overview
This project is a native Home Assistant custom integration for the **Velux ACTIVE** KIX 300 system. It communicates directly with the Velux cloud API, employing the same reverse-engineered protocol used by the official mobile app, bypassing the need for the Apple HomeKit ecosystem.

The integration provides `cover` entities (for shutters/windows) and `sensor` entities (for climate data like CO2, humidity, temperature, etc.) via cloud polling. 

## Branding
- **Icons**: Brand assets (`icon.png`, `logo.png`) are located in the repository root for HACS support. 
- **Integration Icon**: To display the icon in the main Home Assistant UI, the `velux_active` domain must be registered in the official [Home Assistant Brands](https://github.com/home-assistant/brands) repository.

## Main Technologies
- Python
- Home Assistant Integration APIs
- `aiohttp` for asynchronous HTTP requests
- `pytest` and `pytest-asyncio` for testing

## Architecture
- **Authentication**: Uses OAuth 2.0 password grant using client credentials embedded in the Velux ACTIVE app (configured via Config Flow).
- **Communication**: Cloud polling integration (`iot_class: cloud_polling`). A coordinator fetches and syncs data from Velux's endpoints.
- **Component Structure**: Follows the standard Home Assistant custom component layout located in `custom_components/velux_active/`.
    - `api.py`: Handles direct communication with the Velux API.
    - `config_flow.py`: UI setup flow for adding the integration.
    - `coordinator.py`: Manages periodic data polling from the cloud.
    - `cover.py` & `sensor.py`: Platform setups exposing devices to Home Assistant.

## Building and Running
As a Home Assistant custom component, this project is not run as a standalone application.

### Installation for Development/Usage
1. Copy or symlink the `custom_components/velux_active` folder into your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. Configure via the UI: **Settings** -> **Devices & Services** -> **Add Integration** -> **Velux ACTIVE**.

### Testing
The project uses `pytest` for automated testing.
1. Install testing dependencies:
   ```bash
   pip install -r requirements_test.txt
   ```
2. Run tests:
   ```bash
   pytest
   ```

## Development Conventions
- **Asynchronous Code**: Strictly adheres to Python's `async`/`await` patterns for non-blocking I/O operations, which is required by Home Assistant's core event loop.
- **Translations**: UI strings and configuration flows use JSON translation files located in `custom_components/velux_active/translations/`.
- **Formatting & Style**: Standard Python formatting practices applicable to Home Assistant core and custom integrations.
