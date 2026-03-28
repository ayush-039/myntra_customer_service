from pipecat.pipeline.pipeline import Pipeline

from app.services.stt import get_stt
from app.services.llm import get_llm
from app.services.tts import get_tts
from pipecat.audio.vad.vad_analyzer import VADAnalyzer
from pipecat.transports.local.audio import LocalAudioTransport

transport = LocalAudioTransport(
    vad_analyzer=VADAnalyzer()
)

def create_pipeline():
    return Pipeline([
        transport.input(),   # 🎤 Mic input (FIX)
        get_stt(),
        get_llm(),
        get_tts(),
        transport.output()  # 🔊 Speaker output
    ])