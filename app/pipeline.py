from pipecat.pipeline.pipeline import Pipeline
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from app.services.stt import get_stt
from app.services.llm import get_llm
from app.services.tts import get_tts
from app.processors.memory_processor import MemoryProcessor
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
# from pipecat.transports.network.web_rtc import SmallWebRTCTransport, SmallWebRTCTransportParams
from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
from pipecat.transports.daily.transport import DailyTransport, DailyParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from app.config.settings import settings

# ✅ Correct audio config (your DMIC16kHz)
# transport = LocalAudioTransport(
#     LocalAudioTransportParams(
#         input_device_index=11,     # 🎤 DMIC16kHz
#         output_device_index=0,    # 🔊 speaker
#         sample_rate=16000,
#         frames_per_buffer=1024
#     )
# )

async def create_pipeline(room_url: str, token: str):
    # Initialize your services
    stt = get_stt()
    llm = get_llm()
    tts = get_tts()

    # Pass the dynamic URL and token to DailyTransport
    transport = DailyTransport(
        room_url,
        token,
        "Myntra Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=True,
        ),
    )
    # transport = LiveKitTransport(
    #     room_name=room_name,
    #     url=settings.LIVEKIT_URL,
    #     token=settings.LIVEKIT_TOKEN,
    #     params=LiveKitParams(
    #         audio_out_enabled=True,
    #         audio_in_enabled=True,
    #         vad_analyzer=SileroVADAnalyzer(), # Add this to detect your voice
    #         vad_enabled=True
    #     )
    # )
    # messages = [
    #     {
    #         "role": "system",
    #         "content": (
    #             "आप Myntra के एक मिलनसार, मददगार और सहानुभूति रखने वाले कस्टमर सपोर्ट वॉयस एजेंट हैं। "
    #             "आप उपयोगकर्ताओं को ऑर्डर ट्रैकिंग, रिटर्न और एक्सचेंज पॉलिसी, रिफंड की स्थिति और साइजिंग से जुड़ी समस्याओं में मदद करते हैं। "
    #             "अपनी प्रतिक्रियाएं संक्षिप्त और संवादात्मक (conversational) रखें। "
    #             "उपयोगकर्ता से हिंदी में बात करें।"
    #         )
    #     }
    # ]
    messages = [
        {
            "role": "system",
            "content": (
                "તમે Myntra માટે મૈત્રીપૂર્ણ, મદદરૂપ અને સહાનુભૂતિ ધરાવતા કસ્ટમર સપોર્ટ વોઇસ એજન્ટ છો. "
                "તમે ઓર્ડર ટ્રેકિંગ, રિટર્ન અને એક્સચેન્જ પોલિસી, રિફંડ સ્ટેટસ અને સાઇઝિંગની સમસ્યાઓમાં વપરાશકર્તાઓને મદદ કરો છો. "
                "તમારા પ્રતિભાવો ટૂંકા અને વાતચીત જેવા (conversational) રાખો. "
                "વપરાશકર્તા સાથે ગુજરાતીમાં વાત કરો."
            )
        }
    ]
    context = OpenAILLMContext(messages=messages)
    context_aggregator = llm.create_context_aggregator(context)
    return Pipeline([
        transport.input(),
        get_stt(),
        context_aggregator.user(),
        get_llm(),
        get_tts(),
        transport.output(),
        context_aggregator.assistant(),
    ])