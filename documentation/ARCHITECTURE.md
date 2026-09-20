# 🏗️ System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION LAYER                      │
│                                                                   │
│  📱 User's Phone → 📞 Twilio Phone Number → 🔊 Voice Call       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TELEPHONY LAYER (Twilio)                      │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │ Voice Gateway   │───▶│ Media Streams    │                   │
│  │ (TwiML)         │    │ (WebSocket)      │                   │
│  │ - Greeting      │    │ - Bidirectional  │                   │
│  │ - Connect       │    │ - Real-time      │                   │
│  └─────────────────┘    └──────┬───────────┘                   │
│                                 │                                │
│                        Audio Format:                             │
│                        8kHz, μ-law, Base64                       │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BRIDGE SERVER (FastAPI)                       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                WebSocket Handler                          │  │
│  │  ┌──────────────┐       ┌───────────────┐               │  │
│  │  │ Twilio       │       │ Gemini        │               │  │
│  │  │ WebSocket    │◀─────▶│ WebSocket     │               │  │
│  │  │ Listener     │       │ Client        │               │  │
│  │  └──────┬───────┘       └───────┬───────┘               │  │
│  │         │                       │                        │  │
│  │         ▼                       ▼                        │  │
│  │  ┌──────────────────────────────────────┐               │  │
│  │  │      Audio Resampler                 │               │  │
│  │  │  • 8kHz μ-law → 16kHz PCM (input)   │               │  │
│  │  │  • 24kHz PCM → 8kHz μ-law (output)  │               │  │
│  │  │  • scipy signal processing           │               │  │
│  │  └──────────────────────────────────────┘               │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────┐               │  │
│  │  │      Conversation Manager            │               │  │
│  │  │  • Track call state                  │               │  │
│  │  │  • Log transcripts                   │               │  │
│  │  │  • Detect emergencies                │               │  │
│  │  │  • Generate summaries                │               │  │
│  │  └──────────────────────────────────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Function Router                          │  │
│  │                                                            │  │
│  │  Gemini Function Call → Python Implementation             │  │
│  │                                                            │  │
│  │  • search_hospitals()    → RAG Query                      │  │
│  │  • get_scheme_info()     → RAG Query                      │  │
│  │  • get_homework_help()   → RAG Query                      │  │
│  │  • call_ambulance()      → Emergency Handler             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────┬───────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│   GEMINI LIVE API       │  │     KNOWLEDGE LAYER          │
│                         │  │                              │
│  ┌──────────────────┐  │  │  ┌────────────────────────┐ │
│  │ Speech Input     │  │  │  │   FAISS Vector Store   │ │
│  │ • VAD            │  │  │  │                        │ │
│  │ • STT (Hindi)    │  │  │  │  ┌──────────────────┐ │ │
│  │ • Real-time      │  │  │  │  │ Hospital DB      │ │ │
│  └──────────────────┘  │  │  │  │ • 5 hospitals    │ │ │
│                         │  │  │  │ • Contact info   │ │ │
│  ┌──────────────────┐  │  │  │  │ • Multilingual   │ │ │
│  │ AI Processing    │  │  │  │  └──────────────────┘ │ │
│  │ • Understanding  │  │  │  │                        │ │
│  │ • Function calls │  │  │  │  ┌──────────────────┐ │ │
│  │ • Context aware  │  │  │  │  │ Scheme DB        │ │ │
│  └──────────────────┘  │  │  │  │ • Ayushman       │ │ │
│                         │  │  │  │ • Eligibility    │ │ │
│  ┌──────────────────┐  │  │  │  │ • Application    │ │ │
│  │ Speech Output    │  │  │  │  └──────────────────┘ │ │
│  │ • TTS (Hindi)    │  │  │  │                        │ │
│  │ • Natural voice  │  │  │  │  ┌──────────────────┐ │ │
│  │ • Streaming      │  │  │  │  │ NCERT DB         │ │ │
│  └──────────────────┘  │  │  │  │ • Class 6-12     │ │ │
└─────────────────────────┘  │  │  │ • Science/Maths  │ │ │
                             │  │  │ • Explanations   │ │ │
                             │  │  └──────────────────┘ │ │
                             │  │                        │ │
                             │  │  Embeddings:           │ │
                             │  │  multilingual-MiniLM   │ │
                             │  └────────────────────────┘ │
                             └──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Exotel           │  │ Twilio SMS       │  │ Logging      │ │
