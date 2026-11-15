# JARVIS Hardware Components

This document reflects configured firmware in `ESP32_Firmware/JARVIS_ESP32/JARVIS_ESP32.ino`. Presence in firmware does **not** prove a physical component is installed; verify the actual wiring before powering the system.

| Component | Purpose | Protocol / interface | Voltage | Firmware evidence |
|---|---|---|---|---|
| ESP32 development board | Runs firmware, Wi-Fi, MQTT, sensor and relay control | Wi-Fi, GPIO, I²C, SPI | Board supply not specified | `WiFi.h`, `PubSubClient.h`, pin constants |
| DHT11 | Temperature and humidity readings | Single-wire DHT data line | Not specified in source | `DHT dht(DHT_PIN, DHT11)` |
| MQ-3 | Raw gas/alcohol sensor response | Analog input / ADC | Not specified in source | `MQ3_PIN=34`; readings are explicitly not calibrated AQI |
| PIR sensor | Motion detection | Digital GPIO | Not specified in source | `PIR_PIN=27`; motion MQTT event |
| BH1750 | Ambient light measurement | I²C | Not specified in source | I²C address `0x23`; `BH1750` |
| ADXL345 | Acceleration/vibration measurement | I²C | Not specified in source | `Adafruit_ADXL345_Unified`; firmware says it is not seismic-grade |
| SSD1306 OLED | Animated JARVIS eyes | I²C | Not specified in source | address `0x3C`, 128×64 display |
| ILI9341 TFT | Local telemetry dashboard | SPI | Not specified in source | `Adafruit_ILI9341`; configured SPI pins |
| Buzzer | Local audible motion response | Digital GPIO | Not specified in source | `BUZZER_PIN=25`; not active-low |
| Four-channel relay module | Appliance switching | Four digital GPIO outputs | Relay-module supply not specified | `RELAY_PINS={16,17,26,32}`, active-low |
| Lights / Fan / TV / AC | Relay-controlled loads | Relay outputs 1–4 | Mains characteristics not specified | Python mapping: 1 Lights, 2 Fan, 3 TV, 4 AC |
| MQTT broker | Connects ESP32 and JARVIS Python skill | TCP/IP over Wi-Fi | N/A | Python defaults to port 1883; firmware uses `MQTT_HOST`/`MQTT_PORT` |

## MQTT implementation

The firmware consumes `jarvis/esp32/command` commands in the form `relay/<1-4>/on|off`, publishes acknowledgements to `jarvis/esp32/relay/ack`, and publishes telemetry to `jarvis/esp32/sensor`. Event topics include light, temperature, air quality, vibration, and motion under `jarvis/esp32/event/`. The Python MQTT implementation is in `Software/skills/esp32_skill.py`.
