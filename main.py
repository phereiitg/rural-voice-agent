"""
Main FastAPI Application
Streaming Voice AI Server with Gemini Multimodal Live API
"""
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

import os
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware


from websocket_handler import MediaStreamHandler
from vector_store import vector_store



# Configure logging — force UTF-8 on all handlers so Hindi text
# doesn't crash on Windows (which defaults to cp1252)
import sys
_file_handler = logging.FileHandler('voice_ai.log', encoding='utf-8')
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _stream_handler]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Streaming Voice AI with Gemini",
    description="Real-time voice assistant for rural India using Gemini Multimodal Live API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Streaming Voice AI Server")
    
    # Load vector databases
    try:
        logger.info("Loading vector databases...")
        vector_store.load_all_databases()
        logger.info("✅ Vector databases loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading vector databases: {e}")
        logger.info("Creating new databases...")
        try:
            vector_store.create_all_databases()
            logger.info("✅ New databases created successfully")
        except Exception as e2:
            logger.error(f"❌ Failed to create databases: {e2}")
    
    logger.info("✅ Server startup complete")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with server info"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Streaming Voice AI Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            h1 { margin-top: 0; }
            .status { 
                display: inline-block;
                padding: 5px 15px;
                background: #10b981;
                border-radius: 20px;
                font-size: 14px;
            }
            .endpoint {
                background: rgba(0, 0, 0, 0.2);
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
            }
            ul { line-height: 1.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Streaming Voice AI Server</h1>
            <div class="status">● ONLINE</div>
            
            <h2>🎯 Features</h2>
            <ul>
                <li>🏥 Hospital Search (गुवाहाटी और आसपास)</li>
                <li>💊 Ayushman Bharat Scheme Info</li>
                <li>📚 NCERT Homework Help (Class 6-12)</li>
                <li>🚨 Emergency Ambulance Calling</li>
            </ul>
            
            <h2>🔌 Endpoints</h2>
            <div class="endpoint">POST /incoming-call - Twilio voice webhook</div>
            <div class="endpoint">WS /media-stream - Twilio media stream</div>
            <div class="endpoint">GET /health - Health check</div>
            <div class="endpoint">POST /test-rag - Test RAG functions</div>
            
            <h2>⚙️ Configuration</h2>
            <p>Powered by:</p>
            <ul>
                <li>Gemini 2.0 Flash (Multimodal Live API)</li>
                <li>Twilio Media Streams</li>
                <li>FAISS Vector Store</li>
                <li>FastAPI + WebSockets</li>
            </ul>
            
            <p style="margin-top: 30px; text-align: center; opacity: 0.8;">
                Built for rural India 🇮🇳 | Latency: &lt;1 second
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not_configured",
            "twilio": "configured" if os.getenv("TWILIO_ACCOUNT_SID") else "not_configured",
            "vector_store": "loaded" if vector_store.hospital_db else "not_loaded"
        }
    }


