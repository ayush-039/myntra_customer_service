import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
    LIVEKIT_URL=os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY=os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET=os.getenv("LIVEKIT_API_SECRET")
    LIVEKIT_TOKEN=os.getenv("LIVEKIT_TOKEN")

settings = Settings()