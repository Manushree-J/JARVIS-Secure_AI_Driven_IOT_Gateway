# ESP32 Pin Connections

Derived only from `ESP32_Firmware/JARVIS_ESP32/JARVIS_ESP32.ino`. “Component pin” identifies the signal role; module-specific physical pin labels must be verified against each component’s datasheet.

| Component | Component pin | ESP32 GPIO | Interface | Purpose |
|---|---|---:|---|---|
| DHT11 | DATA | 4 | DHT single-wire | Temperature/humidity input |
| MQ-3 | Analog output (AO) | 34 | ADC | Raw gas/alcohol response |
| PIR | Digital output (OUT) | 27 | Digital GPIO | Motion input |
| BH1750 | SDA | 21 | I²C | Light-level data |
| BH1750 | SCL | 22 | I²C | Light-level clock |
| BH1750 | I²C address | `0x23` | I²C | Firmware-configured address |
| ADXL345 | SDA | 21 | I²C | Acceleration data |
| ADXL345 | SCL | 22 | I²C | Acceleration clock |
| SSD1306 OLED | SDA | 21 | I²C | Display data |
| SSD1306 OLED | SCL | 22 | I²C | Display clock |
| SSD1306 OLED | I²C address | `0x3C` | I²C | Firmware-configured address |
| ILI9341 TFT | CS | 5 | SPI | Chip select |
| ILI9341 TFT | DC | 2 | Digital GPIO | Data/command select |
| ILI9341 TFT | RESET | 15 | Digital GPIO | Display reset |
| ILI9341 TFT | SCK | 18 | SPI | Clock |
| ILI9341 TFT | MISO | 19 | SPI | Controller-to-ESP32 data |
| ILI9341 TFT | MOSI | 23 | SPI | ESP32-to-controller data |
| Buzzer | Input | 25 | Digital GPIO | Local alert output |
| Relay channel 1 | IN1 | 16 | Digital GPIO, active-low | Lights |
| Relay channel 2 | IN2 | 17 | Digital GPIO, active-low | Fan |
| Relay channel 3 | IN3 | 26 | Digital GPIO, active-low | TV |
| Relay channel 4 | IN4 | 32 | Digital GPIO, active-low | AC |

## Needs verification

- Power (VCC/VIN), ground, level shifting, and relay contact/load wiring are not specified by the firmware.
- The ESP32 board variant and its power source are not identified.
- `MQTT_HOST` and Wi-Fi placeholder values in the firmware are machine-specific and must be supplied through a secure local build configuration before deployment.
