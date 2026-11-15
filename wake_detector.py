import time
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000
CHANNELS = 1

CLAP_THRESHOLD = 0.10

MIN_CLAP_GAP = 0.15
MAX_CLAP_GAP = 0.80


def detect_clap(indata):

    audio = indata[:, 0]

    volume = np.sqrt(
        np.mean(audio ** 2)
    )

    return volume > CLAP_THRESHOLD


def wait_for_double_clap():

    print("\nJARVIS is sleeping...")
    print("👏👏 Double clap to wake")

    last_clap = 0

    def callback(indata, frames, time_info, status):

        nonlocal last_clap

        if detect_clap(indata):

            now = time.time()

            if (
                last_clap != 0
                and MIN_CLAP_GAP
                <= now - last_clap
                <= MAX_CLAP_GAP
            ):

                raise sd.CallbackStop()

            last_clap = now

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=1024,
            callback=callback
        ):

            sd.sleep(600000)

    except sd.CallbackStop:

        print("\n👏 Double clap detected!")

        return True

    except Exception as e:

        print("Wake detector error:", e)

        return False