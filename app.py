"""
+-------------------+        +-----------------------+        +------------------+        +------------------------+
|   Step 1: Install |        |  Step 2: Real-Time    |        |  Step 3: Pass    |        |  Step 4: Live Audio    |
|   Python Libraries|        |  Transcription with   |        |  Real-Time       |        |  Stream from ElevenLabs|
+-------------------+        |       AssemblyAI      |        |  Transcript to   |        |                        |
|                   |        +-----------------------+        |      OpenAI      |        +------------------------+
| - assemblyai      |                    |                    +------------------+                    |
| - openai          |                    |                             |                              |
| - elevenlabs      |                    v                             v                              v
| - mpv             |        +-----------------------+        +------------------+        +------------------------+
| - portaudio       |        |                       |        |                  |        |                        |
+-------------------+        |  AssemblyAI performs  |-------->  OpenAI generates|-------->  ElevenLabs streams   |
                             |  real-time speech-to- |        |  response based  |        |  response as live      |
                             |  text transcription   |        |  on transcription|        |  audio to the user     |
                             |                       |        |                  |        |                        |
                             +-----------------------+        +------------------+        +------------------------+

###### Step 1: Install Python libraries ######

brew install portaudio
pip install "assemblyai[extras]"
pip install elevenlabs==0.3.0b0
brew install mpv
pip install --upgrade openai
"""

import os
from dotenv import load_dotenv
import assemblyai as aai
from elevenlabs import generate, stream, voices
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")


class AI_Assistant:
    def __init__(self):

        aai.settings.api_key = assemblyai_api_key
        self.openai_client = openai_api_key
        self.elevenlabs_api_key = elevenlabs_api_key

        self.transcriber = None

        # Prompt
        self.full_transcript = [
            {
                "role": "system",
                "content": "You are a receptionist at a restaurant. Be resourceful and efficient.",
            },
        ]

    ###### Step 2: Real-Time Transcription with AssemblyAI ######

    def start_transcription(self):
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
            end_utterance_silence_threshold=1000,
        )

        self.transcriber.connect()
        microphone_stream = aai.extras.MicrophoneStream(sample_rate=16000)
        self.transcriber.stream(microphone_stream)

    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        print("Session ID:", session_opened.session_id)
        return

    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.generate_ai_response(transcript)
        else:
            print(transcript.text, end="\r")

    def on_error(self, error: aai.RealtimeError):
        print("An error occurred:", error)
        return

    def on_close(self):
        # print("Closing Session")
        return

    ###### Step 3: Pass real-time transcript to OpenAI ######

    def generate_ai_response(self, transcript):

        self.stop_transcription()

        self.full_transcript.append({"role": "user", "content": transcript.text})
        print(f"\nPatient: {transcript.text}", end="\r\n")

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=self.full_transcript
        )

        ai_response = response.choices[0].message.content

        self.generate_audio(ai_response)

        self.start_transcription()
        print(f"\nReal-time transcription: ", end="\r\n")

    ###### Step 4: Generate audio with ElevenLabs ######

    def generate_audio(self, text):

        self.full_transcript.append({"role": "assistant", "content": text})
        print(f"\nAI Receptionist: {text}")

        try:
            audio_stream = generate(
                api_key=self.elevenlabs_api_key,
                text=text,
                voice="Xb7hH8MSUJpSbSDYk0k2",
                stream=True,
            )
        except ValueError as e:
            print(e)
            # List available voices and choose a valid one
            available_voices = voices(api_key=self.elevenlabs_api_key)
            print("Available voices:", available_voices)
            # Use a fallback voice
            fallback_voice = available_voices[0] if available_voices else "DefaultVoice"
            audio_stream = generate(
                api_key=self.elevenlabs_api_key,
                text=text,
                voice=fallback_voice,
                stream=True,
            )

        # stream(audio_stream)

        # Use full path to mpv.exe
        mpv_path = r"C:\Program Files\mpv\mpv.exe"
        os.system(f'"{mpv_path}" {audio_stream}')


greeting = "Thank you for choosing our restaurant. I am Rachel, how can I help you with your order today?"
ai_assistant = AI_Assistant()
ai_assistant.generate_audio(greeting)
ai_assistant.start_transcription()
