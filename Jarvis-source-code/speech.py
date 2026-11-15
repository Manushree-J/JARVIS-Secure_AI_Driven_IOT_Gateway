import os
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

ELEVENLABS_MODEL_ID = os.getenv(
    "ELEVENLABS_MODEL_ID",
    "eleven_multilingual_v2"
)

ELEVENLABS_OUTPUT_FORMAT = os.getenv(
    "ELEVENLABS_OUTPUT_FORMAT",
    "pcm_24000"
)


# ============================================================
# ELEVENLABS CLIENT
# ============================================================

if not ELEVENLABS_API_KEY:
    print("❌ ELEVENLABS_API_KEY not found in .env")

if not ELEVENLABS_VOICE_ID:
    print("❌ ELEVENLABS_VOICE_ID not found in .env")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
)


# ============================================================
# SPEECH RECOGNITION
# ============================================================

listener = sr.Recognizer()

listener.energy_threshold = 300
listener.dynamic_energy_threshold = True

# Allows natural pauses while speaking
listener.pause_threshold = 1.5

listener.phrase_threshold = 0.3
listener.non_speaking_duration = 0.5


def listen():

    with sr.Microphone() as source:

        print("\n🎤 Listening...")

        try:

            audio = listener.listen(
                source,
                timeout=15,
                phrase_time_limit=30
            )

            text = listener.recognize_google(audio)

            print(f"Master: {text}")

            return text.lower()

        except sr.WaitTimeoutError:

            return ""

        except sr.UnknownValueError:

            print("❌ Could not understand.")

            return ""

        except sr.RequestError as e:

            print(
                "❌ Speech recognition service unavailable:",
                e
            )

            return ""


# ============================================================
# ELEVENLABS TEXT-TO-SPEECH
# ============================================================

def speak(text):

    if not text:
        return

    print(f"JARVIS: {text}")

    try:

        # ----------------------------------------------------
        # Generate speech
        # ----------------------------------------------------

        audio_stream = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL_ID,
            output_format=ELEVENLABS_OUTPUT_FORMAT,
            text=text
        )

        # ----------------------------------------------------
        # Collect audio chunks
        # ----------------------------------------------------

        audio_bytes = b""

        for chunk in audio_stream:

            if chunk:
                audio_bytes += chunk

        if not audio_bytes:

            print("❌ ElevenLabs returned empty audio.")

            return

        # ----------------------------------------------------
        # Convert PCM bytes to NumPy audio
        # ----------------------------------------------------

        audio_data = np.frombuffer(
            audio_bytes,
            dtype=np.int16
        )

        # ----------------------------------------------------
        # Play audio
        # ----------------------------------------------------

        sd.play(
            audio_data,
            samplerate=24000
        )

        sd.wait()

    except Exception as e:

        print("❌ ElevenLabs Speak Error:")

        print(e)