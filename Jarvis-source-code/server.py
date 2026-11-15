from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from jarvis_ai import ask_ai

import speech_recognition as sr
from pydub import AudioSegment

import pyttsx3

import os
import uuid


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI()


# ============================================================
# JARVIS TEXT-TO-SPEECH
# ============================================================

def speak_jarvis(text):

    try:

        print(
            "JARVIS SPEAKING..."
        )

        # Initialize the Windows
        # laptop speaker voice engine

        engine = pyttsx3.init()

        # Speech speed

        engine.setProperty(
            "rate",
            170
        )

        # Volume
        # 1.0 = maximum

        engine.setProperty(
            "volume",
            1.0
        )

        # Speak response

        engine.say(
            str(text)
        )

        # Wait until speaking is complete

        engine.runAndWait()

        # Stop engine

        engine.stop()

        print(
            "JARVIS FINISHED SPEAKING."
        )


    except Exception as e:

        print(
            "TTS Error:",
            e
        )


# ============================================================
# TEXT COMMAND MODEL
# ============================================================

class CommandRequest(BaseModel):

    command: str


# ============================================================
# JARVIS DASHBOARD
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    return """
<!DOCTYPE html>
<html>

<head>

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>JARVIS</title>


<style>


* {

    box-sizing: border-box;

}


body {

    margin: 0;

    min-height: 100vh;

    background: #050505;

    color: #00e5ff;

    font-family: Arial, sans-serif;

    display: flex;

    flex-direction: column;

    align-items: center;

    padding: 30px 15px;

}


.title {

    font-size: 32px;

    letter-spacing: 8px;

    margin-bottom: 30px;

    text-shadow:

        0 0 10px #00e5ff,

        0 0 20px #00e5ff;

}


.core {

    width: 160px;

    height: 160px;

    border-radius: 50%;

    border: 3px solid #00e5ff;

    display: flex;

    align-items: center;

    justify-content: center;

    box-shadow:

        0 0 20px #00e5ff,

        0 0 50px #00e5ff,

        inset 0 0 30px #00e5ff;

    animation: pulse 2s infinite;

}


.core-inner {

    width: 70px;

    height: 70px;

    border-radius: 50%;

    background: #00e5ff;

    box-shadow:

        0 0 20px #00e5ff,

        0 0 40px #00e5ff;

}


@keyframes pulse {

    0% {

        transform: scale(1);

    }

    50% {

        transform: scale(1.08);

    }

    100% {

        transform: scale(1);

    }

}


.status {

    margin-top: 25px;

    font-size: 18px;

    letter-spacing: 3px;

    text-align: center;

}


#chat {

    width: 100%;

    max-width: 600px;

    height: 300px;

    overflow-y: auto;

    margin-top: 25px;

    padding: 15px;

    border: 1px solid #333;

    border-radius: 10px;

    background: #111;

    color: white;

}


.message {

    margin-bottom: 15px;

    line-height: 1.5;

}


.you {

    color: #00e5ff;

}


.jarvis {

    color: #00ff66;

}


.input-area {

    width: 100%;

    max-width: 600px;

    display: flex;

    gap: 10px;

    margin-top: 20px;

}


input {

    flex: 1;

    min-width: 0;

    padding: 15px;

    border-radius: 10px;

    border: 1px solid #333;

    background: #222;

    color: white;

    font-size: 16px;

}


button {

    padding: 15px 20px;

    border-radius: 10px;

    border: none;

    background: #00e5ff;

    color: black;

    font-weight: bold;

    cursor: pointer;

    font-size: 16px;

}


button:active {

    transform: scale(0.95);

}


button:disabled {

    background: #555;

    color: #aaa;

}


.mic-button {

    width: 60px;

    font-size: 22px;

}


.footer {

    margin-top: 20px;

    color: #666;

    font-size: 12px;

    text-align: center;

}


</style>

</head>


<body>


<div class="title">

J.A.R.V.I.S

</div>


<div class="core">

    <div class="core-inner"></div>

</div>


<div
    id="status"
    class="status"
>

SYSTEM ONLINE

</div>


<div id="chat">

    <div class="message jarvis">

        Jarvis:
        System initialized.
        Brain online.

    </div>

</div>


<div class="input-area">


    <input
        id="command"
        type="text"
        placeholder="Ask JARVIS something..."
    >


    <button
        onclick="sendCommand()"
    >

        SEND

    </button>


    <button
        class="mic-button"
        id="micButton"
        onclick="startListening()"
    >

        🎤

    </button>


</div>


<div class="footer">

AI CORE • MEMORY • OBSIDIAN

</div>


<script>


// ============================================================
// SEND TEXT COMMAND
// ============================================================

async function sendCommand() {


    const input =

        document.getElementById(
            "command"
        );


    const command =

        input.value.trim();


    if (!command) {

        return;

    }


    const chat =

        document.getElementById(
            "chat"
        );


    const status =

        document.getElementById(
            "status"
        );


    chat.innerHTML +=

        `<div class="message you">

            You:
            ${command}

        </div>`;


    input.value = "";


    status.innerText =

        "THINKING...";


    try {


        const response =

            await fetch(

                "/ask",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:

                        JSON.stringify({

                            command:
                                command

                        })

                }

            );


        const data =

            await response.json();


        if (data.reply) {


            chat.innerHTML +=

                `<div class="message jarvis">

                    Jarvis:
                    ${data.reply}

                </div>`;

        }


        status.innerText =

            "SYSTEM ONLINE";


        chat.scrollTop =

            chat.scrollHeight;


    }


    catch (error) {


        console.error(
            error
        );


        chat.innerHTML +=

            `<div class="message">

                Error connecting
                to JARVIS.

            </div>`;


        status.innerText =

            "ERROR";


    }

}


// ============================================================
// PHONE MICROPHONE
// ============================================================

async function startListening() {


    const status =

        document.getElementById(
            "status"
        );


    const micButton =

        document.getElementById(
            "micButton"
        );


    const chat =

        document.getElementById(
            "chat"
        );


    try {


        // ====================================================
        // REQUEST MICROPHONE ACCESS
        // ====================================================

        const stream =

            await navigator
                .mediaDevices
                .getUserMedia({

                    audio: true

                });


        status.innerText =

            "LISTENING...";


        micButton.disabled =

            true;


        // ====================================================
        // CREATE AUDIO RECORDER
        // ====================================================

        const recorder =

            new MediaRecorder(
                stream
            );


        const audioChunks = [];


        // ====================================================
        // COLLECT AUDIO DATA
        // ====================================================

        recorder.ondataavailable =

            function(event) {


                if (
                    event.data.size > 0
                ) {


                    audioChunks.push(

                        event.data

                    );


                }

            };


        // ====================================================
        // WHEN RECORDING STOPS
        // ====================================================

        recorder.onstop =

            async function() {


                // =============================================
                // STOP MICROPHONE
                // =============================================

                stream
                    .getTracks()
                    .forEach(

                        function(track) {


                            track.stop();


                        }

                    );


                // =============================================
                // CREATE WEBM AUDIO FILE
                // =============================================

                const audioBlob =

                    new Blob(

                        audioChunks,

                        {

                            type:
                                "audio/webm"

                        }

                    );


                // =============================================
                // CREATE FORM DATA
                // =============================================

                const formData =

                    new FormData();


                formData.append(

                    "audio",

                    audioBlob,

                    "voice.webm"

                );


                status.innerText =

                    "PROCESSING VOICE...";


                try {


                    // =========================================
                    // SEND AUDIO TO PYTHON SERVER
                    // =========================================

                    const response =

                        await fetch(

                            "/voice",

                            {

                                method:
                                    "POST",

                                body:
                                    formData

                            }

                        );


                    const data =

                        await response.json();


                    // =========================================
                    // SERVER ERROR
                    // =========================================

                    if (
                        data.error
                    ) {


                        chat.innerHTML +=

                            `<div class="message">

                                Error:
                                ${data.error}

                            </div>`;


                        status.innerText =

                            "ERROR";


                        micButton.disabled =

                            false;


                        return;

                    }


                    // =========================================
                    // SHOW RECOGNIZED SPEECH
                    // =========================================

                    chat.innerHTML +=

                        `<div class="message you">

                            You:
                            ${data.command}

                        </div>`;


                    // =========================================
                    // SHOW JARVIS RESPONSE
                    // =========================================

                    chat.innerHTML +=

                        `<div class="message jarvis">

                            Jarvis:
                            ${data.reply}

                        </div>`;


                    chat.scrollTop =

                        chat.scrollHeight;


                    status.innerText =

                        "SYSTEM ONLINE";


                }


                catch (error) {


                    console.error(

                        error

                    );


                    chat.innerHTML +=

                        `<div class="message">

                            Error sending
                            voice command.

                        </div>`;


                    status.innerText =

                        "ERROR";


                }


                micButton.disabled =

                    false;


            };


        // ====================================================
        // START RECORDING
        // ====================================================

        recorder.start();


        // ====================================================
        // RECORD FOR 5 SECONDS
        // ====================================================

        setTimeout(

            function() {


                if (

                    recorder.state ===

                    "recording"

                ) {


                    recorder.stop();


                }


            },

            5000

        );


    }


    catch (error) {


        console.error(

            error

        );


        status.innerText =

            "MICROPHONE ERROR";


        alert(

            "Could not access microphone. " +

            "Please allow microphone permission."

        );


        micButton.disabled =

            false;


    }

}


// ============================================================
// ENTER KEY SUPPORT
// ============================================================

document

    .getElementById(
        "command"
    )

    .addEventListener(

        "keypress",

        function(event) {


            if (

                event.key ===

                "Enter"

            ) {


                sendCommand();


            }


        }

    );


</script>


</body>

</html>
"""


