# 🚀 Streaming Voice AI with Gemini Multimodal Live API

**Real-time voice assistant for rural India with <1 second latency**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Features

- 🏥 **Hospital Search** - Find nearby hospitals in Guwahati and surrounding areas
- 💊 **Ayushman Bharat Info** - Get scheme details, eligibility, and card application info
- 📚 **Homework Help** - NCERT-based assistance for Class 6-12 students
- 🚨 **Emergency Response** - Automatic ambulance calling with location tracking
- 📱 **SMS Summaries** - Post-call SMS with important information
- 🇮🇳 **Hindi Language** - Full support for Hindi conversations

## 🏗️ Architecture

```
User (Phone) → Twilio → WebSocket Bridge → Gemini Live API
                ↓              ↓              ↓
            8kHz μ-law    Resampling    16kHz PCM
                           ↓
                    RAG Functions
                   (Vector Store)
```

### Technology Stack

- **Voice Processing**: Twilio Media Streams (WebSocket)
- **AI Engine**: Gemini 2.0 Flash Multimodal Live API
- **Backend**: FastAPI + Python 3.9+
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: Sentence Transformers (Multilingual)
- **Audio Processing**: scipy, numpy, audioop

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- Twilio account with phone number
- Google Gemini API key
- ngrok (for local development)

### Step 1: Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd streaming-voice-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

Required environment variables:

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Exotel (for ambulance calls)
EXOTEL_SID=your_exotel_sid
EXOTEL_TOKEN=your_exotel_token
EXOTEL_NUMBER=your_exotel_number

# Server
SERVER_URL=https://your-ngrok-url.ngrok.io
PORT=8000

# Emergency
AMBULANCE_NUMBER=+911082345678
```

### Step 3: Setup Databases

```bash
# Create vector databases
python scripts/setup_databases.py
```

This will create three FAISS databases:
- Hospital information
- Ayushman Bharat scheme details
- NCERT curriculum content

### Step 4: Run Tests

```bash
# Test RAG functions
python tests/test_rag.py
```

Expected output:
```
✅ Hospital search working
✅ Scheme info retrieval working
✅ Homework help working
```

## 🚀 Running the Server

### Local Development

```bash
# Terminal 1: Start the server
python main.py

# Terminal 2: Start ngrok
ngrok http 8000
```

The server will start on `http://localhost:8000`

### Configure Twilio

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Your number
3. Under "Voice & Fax", set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/incoming-call`
   - **HTTP**: POST
4. Save

## 📞 Making a Test Call

1. Call your Twilio phone number
2. Wait for the greeting in Hindi
3. Speak your query:
   - "मुझे गुवाहाटी में अस्पताल चाहिए"
   - "आयुष्मान भारत के बारे में बताओ"
   - "कक्षा 8 विज्ञान में फसल उत्पादन क्या है?"
   - "मुझे आपातकालीन मदद चाहिए" (Emergency)

## 🔧 API Endpoints

### Health Check
```bash
GET /health
```

### Incoming Call (Twilio Webhook)
```bash
POST /incoming-call
```

### WebSocket Media Stream
```bash
WS /media-stream
```

### Test RAG Functions
```bash
POST /test-rag
Content-Type: application/json

{
  "function": "search_hospitals",
  "args": {
    "location": "गुवाहाटी",
    "hospital_type": "Private"
  }
}
```

### Statistics
```bash
GET /stats
```

## 🗂️ Project Structure

```
streaming-voice-ai/
├── main.py                    # FastAPI application
├── websocket_handler.py       # Twilio ↔ Gemini bridge
├── gemini_client.py           # Gemini Live API client
├── audio_resampler.py         # Audio format conversion
├── vector_store.py            # FAISS vector databases
├── rag_tools.py               # RAG function implementations
├── emergency_handler.py       # Emergency detection & calling
├── sms_service.py             # SMS notifications
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── data/
│   ├── hospital_vectors/      # Hospital database
│   ├── scheme_vectors/        # Scheme database
│   ├── ncert_vectors/         # NCERT database
│   └── emergency_logs/        # Emergency call logs
├── scripts/
│   └── setup_databases.py     # Database creation script
└── tests/
    └── test_rag.py            # RAG function tests
