import asyncio
import aiohttp
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from twilio.rest import Client

from app.pipeline import create_pipeline
from app.config.settings import settings

app = FastAPI()

async def create_daily_room():
    """Helper to create a Daily room via API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {settings.DAILY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"properties": {"exp": 3600}} # Room expires in 1 hour
        async with session.post("https://api.daily.co/v1/rooms", headers=headers, json=payload) as res:
            data = await res.json()
            print("data:", data)
            return data["url"], data["name"]

async def run_bot(room_url: str, token: str):
    """Background task to run the Pipecat bot"""
    pipeline = await create_pipeline(room_url, token)
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    await runner.run(task)

@app.post("/incoming-call")
async def handle_incoming_call(request: Request, background_tasks: BackgroundTasks):
    """Twilio Webhook for Call-In"""
    # 1. Create a Daily room for the call
    room_url, room_name = await create_daily_room()
    
    # 2. Start the Pipecat bot in the background
    # Note: In production, generate a real token using the Daily API. Passing an empty string works for public rooms.
    background_tasks.add_task(run_bot, room_url, "") 
    
    # 3. Instruct Twilio to connect to the Daily SIP URI using TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Dial>
                <Sip>sip:{room_name}@sip.daily.co</Sip>
            </Dial>
        </Response>"""
    return PlainTextResponse(content=twiml, media_type="application/xml")

@app.post("/call-out")
async def handle_call_out(to_number: str, background_tasks: BackgroundTasks):
    """Endpoint to trigger an outbound call"""
    # 1. Create a Daily room
    room_url, room_name = await create_daily_room()
    
    # 2. Start the Pipecat bot
    background_tasks.add_task(run_bot, room_url, "")
    
    # 3. Use Twilio to dial the user and bridge them to Daily
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to=to_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        twiml=f'<Response><Dial><Sip>sip:{room_name}@sip.daily.co</Sip></Dial></Response>'
    )
    return {"message": "Call initiated", "call_sid": call.sid}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)