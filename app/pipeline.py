# from pipecat.pipeline.pipeline import Pipeline
# from pipecat.audio.vad.silero import SileroVADAnalyzer
# from pipecat.transports.daily.transport import DailyTransport, DailyParams
# from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

# from app.services.stt import get_stt
# from app.services.llm import get_llm
# from app.services.tts import get_tts
# from app.config.settings import settings


# async def create_pipeline(room_url: str, token: str):
#     # ✅ Instantiate each service ONCE
#     stt = get_stt()
#     llm = get_llm()
#     tts = get_tts()

#     # ✅ DailyParams: disable built-in transcription since we use Sarvam STT
#     #    Enable VAD so Pipecat knows when the user stops speaking
#     transport = DailyTransport(
#         room_url,
#         token,
#         "Myntra Bot",
#         DailyParams(
#             audio_in_enabled=True,
#             audio_out_enabled=True,
#             transcription_enabled=False,        # ← off: we handle STT ourselves
#             vad_enabled=True,                   # ← on: needed for turn detection
#             vad_analyzer=SileroVADAnalyzer(),   # ← silero works well with 16 kHz
#         ),
#     )

#     # messages = [
#     #     {
#     #         "role": "system",
#     #         "content": (
#     #             "તમે Myntra માટે મૈત્રીપૂર્ણ, મદદરૂપ અને સહાનુભૂતિ ધરાવતા કસ્ટમર સપોર્ટ વોઇસ એજન્ટ છો. "
#     #             "તમે ઓર્ડર ટ્રેકિંગ, રિટર્ન અને એક્સચેન્જ પોલિસી, રિફંડ સ્ટેટસ અને સાઇઝિંગની સમસ્યાઓમાં વપરાશકર્તાઓને મદદ કરો છો. "
#     #             "તમારા પ્રતિભાવો ટૂંકા અને વાતચીત જેવા (conversational) રાખો. "
#     #             "વપરાશકર્તા સાથે ગુજરાતીમાં વાત કરો."
#     #         ),
#     #     }
#     # ]

#     messages = [
#     {
#         "role": "system",
#         "content": (
#             "You are a friendly, helpful, and empathetic customer support voice agent for Myntra. "
#             "You help users with order tracking, return and exchange policies, refund status, and sizing issues. "
#             "Keep your responses short and conversational. "
#             "Speak with the user in english."
#         ),
#     }
# ]
#     # ✅ Build context and aggregator using the SAME llm instance
#     context = OpenAILLMContext(messages=messages)
#     context_aggregator = llm.create_context_aggregator(context)

#     # ✅ Pipeline uses the same stt / llm / tts variables — no duplicate instantiation
#     pipeline = Pipeline(
#         [
#             transport.input(),
#             stt,                               # Sarvam STT → TranscriptionFrame
#             context_aggregator.user(),         # Attach user turn to context
#             llm,                               # OpenAI LLM → LLMResponseFrame
#             tts,                               # Sarvam TTS → AudioFrame
#             transport.output(),                # Send audio to Daily room
#             context_aggregator.assistant(),    # Attach assistant turn to context
#         ]
#     )

#     return pipeline


import asyncio
import logging

from pipecat.pipeline.pipeline import Pipeline
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transports.daily.transport import DailyTransport, DailyParams
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.pipeline.task import PipelineTask

from app.services.stt import get_stt
from app.services.llm import get_llm
from app.services.tts import get_tts

logger = logging.getLogger(__name__)

# How long (seconds) to wait for the callee to pick up before hanging up
NO_ANSWER_TIMEOUT = 30


async def create_pipeline(room_url: str, token: str):
    stt = get_stt()
    llm = get_llm()
    tts = get_tts()

    transport = DailyTransport(
        room_url,
        token,
        "Myntra Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
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
    context = OpenAILLMContext(messages=messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # ---------- event callbacks ----------

    task_holder = {}  # will be set by run_bot after task is created

    @transport.event_handler("on_participant_joined")
    async def on_participant_joined(transport, participant):
        participant_id = participant.get("id", "")
        # Ignore the bot's own join event
        if participant_id == transport.participant_id:
            return
        logger.info("Human participant joined: %s — cancelling no-answer timer", participant_id)
        # Cancel the no-answer timeout now that someone picked up
        timer = task_holder.get("no_answer_timer")
        if timer and not timer.done():
            timer.cancel()

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        participant_id = participant.get("id", "")
        logger.info("Participant left: %s (reason: %s) — ending pipeline", participant_id, reason)
        task = task_holder.get("pipeline_task")
        if task:
            await task.cancel()

    @transport.event_handler("on_call_state_updated")
    async def on_call_state_updated(transport, state):
        logger.info("Call state updated: %s", state)
        if state == "left":
            task = task_holder.get("pipeline_task")
            if task:
                await task.cancel()

    return pipeline, transport, task_holder

# curl -k -X POST "https://unappended-margot-nondigestible.ngrok-free.dev/call-out?to_number=+919909764364"