@app.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Twilio voice webhook - receives incoming calls
    Returns TwiML to connect to media stream
    """
    form_data = await request.form()
    from_number = form_data.get('From')
    to_number = form_data.get('To')
    call_sid = form_data.get('CallSid')
    
    logger.info(f"📞 Incoming call: {call_sid}")
    logger.info(f"From: {from_number} → To: {to_number}")
    
    # Get server URL from environment or request
    server_url = os.getenv("SERVER_URL")
    if not server_url:
        # Try to construct from request
        server_url = f"{request.url.scheme}://{request.url.netloc}"
    stream_url = server_url.replace("https://", "wss://").replace("http://", "ws://")
    
    # TwiML response to connect to media stream
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN" voice="woman">
        नमस्ते! मैं आपकी सहायक हूं। मैं अस्पताल की जानकारी, आयुष्मान योजना, और होमवर्क में मदद कर सकती हूं। कृपया अपना सवाल पूछें।
    </Say>
    <Connect>
        <Stream url="{stream_url}/media-stream">
            <Parameter name="From" value="{from_number}" />
            <Parameter name="To" value="{to_number}" />
            <Parameter name="CallSid" value="{call_sid}" />
        </Stream>
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream_endpoint(websocket: WebSocket):
    """
    Twilio Media Stream WebSocket endpoint
    This is where the real-time audio streaming happens
    """
    logger.info("New WebSocket connection request")
    
    handler = MediaStreamHandler()
    await handler.handle_stream(websocket)


@app.post("/ambulance-briefing")
async def ambulance_briefing(
    name: str = "अज्ञात",
    location: str = "",
    emergency: str = "",
    phone: str = "",
    condition: str = ""
):
    """
    TwiML endpoint — called by Exotel when the ambulance/demo call is answered.
    Speaks the patient briefing aloud so the recipient immediately knows:
      - Who needs help (name)
      - Where they are (location)
      - What happened (emergency type)
      - Their phone number (auto-captured from Twilio, not asked from user)
      - Any extra condition details

    Example spoken output (Hindi):
      "सावधान! आपातकालीन कॉल।
       मरीज का नाम: अमित।
       स्थान: एम.जी. रोड।
       आपातकाल: दुर्घटना।
       कॉलर का नंबर है: +91 99 XXXX XXXX।
       कृपया तुरंत सहायता भेजें।"
    """
    import html as html_lib  # XML/HTML escaping

    # Escape all user-provided values so they're safe inside XML <Say> tags.
    # Without this, special chars (em dash, &, <, >) break the TwiML and
    # Twilio returns "Application Error" when the call is answered.
    def xs(text: str) -> str:
        """XML-safe escape"""
        return html_lib.escape(str(text), quote=False)
    
    # Add this helper function inside ambulance_briefing, after the xs() function:
    def speak_phone(number: str) -> str:
        """Convert +919235527628 → 9 2 3 5 5 2 7 6 2 8 (spaced digits, no country code)"""
        digits = ''.join(c for c in number if c.isdigit())
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]  # strip India country code
        return ' '.join(digits)  # space between each digit so TTS reads them one by one

    condition_part = f"मरीज की स्थिति: {xs(condition)}. " if condition else ""

    # Build two <Say> blocks — one full briefing, one short repeat
    first_say = (
        f"सावधान! आपातकालीन कॉल. "
        f"मरीज का नाम: {xs(name)}. "
        f"स्थान: {xs(location)}. "
        f"आपातकाल: {xs(emergency)}. "
        f"{condition_part}"
        f"कॉलर का नंबर है: {speak_phone(phone)}. "
        f"कृपया तुरंत सहायता भेजें."
    )

    repeat_say = (
        f"दोबारा सुनें. "
        f"मरीज का नाम: {xs(name)}. "
        f"स्थान: {xs(location)}. "
        f"कॉलर नंबर: {speak_phone(phone)}."
    )

    logger.info(
        f"Ambulance briefing served | name={name} | location={location} "
        f"| emergency={emergency} | phone={phone}"
    )

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN" voice="Polly.Aditi">{first_say}</Say>
    <Pause length="2"/>
    <Say language="hi-IN" voice="Polly.Aditi">{repeat_say}</Say>
    <Pause length="1"/>
    <Say language="hi-IN" voice="Polly.Aditi">यह कॉल समाप्त होती है. धन्यवाद.</Say>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@app.post("/call-status")
async def call_status_callback(request: Request):
    """
    Callback for call status updates from Exotel
    Used for ambulance call tracking
    """
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    call_status = form_data.get('CallStatus')
    
    logger.info(f"📞 Call status update: {call_sid} - {call_status}")
    
    return {"status": "received"}


@app.post("/test-rag")
async def test_rag(request: Request):
    """
    Test endpoint for RAG functions
    Useful for debugging without making actual phone calls
    """
    from rag_tools import rag_tools
    
    data = await request.json()
    function_name = data.get('function')
    args = data.get('args', {})
    
    result = None
    
    if function_name == "search_hospitals":
        result = await rag_tools.search_hospitals(
            location=args.get('location', 'गुवाहाटी'),
            hospital_type=args.get('hospital_type')
        )
    elif function_name == "get_scheme_info":
        result = await rag_tools.get_scheme_info(
            query=args.get('query', 'आयुष्मान भारत क्या है?')
        )
    elif function_name == "get_homework_help":
        result = await rag_tools.get_homework_help(
            subject=args.get('subject'),
            class_number=args.get('class_number'),
            question=args.get('question', 'गुरुत्वाकर्षण क्या है?')
        )
    else:
        return {"error": "Unknown function"}
    
    return result


@app.get("/stats")
async def get_stats():
    """
    Get server statistics
    """
    # Count emergency logs
    emergency_log_dir = Path("./data/emergency_logs")
    emergency_count = 0
    if emergency_log_dir.exists():
        emergency_count = len(list(emergency_log_dir.glob("*.log")))
    
    return {
        "server": "Streaming Voice AI",
        "uptime": "running",
        "emergency_logs": emergency_count,
        "vector_databases": {
            "hospitals": "loaded" if vector_store.hospital_db else "not_loaded",
            "schemes": "loaded" if vector_store.scheme_db else "not_loaded",
            "ncert": "loaded" if vector_store.ncert_db else "not_loaded"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting server on port {port}")
    logger.info("📝 Make sure to:")
    logger.info("   1. Set GEMINI_API_KEY in .env")
    logger.info("   2. Set Twilio credentials in .env")
    logger.info("   3. Run ngrok: ngrok http 8000")
    logger.info("   4. Update Twilio webhook to your ngrok URL")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        #reload_excludes=["*.log"],
        log_level="info"
    )