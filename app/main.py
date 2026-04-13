import time
import aiohttp
import logging

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from twilio.rest import Client

from app.pipeline import create_pipeline
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


async def create_daily_room() -> tuple[str, str, str]:
    """
    Create a Daily room with SIP dial-in enabled.

    The correct Daily API format is a nested "sip" object under "properties".
    "sip_mode" and "enable_dialin" are NOT valid top-level room properties.

    Returns: (room_url, room_name, sip_uri)
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {settings.DAILY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "properties": {
                "exp": int(time.time()) + 3600,
                # Correct: SIP is enabled via a nested "sip" object
                "sip": {
                    "display_name": "myntra-bot",
                    "sip_mode": "dial-in",
                    "num_endpoints": 1,
                    "video": False,
                },
            }
        }
        async with session.post(
            "https://api.daily.co/v1/rooms", headers=headers, json=payload
        ) as res:
            data = await res.json()
            logger.info("Daily room created: %s", data)

            if "url" not in data:
                raise RuntimeError(f"Failed to create Daily room: {data}")

            # Daily returns the real SIP URI in config.sip_uri when sip is set.
            # Extract it, with a safe fallback to the legacy format.
            # Daily returns the endpoint WITHOUT the "sip:" scheme prefix
            raw_endpoint = data.get("config", {}).get("sip_uri", {}).get("endpoint")
            if raw_endpoint:
                # Add sip: prefix if not already present
                sip_uri = raw_endpoint if raw_endpoint.startswith("sip:") else f"sip:{raw_endpoint}"
            else:
                # Fallback (should not happen if sip property was set correctly)
                sip_uri = f"sip:{data['name']}@sip.daily.co"
                logger.warning("sip_uri.endpoint not found in Daily response, using fallback: %s", sip_uri)
            logger.info("SIP URI: %s", sip_uri)

            return data["url"], data["name"], sip_uri


async def create_daily_token(room_name: str) -> str:
    """
    Mint an owner meeting token for the bot.
    Owner tokens bypass room security so the bot can always join.
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {settings.DAILY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "properties": {
                "room_name": room_name,
                "is_owner": True,
                "exp": int(time.time()) + 3600,
            }
        }
        async with session.post(
            "https://api.daily.co/v1/meeting-tokens",
            headers=headers,
            json=payload,
        ) as res:
            data = await res.json()
            logger.info("Daily token created for room: %s", room_name)

            if "token" not in data:
                raise RuntimeError(f"Failed to create Daily token: {data}")

            return data["token"]


async def run_bot(room_url: str, token: str):
    """Background task: run the Pipecat pipeline for this call."""
    try:
        logger.info("Starting bot for room: %s", room_url)
        pipeline = await create_pipeline(room_url, token)
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        await runner.run(task)
        logger.info("Bot finished for room: %s", room_url)
    except Exception:
        logger.exception("Bot crashed for room: %s", room_url)


@app.post("/incoming-call")
async def handle_incoming_call(request: Request, background_tasks: BackgroundTasks):
    """
    Twilio webhook for inbound calls.
    Flow: Twilio -> Daily SIP URI -> Pipecat bot.
    """
    # 1. Create a SIP-enabled Daily room, get real sip_uri back
    room_url, room_name, sip_uri = await create_daily_room()

    # 2. Mint a real owner token for the bot
    token = await create_daily_token(room_name)

    # 3. Start the Pipecat bot in the background
    background_tasks.add_task(run_bot, room_url, token)

    # 4. Tell Twilio to SIP-dial into the Daily room using the real sip_uri
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>
        <Sip>{sip_uri}</Sip>
    </Dial>
</Response>"""
    return PlainTextResponse(content=twiml, media_type="application/xml")


@app.post("/call-out")
async def handle_call_out(to_number: str, background_tasks: BackgroundTasks):
    """
    Trigger an outbound call to `to_number`.
    Flow: Bot joins Daily room -> Twilio dials user -> bridges user into room via SIP.
    """
    # 1. Create a SIP-enabled Daily room
    room_url, room_name, sip_uri = await create_daily_room()

    # 2. Mint a real owner token for the bot
    token = await create_daily_token(room_name)

    # 3. Start the Pipecat bot
    background_tasks.add_task(run_bot, room_url, token)

    # 4. Use Twilio to dial the user and bridge them into Daily via the real sip_uri
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    twiml = f"<Response><Dial><Sip>{sip_uri}</Sip></Dial></Response>"
    call = client.calls.create(
        to=to_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        twiml=twiml,
    )
    logger.info(
        "Outbound call initiated: %s -> %s (SID: %s)",
        settings.TWILIO_PHONE_NUMBER, to_number, call.sid,
    )
    return {"message": "Call initiated", "call_sid": call.sid, "room_url": room_url}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)