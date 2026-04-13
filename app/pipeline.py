from pipecat.pipeline.pipeline import Pipeline
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transports.daily.transport import DailyTransport, DailyParams
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

from app.services.stt import get_stt
from app.services.llm import get_llm
from app.services.tts import get_tts
from app.config.settings import settings


async def create_pipeline(room_url: str, token: str):
    # ✅ Instantiate each service ONCE
    stt = get_stt()
    llm = get_llm()
    tts = get_tts()

    # ✅ DailyParams: disable built-in transcription since we use Sarvam STT
    #    Enable VAD so Pipecat knows when the user stops speaking
    transport = DailyTransport(
        room_url,
        token,
        "Myntra Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=False,        # ← off: we handle STT ourselves
            vad_enabled=True,                   # ← on: needed for turn detection
            vad_analyzer=SileroVADAnalyzer(),   # ← silero works well with 16 kHz
        ),
    )

    # messages = [
    #     {
    #         "role": "system",
    #         "content": (
    #             "તમે Myntra માટે મૈત્રીપૂર્ણ, મદદરૂપ અને સહાનુભૂતિ ધરાવતા કસ્ટમર સપોર્ટ વોઇસ એજન્ટ છો. "
    #             "તમે ઓર્ડર ટ્રેકિંગ, રિટર્ન અને એક્સચેન્જ પોલિસી, રિફંડ સ્ટેટસ અને સાઇઝિંગની સમસ્યાઓમાં વપરાશકર્તાઓને મદદ કરો છો. "
    #             "તમારા પ્રતિભાવો ટૂંકા અને વાતચીત જેવા (conversational) રાખો. "
    #             "વપરાશકર્તા સાથે ગુજરાતીમાં વાત કરો."
    #         ),
    #     }
    # ]

    messages = [
    {
        "role": "system",
        "content": (
            "You are a friendly, helpful, and empathetic customer support voice agent for Myntra. "
            "You help users with order tracking, return and exchange policies, refund status, and sizing issues. "
            "Keep your responses short and conversational. "
            "Speak with the user in english."
        ),
    }
]
    # ✅ Build context and aggregator using the SAME llm instance
    context = OpenAILLMContext(messages=messages)
    context_aggregator = llm.create_context_aggregator(context)

    # ✅ Pipeline uses the same stt / llm / tts variables — no duplicate instantiation
    pipeline = Pipeline(
        [
            transport.input(),
            stt,                               # Sarvam STT → TranscriptionFrame
            context_aggregator.user(),         # Attach user turn to context
            llm,                               # OpenAI LLM → LLMResponseFrame
            tts,                               # Sarvam TTS → AudioFrame
            transport.output(),                # Send audio to Daily room
            context_aggregator.assistant(),    # Attach assistant turn to context
        ]
    )

    return pipeline