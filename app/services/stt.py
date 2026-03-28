from pipecat.services.deepgram.stt import DeepgramSTTService
from app.config.settings import settings

def get_stt():
    return DeepgramSTTService(
        api_key=settings.DEEPGRAM_API_KEY
    )