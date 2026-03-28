import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

settings = Settings()