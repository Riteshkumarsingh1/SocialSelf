from fastapi import APIRouter, Request, Response, Form
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from .ai_agent import get_ai_response, get_user_tone
from .database import get_db

router = APIRouter()

twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

@router.post("/whatsapp/incoming")
async def handle_whatsapp_message(request: Request):
    """Handle incoming WhatsApp messages"""
    form_data = await request.form()
    incoming_msg = form_data.get('Body', '')
    sender = form_data.get('From', '').replace('whatsapp:', '')
    
    # For demo, use default user_id 1
    # In production, you'd map phone numbers to user accounts
    tone = "friendly"
    
    ai_reply = await get_ai_response(incoming_msg, tone)
    
    # Log conversation
    conn = await get_db()
    await conn.execute(
        "INSERT INTO conversation_logs (user_id, platform, message, ai_reply, tone_used) VALUES ($1, $2, $3, $4, $5)",
        1, "whatsapp", incoming_msg, ai_reply, tone
    )
    await conn.close()
    
    response = MessagingResponse()
    response.message(ai_reply)
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/whatsapp/send")
async def send_whatsapp_message(to: str = Form(...), message: str = Form(...)):
    """Send a WhatsApp message"""
    twilio_client.messages.create(
        body=message,
        from_=f'whatsapp:{os.getenv("TWILIO_WHATSAPP_NUMBER")}',
        to=f'whatsapp:{to}'
    )
    return {"status": "sent"}
