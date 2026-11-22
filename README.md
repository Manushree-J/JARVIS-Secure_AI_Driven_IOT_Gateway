# JARVIS — Local Voice Assistant & IoT Control Gateway

JARVIS is a Windows-based voice assistant and IoT control system. It combines wake-word voice interaction, local Qwen inference through Ollama, ElevenLabs speech output, deterministic skills, an ESP32/MQTT hardware bridge, environmental sensors, camera vision, and persistent memory.

> This repository describes the implementation currently present in this folder. Some integrations are optional and require separate services or hardware.

## Problem and objectives

**JARVIS** is designed around a **privacy-first, local-first architecture** that delivers a hands-free interface for desktop automation, home-appliance control, live sensor telemetry, and contextual conversation. Instead of relying on cloud LLM APIs, core reasoning and memory run entirely on-machine via **Ollama (Qwen 2.5 7B)**, **ChromaDB**, and a local **Obsidian Markdown vault**—ensuring low-latency execution, deterministic hardware control, and zero cloud exposure for personal context or credentials.

## Features

- **Full Bidirectional Voice Pipeline:** Combines always-on `"Hey Jarvis"` wake-word detection (**OpenWakeWord**) and microphone speech-to-text capture (**SpeechRecognition**) with natural neural voice synthesis (**ElevenLabs TTS**) for seamless hands-free conversation.
- **Privacy-First Local AI & Memory:** Runs **Qwen 2.5 7B** locally through Ollama’s OpenAI-compatible API with zero cloud fallback in the text path, backed by **ChromaDB** semantic vector memory and an external **Obsidian-style Markdown vault**.
- **Custom Desktop GUI & Live Telemetry Dashboard:** Features a dedicated **CustomTkinter** desktop UI (`jarvis_ui.py`) and a **FastAPI/WebSocket** HUD (`gui_server.py`) for real-time chat interaction, visual system status, and live **ESP32** environmental sensor telemetry alongside the physical TFT/OLED hardware displays.
- **Modular Deterministic Skill Routing:** Dispatches explicit commands across Windows system controls, browser automation, coding workflows, file management, Gmail, Google Calendar, Obsidian vault actions, ESP32 relays, and computer vision.
- **Hybrid Camera Vision:** Supports local real-time object detection via **Ultralytics YOLO** and **OpenCV**, with optional cloud image analysis through OpenRouter (`skills/ai_vision_skill.py`).

## Architecture

```text
Microphone → OpenWakeWord → SpeechRecognition → JARVIS UI/AI
                                      ↓
                         Skill Manager → deterministic skill
                                      ↓
                           Qwen client → Ollama/Qwen
                                      ↓
                            ElevenLabs → speakers

ESP32 sensors/relays ← MQTT broker ← skills/esp32_skill.py
GUI Event Manager → WebSocket/FastAPI → frontend/index.html
Conversation Markdown + ChromaDB → memory.py / memory_writer.py
```

`jarvis_ai.py` and `jarvis_ui.py` are the primary Python runtime components. `gui_server.py` exposes the local WebSocket gateway; `server.py` is the existing FastAPI voice/dashboard server. Avoid starting multiple copies of these services.

## Results and demonstrations

The following images show the current JARVIS implementation, including its hardware prototype, voice interaction, ESP32 communication, memory integration, display output, and computer vision capabilities.

### 1. Hardware Prototype

![JARVIS Hardware Prototype](Results/hardware.jpg)

### 2. TFT Display and Sensor Output

![TFT Display Results](Results/TFT%20results.jpg)

### 3. Voice Interaction

![JARVIS Chat Interaction](Results/chat.jpg)

### 4. ESP32 Communication

![JARVIS ESP32 Interaction](Results/chatesp32.jpg)

### 5. Conversational Memory

![JARVIS Chat Memory](Results/chatmemory.jpg)

### 6. Obsidian Knowledge Integration

![Obsidian Brain](Results/obsidian%20brain.jpg)

### 7. Computer Vision

![OpenCV Results](Results/opencv.jpg)

### 8. Desktop User Interface

![JARVIS User Interface](Results/userinterface.jpg)
*Custom desktop interface displaying real-time conversational logs, active skill/engine status, and live ESP32 sensor telemetry alongside the physical TFT/OLED hardware displays.*

## ESP32, MQTT, sensors, and relays

`ESP32_JARVIS/ESP32_JARVIS.ino` is preserved firmware for an ESP32 dashboard. It uses MQTT topics under `jarvis/esp32/` and supports four relay outputs:

