# 🚀 Deployment Guide

## Production Deployment Options

### Option 1: Railway (Recommended)

**Pros**: Easy, automatic HTTPS, great for WebSockets

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize Project**
```bash
cd streaming-voice-ai
railway init
```

4. **Set Environment Variables**
```bash
railway variables set GEMINI_API_KEY=your_key
railway variables set TWILIO_ACCOUNT_SID=your_sid
railway variables set TWILIO_AUTH_TOKEN=your_token
railway variables set TWILIO_PHONE_NUMBER=+1234567890
railway variables set PORT=8000
```

5. **Deploy**
```bash
railway up
```

6. **Get Your URL**
```bash
railway domain
# Example: your-app.railway.app
```

7. **Update Twilio Webhook**
- URL: `https://your-app.railway.app/incoming-call`

---

### Option 2: Render

**Pros**: Free tier, easy setup, good documentation

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: streaming-voice-ai
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python scripts/setup_databases.py`
   - **Start Command**: `python main.py`
   - **Instance Type**: Free (or Starter for production)

3. **Add Environment Variables**
   ```
   GEMINI_API_KEY=your_key
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE_NUMBER=+1234567890
   PORT=8000
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (3-5 minutes)

5. **Get Your URL**
   - Example: `https://streaming-voice-ai.onrender.com`

6. **Update Twilio**
   - Webhook: `https://your-app.onrender.com/incoming-call`

---

### Option 3: Google Cloud Run

**Pros**: Serverless, scales to zero, good for WebSockets

1. **Create Dockerfile**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Setup databases on container start
RUN python scripts/setup_databases.py

EXPOSE 8080

CMD ["python", "main.py"]
```

2. **Build and Push**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/voice-ai
```

3. **Deploy**
```bash
gcloud run deploy voice-ai \
  --image gcr.io/PROJECT_ID/voice-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars GEMINI_API_KEY=your_key,TWILIO_ACCOUNT_SID=your_sid
```

---

### Option 4: DigitalOcean App Platform

1. **Create App**
   - Go to App Platform
   - Connect GitHub repo

2. **Configure**
   - **App Name**: streaming-voice-ai
   - **Plan**: Basic ($5/month)
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python main.py`

3. **Environment Variables**
   - Add all required env vars in dashboard

4. **Deploy**
   - Click "Create Resources"

---

## Production Configuration

### 1. Update main.py for Production

```python
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=4,  # Multiple workers
        reload=False,  # Disable in production
        log_level="info",
        access_log=True
    )
```

### 2. Add Gunicorn (Recommended)

Update `requirements.txt`:
```
gunicorn==21.2.0
```

Create `gunicorn_conf.py`:
```python
import multiprocessing

# Gunicorn config
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
timeout = 120
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

Update start command:
```bash
gunicorn main:app -c gunicorn_conf.py
```

### 3. Environment Variables Checklist

Required:
- ✅ `GEMINI_API_KEY`
- ✅ `TWILIO_ACCOUNT_SID`
- ✅ `TWILIO_AUTH_TOKEN`
- ✅ `TWILIO_PHONE_NUMBER`

Optional:
- `EXOTEL_SID` (for ambulance calling)
- `EXOTEL_TOKEN`
- `EXOTEL_NUMBER`
- `AMBULANCE_NUMBER`
- `PORT` (default: 8000)

### 4. Database Persistence

For production, mount persistent volume:

**Railway**:
```bash
# Databases auto-persist in Railway volumes
```

**Render**:
```yaml
# Add in render.yaml
volumes:
  - name: data
    mountPath: /app/data
    sizeGB: 1
```

**Docker**:
```bash
docker run -v $(pwd)/data:/app/data your-image
```

### 5. Monitoring & Logging

**Add Sentry**:
```bash
pip install sentry-sdk[fastapi]
```

In `main.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

**Add Prometheus**:
```bash
pip install prometheus-fastapi-instrumentator
```

In `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 6. Security Hardening

**Add rate limiting**:
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/incoming-call")
@limiter.limit("10/minute")
async def incoming_call(request: Request):
    ...
```

**Add CORS properly**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 7. Health Checks

Production-ready health endpoint:

```python
@app.get("/health")
async def health_check():
    # Check all services
    checks = {
        "server": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "vector_store": bool(vector_store.hospital_db),
        "disk_space": shutil.disk_usage("/").free > 1e9,  # > 1GB
        "memory": psutil.virtual_memory().percent < 90
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return Response(
        content=json.dumps(checks),
        status_code=status_code,
        media_type="application/json"
    )
```

### 8. Auto-scaling Configuration

**Railway**: Auto-scales based on CPU/memory

**Render**: Configure in dashboard

**Cloud Run**: Auto-scales 0-1000 instances

**K8s**: Create HPA manifest
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: voice-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: voice-ai
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Post-Deployment Checklist

- [ ] Server is accessible via HTTPS
- [ ] Twilio webhook updated and working
- [ ] Made a test call successfully
- [ ] Checked logs for errors
- [ ] Vector databases loaded
- [ ] SMS service working
- [ ] Health endpoint returns 200
- [ ] Set up monitoring alerts
- [ ] Configured backups
- [ ] Documented deployment process

---

## Troubleshooting Production Issues

### WebSocket Connection Fails

**Cause**: Proxy/load balancer doesn't support WebSockets

**Fix**: 
- Railway/Render: Built-in support ✅
- Nginx: Add proxy settings
```nginx
location /media-stream {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### High Latency

**Causes**:
1. Server location far from users
2. Cold starts (serverless)
3. Slow database queries

**Fixes**:
1. Deploy to region near users (us-central1 for US, asia-south1 for India)
2. Use warm-up requests or reserved instances
3. Pre-load vector databases on startup

### Database Not Persisting

**Cause**: No persistent volume mounted

**Fix**: See "Database Persistence" section above

### Out of Memory

**Cause**: Vector databases too large, not enough RAM

**Fix**:
1. Upgrade instance size
2. Use disk-based FAISS instead of in-memory
3. Implement database sharding

---

## Cost Optimization

### Free Tier Usage

**Render Free**:
- ✅ Enough for testing
- ❌ Spins down after 15 min inactivity
- ❌ Limited hours per month

**Railway Free**:
- ✅ $5 credit per month
- ✅ No sleep
- ✅ Good for demos

**Recommendation**: Start free, upgrade if usage > 1000 calls/month

### Production Costs

**Low Traffic** (100 calls/day):
- Railway: $5/month
- Render: $7/month
- Cloud Run: $0-5/month

**High Traffic** (1000 calls/day):
- Railway: $20-30/month
- Render: $25/month
- Cloud Run: $10-20/month

---

## Support

For deployment issues:
1. Check service status page
2. Review deployment logs
3. Test health endpoint
4. Contact platform support

---

**Last Updated**: 2024
