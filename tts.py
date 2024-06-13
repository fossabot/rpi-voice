import os
import httpx
import logging
from dotenv import load_dotenv
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import asyncio
import time

# Configuration and setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextToSpeech:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.voice_name = os.getenv("TTS_VOICE_NAME", "alloy")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = "2024-02-15-preview"
        self.tts_model = os.getenv("TTS_MODEL_NAME", "tts-1-hd")
        self.headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        self.timeout = httpx.Timeout(10.0, connect=60.0)
        self.max_retries = 3   # Define the maximum number of retries
        self.retry_delay = 5   # Delay between retries in seconds

    def construct_request_url(self):
        url = f"{self.endpoint}/openai/deployments/{self.tts_model}/audio/speech?api-version={self.api_version}"
        return url

    async def synthesize_speech(self, text):
        data = {"model": self.tts_model, "input": text, "voice": self.voice_name}
        retries = 0
        while retries < self.max_retries:
            try:
                async with httpx.AsyncClient(http2=True, timeout=self.timeout) as client:
                    response = await client.post(self.construct_request_url(), headers=self.headers, json=data)
                    response.raise_for_status()
                    logging.info("Speech synthesis request successful.")
                    return BytesIO(response.content)
            except httpx.ReadTimeout as e:
                retries += 1
                logging.warning(f"Read timeout occurred, retry {retries}/{self.max_retries}")
                time.sleep(self.retry_delay)
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP Status Error occurred: {e}", exc_info=True)
                break
            except httpx.RequestError as e:
                logging.error(f"HTTP Request Error: {e}", exc_info=True)
                break
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}", exc_info=True)
                break
        logging.error("Failed to synthesize speech after retries.")
        return None

    def play_speech(self, audio_stream):
        try:
            if audio_stream:
                sound = AudioSegment.from_file(audio_stream, format="mp3")
                logging.info("Playback started.")
                play(sound)
            else:
                logging.error("Failed to play speech: No audio stream.")
        except Exception as e:
            logging.error(f"Error while playing audio: {e}", exc_info=True)

# Usage
async def main():
    tts = TextToSpeech()
    text_to_synthesize = "Today is a wonderful day to build something people love!"
    audio_stream = await tts.synthesize_speech(text_to_synthesize)
    if audio_stream:
        tts.play_speech(audio_stream)

if __name__ == "__main__":
    asyncio.run(main())