│  │ • Ambulance call │  │ • Post-call SMS  │  │ • Emergency  │ │
│  │ • 108 connect    │  │ • Summaries      │  │ • Analytics  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### 1. Normal Query Flow (Hospital Search)

```
Time: 0.0s
User speaks: "मुझे गुवाहाटी में अस्पताल चाहिए"
     │
     ▼
Time: 0.1s
Twilio captures first audio chunk (20ms)
     │
     ▼
Time: 0.12s
Bridge receives μ-law audio
     │
     ▼
Time: 0.13s
Resampler: 8kHz μ-law → 16kHz PCM
     │
     ▼
Time: 0.14s
Send to Gemini via WebSocket
     │
     ▼
Time: 0.15-0.8s
Gemini processes audio (VAD + STT)
[User continues speaking...]
     │
     ▼
Time: 0.8s
User finishes speaking
     │
     ▼
Time: 0.85s
Gemini detects end-of-speech (VAD)
     │
     ▼
Time: 0.88s
Gemini understanding: "User needs hospital in Guwahati"
     │
     ▼
Time: 0.9s
Gemini calls: search_hospitals(location="गुवाहाटी")
     │
     ▼
Time: 0.92s
Bridge executes function → Query FAISS
     │
     ▼
Time: 0.95s
FAISS returns top 3 hospitals (vector similarity)
     │
     ▼
Time: 0.96s
Format result in Hindi
     │
     ▼
Time: 0.97s
Send function response back to Gemini
     │
     ▼
Time: 1.0s
Gemini generates response + TTS
     │
     ▼
Time: 1.05s
First audio chunk (24kHz PCM) sent to bridge
     │
     ▼
Time: 1.06s
Resampler: 24kHz PCM → 8kHz μ-law
     │
     ▼
Time: 1.08s
Send to Twilio WebSocket
     │
     ▼
Time: 1.1s
User hears: "गुवाहाटी में तीन अस्पताल हैं..."
     │
     ▼
Time: 1.1-2.5s
Streaming audio response continues
     │
     ▼
Time: 2.5s
Response complete

TOTAL LATENCY: ~1.1 seconds
```

### 2. Emergency Flow

```
User speaks: "मुझे दिल का दौरा हो रहा है"
     │
     ▼
Gemini detects emergency keywords
     │
     ▼
Gemini calls: call_ambulance(
    location="user_location",
    emergency_type="दिल का दौरा"
)
     │
     ▼
Bridge Emergency Handler:
├─ Log emergency (with timestamp)
├─ Call Exotel API → Connect to 108
├─ Send SMS alert to user
└─ Return safety instructions
     │
     ▼
Gemini speaks safety instructions:
"शांत रहें। बैठ जाएं। एम्बुलेंस आ रही है..."
     │
     ▼
Exotel connects call to ambulance
     │
     ▼
User receives SMS with emergency details
```

## Component Deep Dive

### Audio Resampler

**Challenge**: Different audio formats
- Twilio: 8kHz, μ-law (phone quality)
- Gemini: 16kHz PCM input, 24kHz PCM output

**Solution**:
```python
# Upsampling (Twilio → Gemini)
1. Decode Base64
2. μ-law → Linear PCM
3. Resample 8kHz → 16kHz (scipy.signal.resample)
4. Encode Base64

# Downsampling (Gemini → Twilio)
1. Decode Base64
2. Resample 24kHz → 8kHz
3. Linear PCM → μ-law
4. Encode Base64
```