```

## 🔬 How It Works

### Audio Flow

1. **User speaks** → Twilio captures (8kHz μ-law)
2. **Twilio** → Bridge server via WebSocket
3. **Resampler** converts 8kHz μ-law → 16kHz PCM
4. **Gemini** processes audio in real-time
5. **Gemini** generates response (24kHz PCM)
6. **Resampler** converts 24kHz PCM → 8kHz μ-law
7. **Bridge** → Twilio → User hears response

**Total latency: ~1-1.5 seconds**

### Function Calling

Gemini can call these functions based on conversation:

1. **search_hospitals(location, type)**
   - Queries FAISS vector store
   - Returns nearest hospitals with contact info

2. **get_scheme_info(query)**
   - Retrieves Ayushman Bharat information
   - Returns eligibility, benefits, application process

3. **get_homework_help(subject, class, question)**
   - Searches NCERT curriculum database
   - Returns explanations and examples

4. **call_ambulance(location, emergency_type)**
   - Logs emergency
   - Initiates Exotel call to 108
   - Sends SMS alert to user

## 🎛️ Configuration Options

### Voice Selection

Edit `gemini_client.py`:

```python
"prebuilt_voice_config": {
    "voice_name": "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
}
```

### Audio Quality

Edit `audio_resampler.py` to adjust sample rates:

```python
self.twilio_rate = 8000          # Twilio (fixed)
self.gemini_input_rate = 16000   # Can increase for better quality
self.gemini_output_rate = 24000  # Gemini output (fixed)
```

### Response Length

Edit system instruction in `gemini_client.py`:

```python
"Keep responses under 40 words for voice clarity."  # Adjust as needed
```

## 📊 Monitoring & Logging

### Log Files

- `voice_ai.log` - Main application logs
- `data/emergency_logs/emergencies_YYYYMMDD.log` - Emergency call records

### View Logs

```bash
# Real-time logs
tail -f voice_ai.log

# Emergency logs
cat data/emergency_logs/emergencies_*.log
```

### Metrics

```bash
# Get server statistics
curl http://localhost:8000/stats
```

## 🐛 Troubleshooting

### Issue: "Gemini WebSocket connection failed"

**Solution**: Check your `GEMINI_API_KEY` in `.env`

```bash
# Test API key
curl -H "x-goog-api-key: YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

### Issue: "Twilio WebSocket not connecting"

**Solution**: 
1. Ensure ngrok is running
2. Update Twilio webhook URL
3. Check server logs for errors

### Issue: "Audio quality is poor"

**Solution**: 
1. Check internet connection (both server and phone)
2. Increase resampling quality in `audio_resampler.py`
3. Use Twilio's Super SIM for better quality

### Issue: "RAG functions not working"

**Solution**:
```bash
# Rebuild databases
python scripts/setup_databases.py

# Test functions
python tests/test_rag.py
```

### Issue: "Ambulance call not going through"

**Solution**:
1. Check Exotel credentials in `.env`
2. Verify ambulance number format (+91...)
3. Check Exotel account balance

## 💰 Cost Estimation (24-48 hour hackathon)

| Service | Usage | Cost |
|---------|-------|------|
| Gemini Live API | ~100 calls × 2 min | $0-50 (preview) |
| Twilio Phone Number | 1 number | $1 |
| Twilio Media Streams | 100 calls × 2 min | $0.50 |
| ngrok | Basic plan | Free |
| **Total** | | **~$2-52** |

## 🚀 Deployment

### Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Deploy to Render

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`
5. Add environment variables

### Production Checklist

- [ ] Use production-grade ASGI server (gunicorn + uvicorn)
- [ ] Enable HTTPS (Railway/Render provide this)
- [ ] Set up proper logging and monitoring
- [ ] Configure rate limiting
- [ ] Add authentication for admin endpoints
- [ ] Set up database backups
- [ ] Configure auto-scaling

## 🧪 Testing

### Unit Tests

```bash
# Test audio resampling
python -c "from audio_resampler import resampler; print('✅ Resampler OK')"

# Test vector store
python -c "from vector_store import vector_store; vector_store.load_all_databases(); print('✅ Vector store OK')"
```

### Integration Tests

```bash
# Test full RAG pipeline
python tests/test_rag.py
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test (create locustfile.py first)
locust -f locustfile.py
```

## 📚 Resources

- [Gemini Live API Docs](https://ai.google.dev/gemini-api/docs/live-api)
- [Twilio Media Streams](https://www.twilio.com/docs/voice/twiml/stream)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Google Gemini team for the Live API
- Twilio for media streaming support
- Rural India communities for inspiration

## 📧 Support

For issues and questions:
- Create a GitHub issue
- Email: your-email@example.com

---

**Built with ❤️ for rural India 🇮🇳**

**Latency: <1 second | Language: Hindi | Coverage: Healthcare + Education**
