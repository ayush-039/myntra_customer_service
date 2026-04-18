from pipecat.services.sarvam.stt import SarvamSTTService
from app.config.settings import settings

def get_stt():
    return SarvamSTTService(
        api_key=settings.SARVAM_API_KEY,
        language="eng-IN",  # Auto-detect for multilingual students
        model="saaras:v3",
        mode="transcribe"
    )