**Performance**: ~5ms per chunk

### Vector Store

**Technology**: FAISS (Facebook AI Similarity Search)

**Why FAISS?**
- ✅ Fast similarity search (< 10ms)
- ✅ Supports multilingual embeddings
- ✅ Efficient memory usage
- ✅ Can scale to millions of documents

**Embedding Model**:
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Supports Hindi + English
- 384-dimensional vectors
- ~50MB model size

**Query Process**:
```
User query (Hindi) → Embed → FAISS search → Top K results → Format → Return
                      ↓
                Cosine similarity
                      ↓
              Most relevant docs
```

### WebSocket Management

**Two concurrent WebSockets**:

1. **Twilio WebSocket** (inbound/outbound)
   - Receives user audio
   - Sends AI responses
   - Handles call events (start/stop)

2. **Gemini WebSocket** (bidirectional)
   - Sends user audio
   - Receives AI audio + function calls
   - Maintains real-time connection

**Concurrency**: `asyncio.gather()` runs both loops simultaneously

## Scaling Considerations

### Current Capacity

- **Single instance**: ~50 concurrent calls
- **Bottleneck**: Audio resampling (CPU-intensive)
- **Memory**: ~500MB (with all vector stores)

### Horizontal Scaling

```
Load Balancer
     │
     ├─ Instance 1 (50 calls)
     ├─ Instance 2 (50 calls)
     └─ Instance N (50 calls)
     
Total capacity: N × 50 calls
```

**Note**: Each WebSocket is stateful, so sticky sessions required

### Optimization Ideas

1. **GPU acceleration** for audio processing
2. **Redis** for session state sharing
3. **CDN** for static vector databases
4. **Batch processing** for function calls
5. **Connection pooling** for external APIs

## Security Architecture

### Authentication Flow

```
Incoming Call
     │
     ▼
Twilio Signature Verification
     │
     ▼
Rate Limiting (10 calls/min per number)
     │
     ▼
WebSocket with API key verification
     │
     ▼
Function execution with input validation
```

### Data Protection

- **In-transit**: HTTPS/WSS only
- **At-rest**: Vector DBs (non-sensitive)
- **Logs**: Sanitized (no PII)
- **Emergency logs**: Encrypted + access controlled

## Monitoring Points

```
┌─────────────────┐
│ Application     │
│ Metrics         │
├─────────────────┤
│ • Calls/min     │
│ • Avg latency   │
│ • Error rate    │
│ • WebSocket     │
│   disconnects   │
└─────────────────┘

┌─────────────────┐
│ Infrastructure  │
│ Metrics         │
├─────────────────┤
│ • CPU usage     │
│ • Memory usage  │
│ • Disk I/O      │
│ • Network       │
└─────────────────┘

┌─────────────────┐
│ Business        │
│ Metrics         │
├─────────────────┤
│ • Hospital      │
│   searches      │
│ • Emergency     │
│   calls         │
│ • Homework help │
│ • User          │
│   satisfaction  │
└─────────────────┘
```

## Failure Modes & Recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Gemini API down | Health check | Fallback to basic responses |
| Twilio disconnect | WebSocket error | Reconnect + notify user |
| Vector DB corrupt | Startup check | Rebuild from source |
| High latency | Per-request timing | Circuit breaker + alert |
| Out of memory | System metrics | Restart + scale up |
| Emergency call fails | API response | SMS fallback + log |

## Technology Choices Rationale

### Why FastAPI?
- ✅ Native WebSocket support
- ✅ Async/await for concurrency
- ✅ Fast performance
- ✅ Easy deployment

### Why FAISS over alternatives?
- vs. Pinecone: Free, no API limits
- vs. Weaviate: Simpler, faster for small data
- vs. ChromaDB: Better performance

### Why Gemini Live over alternatives?
- vs. OpenAI Realtime: Better Hindi support
- vs. ElevenLabs: More cost-effective
- vs. Custom STT+LLM+TTS: Single API, lower latency

---

