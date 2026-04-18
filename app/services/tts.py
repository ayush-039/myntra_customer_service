from pipecat.services.sarvam.tts import SarvamTTSService
from app.config.settings import settings

def get_tts():
    return SarvamTTSService(
        api_key=settings.SARVAM_API_KEY,
        target_language_code="eng-IN",
        model="bulbul:v3",
        speaker="aditya"  # Clear and articulate voice for teaching
    )

