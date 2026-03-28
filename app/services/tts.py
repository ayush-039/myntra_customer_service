from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from app.config.settings import settings

def get_tts():
    return ElevenLabsTTSService(
        api_key=settings.ELEVENLABS_API_KEY,
        # Pipecat expects ElevenLabs voice *IDs* (Settings.voice).
        # Passing `voice=` is ignored by current Pipecat versions, leaving voice_id=None.
        settings=ElevenLabsTTSService.Settings(
            voice="21m00Tcm4TlvDq8ikWAM"  # ✅ REAL Rachel voice ID
        )
    )