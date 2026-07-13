from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import logging
from .ai_agent import get_ai_response
from .auth import get_current_user

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

@router.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """Handle incoming call - simple greeting and conversation"""
    form_data = await request.form()
    speech_result = form_data.get('SpeechResult', '')
    digits = form_data.get('Digits', '')
    user_input = speech_result or digits

    response = VoiceResponse()
    base_url = os.getenv("BASE_URL", "https://your-ngrok-url.ngrok.io")
    absolute_action_url = f"{base_url}/api/voice/incoming"
    tone = "friendly"  # default tone

    if not user_input:
        # First time - greeting
        greeting = "Hey! Thanks for calling. I'm your AI assistant. How can I help you today? Just speak or press any key."
        response.say(greeting, voice='Polly.Joanna')
        response.gather(
            input='speech dtmf',
            action=absolute_action_url,
            method='POST',
            timeout=5,
            num_digits=1,
            speech_timeout='auto'
        )
    else:
        # User responded - process with AI
        try:
            logger.info(f"User input: {user_input}")
            ai_reply = await get_ai_response(user_input, tone)
            logger.info(f"AI reply: {ai_reply}")
            response.say(ai_reply, voice='Polly.Joanna')
            # Continue conversation
            response.gather(
                input='speech dtmf',
                action=absolute_action_url,
                method='POST',
                timeout=5,
                num_digits=1,
                speech_timeout='auto'
            )
        except Exception as e:
            logger.error(f"AI error: {e}")
            response.say("I'm having trouble understanding. Could you please repeat?", voice='Polly.Joanna')
            response.gather(
                input='speech dtmf',
                action=absolute_action_url,
                method='POST',
                timeout=5
            )

    return Response(content=str(response), media_type="application/xml")

@router.post("/make-call")
async def make_call_endpoint(
    phone_number: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Make outgoing call from dashboard"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    base_url = os.getenv("BASE_URL")
    if not base_url:
        raise HTTPException(status_code=500, detail="BASE_URL not set in .env")
    
    call = twilio_client.calls.create(
        url=f"{base_url}/api/voice/incoming",
        to=phone_number,
        from_=os.getenv("TWILIO_PHONE_NUMBER")
    )
    return {"status": "calling", "call_sid": call.sid}