| Relay | Appliance |
|---|---|
| 1 | Lights |
| 2 | Fan |
| 3 | TV |
| 4 | AC / air conditioner |

The firmware and Python skill implement relay commands, acknowledgements, and telemetry. Sensors and peripherals in the firmware include DHT11 temperature/humidity, MQ-3 raw gas-response input, BH1750 light level, PIR motion, ADXL345 acceleration/vibration, TFT display, OLED eyes, and a buzzer.

MQ-3 values are rough raw-response categories, not certified air-quality measurements. Motion events are published by MQTT and displayed in telemetry; motion-triggered announcements are not currently implemented as a separate voice-notification subsystem.

Configure MQTT with `JARVIS_MQTT_BROKER`, `JARVIS_MQTT_PORT`, and related variables in `.env`.

## Memory and integrations

ChromaDB uses the local `jarvis_memory/` directory, which is user data and intentionally ignored by Git. Conversation and personal memory Markdown files are written to the external path configured in the source (`D:\VS\Jarvis Brain`).

Google Calendar and Gmail use OAuth through `google_auth.py`; local tokens and `client_secrets.json` must never be committed.

The text AI is local Qwen/Ollama. The existing `skills/ai_vision_skill.py` is a separate optional OpenRouter image-analysis path; this README does not claim it is available without a valid key and network access.

## Technologies

Python, FastAPI, Uvicorn, CustomTkinter, WebSockets, OpenAI-compatible Ollama API, Qwen, ElevenLabs, OpenWakeWord, SpeechRecognition, sounddevice, ChromaDB, OpenCV, Ultralytics YOLO, Paho MQTT, ESP32/Arduino, Google APIs, and Jetpack Compose in the companion Android project.

## Hardware

The firmware pin map currently defines DHT11, MQ-3, PIR, BH1750, ADXL345, ILI9341 TFT, SSD1306 OLED, buzzer, and four active-low relay outputs.

Review wiring and electrical isolation before connecting mains appliances. The firmware starts relay outputs off.

## Installation

1. Install Python 3.11 or a compatible supported Python version.
2. Install dependencies:

   ```bash
   py -3 -m pip install -r requirements.txt
   ```

3. Install and start Ollama, then obtain the configured model:

   ```bash
   ollama pull qwen2.5:7b
   ```

4. Install and run a local MQTT broker such as Mosquitto when using ESP32 features.
5. Copy `.env.example` to `.env` and fill in only local credentials and service settings.
6. For Google skills, configure OAuth client credentials locally and complete the interactive authorization flow.
7. For camera skills, ensure camera permissions, YOLO weights, and any optional vision API access are configured.

## Running

The desktop runtime is started from the project directory with:

```bash
py -3 jarvis_ai.py
```

The existing local FastAPI/WebSocket components can be started separately when needed, for example:

```bash
py -3 -m uvicorn gui_server:app --host 127.0.0.1 --port 8000
```

Do not start duplicate JARVIS, GUI, or WebSocket processes. Say "Hey Jarvis" after the desktop runtime is ready.

## Directory structure

```text
.
├── jarvis_ai.py             # Core voice/conversation loop
├── jarvis_ui.py             # CustomTkinter desktop UI and engine bridge
├── skill_manager.py         # Skill registry and router
├── skills/                  # Windows, vision, ESP32, Google, and other skills
├── qwen_client.py           # Ollama/Qwen client
├── speech.py                # Speech recognition and ElevenLabs TTS
├── memory_writer.py         # ChromaDB + external Markdown persistence
├── gui_server.py            # Local FastAPI/WebSocket gateway
├── frontend/                # Web HUD
├── server.py                # Existing FastAPI dashboard/voice server
├── ESP32_JARVIS/            # ESP32 firmware
├── JARVIS-Companion/        # Android companion project
├── Results/                 # Project demonstration images
├── .env.example             # Safe configuration template
└── requirements.txt         # Python dependencies
```

## Known limitations

- Ollama, MQTT, microphone, speakers, camera, and external Google/ElevenLabs services are environment-dependent.
- Conversation paths are currently Windows-specific and point to an external vault.
- The OpenRouter image-analysis path remains separate from local Qwen and requires a valid optional credential.
- Sensor thresholds are hardware-specific; MQ-3 readings are not calibrated AQI.
- The Android companion is currently a starter Compose application rather than a complete JARVIS control client.
- No automated end-to-end hardware test is included.


## Security and repository policy

Never commit `.env`, OAuth client files, tokens, private keys, memory databases, generated logs, model caches, or personal vault data.

Rotate any credential that has ever been stored in a local file exposed outside the machine.


