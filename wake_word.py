import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model


SAMPLE_RATE = 16000
BLOCK_SIZE = 1280
THRESHOLD = 0.30


print("Loading wake-word model...")

openwakeword.utils.download_models()

model = Model(
    wakeword_models=["hey_jarvis"]
)

print("Wake-word model loaded.")


def wait_for_wake_word():

    print("\nJARVIS is sleeping...")
    print('Say "Hey Jarvis"...')

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=BLOCK_SIZE
    ) as stream:

        while True:

            audio, overflowed = stream.read(BLOCK_SIZE)

            audio = np.asarray(audio[:, 0])

            predictions = model.predict(audio)

            score = predictions.get(
                "hey_jarvis",
                0.0
            )

            # Suppressed continuous score spam; only fire on detection
            if score >= THRESHOLD:
                print("\n\n🔥 WAKE WORD DETECTED!")
                return True