# ============================================================
# TEXT COMMAND ENDPOINT
# ============================================================

@app.post("/ask")
def ask_jarvis(
    request: CommandRequest
):

    try:


        print(
            "\n=============================="
        )


        print(
            "TEXT COMMAND RECEIVED"
        )


        print(
            "=============================="
        )


        print(

            "You:",

            request.command

        )


        # ====================================================
        # SEND COMMAND TO JARVIS AI
        # ====================================================

        reply = ask_ai(

            request.command

        )


        print(

            "Jarvis:",

            reply

        )


        # ====================================================
        # JARVIS SPEAKS THROUGH LAPTOP SPEAKER
        # ====================================================

        speak_jarvis(

            reply

        )


        # ====================================================
        # RETURN RESPONSE TO PHONE
        # ====================================================

        return {

            "reply":

                str(reply)

        }


    except Exception as e:


        print(

            "AI Error:",

            e

        )


        return {

            "reply":

                "Sorry, I encountered an error: "

                + str(e)

        }


# ============================================================
# VOICE COMMAND ENDPOINT
# ============================================================

@app.post("/voice")
async def voice_command(

    audio: UploadFile = File(...)

):


    # ========================================================
    # CREATE UNIQUE TEMPORARY FILENAMES
    # ========================================================

    unique_id = str(

        uuid.uuid4()

    )


    webm_filename = (

        f"temp_{unique_id}.webm"

    )


    wav_filename = (

        f"temp_{unique_id}.wav"

    )


    try:


        print(

            "\n=============================="

        )


        print(

            "VOICE COMMAND RECEIVED"

        )


        print(

            "=============================="

        )


        # ====================================================
        # READ AUDIO FROM PHONE
        # ====================================================

        audio_data = await audio.read()


        print(

            "Received audio size:",

            len(audio_data),

            "bytes"

        )


        if not audio_data:


            return {

                "error":

                    "No audio data was received."

            }


        # ====================================================
        # SAVE WEBM FILE
        # ====================================================

        with open(

            webm_filename,

            "wb"

        ) as f:


            f.write(

                audio_data

            )


        print(

            "WebM file saved:",

            webm_filename

        )


        # ====================================================
        # CONVERT WEBM TO WAV
        # ====================================================

        print(

            "Converting WebM to WAV..."

        )


        audio_segment = (

            AudioSegment.from_file(

                webm_filename,

                format="webm"

            )

        )


        print(

            "Original audio:",

            audio_segment.channels,

            "channels,",

            audio_segment.frame_rate,

            "Hz"

        )


        # ====================================================
        # STANDARDIZE AUDIO
        # ====================================================

        audio_segment = (

            audio_segment

            .set_channels(

                1

            )

            .set_frame_rate(

                16000

            )

            .set_sample_width(

                2

            )

        )


        print(

            "Standardized audio:",

            audio_segment.channels,

            "channel,",

            audio_segment.frame_rate,

            "Hz"

        )


        # ====================================================
        # EXPORT PCM WAV
        # ====================================================

        audio_segment.export(

            wav_filename,

            format="wav",

            parameters=[

                "-ac",

                "1",

                "-ar",

                "16000"

            ]

        )


        print(

            "WAV file created:",

            wav_filename

        )


        # ====================================================
        # CHECK WAV FILE
        # ====================================================

        if not os.path.exists(

            wav_filename

        ):


            return {

                "error":

                    "WAV file was not created."

            }


        wav_size = os.path.getsize(

            wav_filename

        )


        print(

            "WAV file size:",

            wav_size,

            "bytes"

        )


        if wav_size < 100:


            return {

                "error":

                    "Generated WAV file is empty or corrupted."

            }


        # ====================================================
        # SPEECH RECOGNITION
        # ====================================================

        print(

            "Starting speech recognition..."

        )


        recognizer = sr.Recognizer()


        with sr.AudioFile(

            wav_filename

        ) as source:


            recorded_audio = (

                recognizer.record(

                    source

                )

            )


        print(

            "Audio loaded successfully."

        )


        # ====================================================
        # CONVERT SPEECH TO TEXT
        # ====================================================

        print(

            "Converting speech to text..."

        )


        command = (

            recognizer.recognize_google(

                recorded_audio

            )

        )


        print(

            "You:",

            command

        )


        # ====================================================
        # SEND COMMAND TO JARVIS AI
        # ====================================================

        print(

            "Sending command to JARVIS AI..."

        )


        reply = ask_ai(

            command

        )


        print(

            "Jarvis:",

            reply

        )


        # ====================================================
        # JARVIS SPEAKS THROUGH LAPTOP SPEAKER
        # ====================================================

        speak_jarvis(

            reply

        )


        # ====================================================
        # SEND RESULT BACK TO PHONE
        # ====================================================

        return {


            "command":

                command,


            "reply":

                str(reply)


        }


    # ========================================================
    # SPEECH NOT UNDERSTOOD
    # ========================================================

    except sr.UnknownValueError:


        print(

            "Speech could not be understood."

        )


        return {


            "error":

                "I could not understand what you said."


        }


    # ========================================================
    # GOOGLE SPEECH RECOGNITION ERROR
    # ========================================================

    except sr.RequestError as e:


        print(

            "Speech recognition service error:",

            e

        )


        return {


            "error":

                "Speech recognition service error: "

                + str(e)


        }


    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:


        print(

            "VOICE PROCESSING ERROR:"

        )


        print(

            type(e).__name__,

            ":",

            str(e)

        )


        return {


            "error":

                "Voice processing error: "

                + str(e)


        }


    # ========================================================
    # DELETE TEMPORARY FILES
    # ========================================================

    finally:


        if os.path.exists(

            webm_filename

        ):


            try:


                os.remove(

                    webm_filename

                )


                print(

                    "Temporary WebM deleted."

                )


            except Exception:


                pass


        if os.path.exists(

            wav_filename

        ):


            try:


                os.remove(

                    wav_filename

                )


                print(

                    "Temporary WAV deleted."

                )


            except Exception:


                pass