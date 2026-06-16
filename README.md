# AI Agent for Telephony - Voice Bot

A production-ready conversational AI telephony system built on Vocode, integrating Deepgram, OpenAI, and a pluggable text-to-speech layer (ElevenLabs or [60db](https://60db.ai)) to deliver natural voice interactions for inbound and outbound phone calls.

## Overview

This AI-powered telephony solution enables businesses to deploy intelligent voice agents for various use cases including customer support, appointment scheduling, lead qualification, and information collection. The system provides seamless integration with existing telephony infrastructure through Twilio's robust platform.

### Key Features

- **Real-time Voice Processing**: Advanced speech-to-text and text-to-speech capabilities
- **Intelligent Conversation Management**: OpenAI-powered natural language understanding
- **Scalable Architecture**: Docker-based deployment with Kubernetes support
- **Comprehensive Monitoring**: Built-in Prometheus metrics and observability
- **Flexible Configuration**: Customizable agents, transcribers, and synthesizers
- **Pluggable TTS**: Switch between ElevenLabs and 60db with a single environment variable — no code changes

## Architecture

The system leverages the following technology stack:

- **Voice Processing**: Deepgram for speech transcription; ElevenLabs **or** 60db for synthesis (selectable via `TTS_PROVIDER`)
- **AI Engine**: OpenAI for conversational intelligence
- **Telephony**: Twilio for call management and routing
- **Infrastructure**: FastAPI, Redis, Docker, Kubernetes
- **Monitoring**: Prometheus metrics collection

## System Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AI TELEPHONY VOICE BOT WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    👤 USER (Phone Call)
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              🌐 TWILIO TELEPHONY SERVICE                                │
│                          ┌─────────────────┬─────────────────┐                          │
│                          │   Inbound Call  │  Outbound Call  │                          │
│                          │    Webhook      │   Initiation    │                          │
└──────────────────────────┼─────────────────┼─────────────────┼──────────────────────────┘
                           │                 │                 │
                           ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           📱 VOICE BOT APPLICATION CORE                                │
│                                                                                         │
│  ┌─────────────────────┐                                    ┌─────────────────────┐    │
│  │  📞 INBOUND HANDLER │                                    │ 📱 OUTBOUND HANDLER │    │
│  │   (inbound.py)      │                                    │ (outbound_call.py)  │    │
│  └──────────┬──────────┘                                    └──────────┬──────────┘    │
│             │                                                          │               │
│             └──────────────────────┐              ┌────────────────────┘               │
│                                    ▼              ▼                                    │
│                          ┌─────────────────────────────┐                              │
│                          │  🎯 VOICE BOT EVENTS MANAGER │                              │
│                          │  (VoiceBotEventsManager)     │                              │
│                          │                              │                              │
│                          │  Event Types Handled:        │                              │
│                          │  • TRANSCRIPT               │                              │
│                          │  • TRANSCRIPT_COMPLETE      │                              │
│                          │  • PHONE_CALL_CONNECTED     │                              │
│                          │  • PHONE_CALL_ENDED         │                              │
│                          │  • RECORDING                │                              │
│                          │  • ACTION                   │                              │
│                          └─────────────┬───────────────┘                              │
│                                        │                                              │
│                                        ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    🏭 AGENT FACTORY & CONFIGURATION                            │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │  │
│  │  │ 📝 PROMPT       │    │ 🏭 AGENT        │    │ 🗄️ REDIS CONFIG │           │  │
│  │  │ HANDLER         │    │ FACTORY         │    │ MANAGER         │           │  │
│  │  │ (system_prompt) │    │ (SpellerAgent   │    │ (Session Store) │           │  │
│  │  └─────────────────┘    │ Factory)        │    └─────────────────┘           │  │
│  │                         └─────────┬───────┘                                  │  │
│  │                                   │                                          │  │
│  │                    ┌──────────────┼──────────────┐                          │  │
│  │                    ▼              ▼              ▼                          │  │
│  │         ┌─────────────────┐              ┌─────────────────┐                │  │
│  │         │ 🤖 CHATGPT      │              │ 🔤 SPELLER      │                │  │
│  │         │ AGENT           │              │ AGENT           │                │  │
│  │         │ (OpenAI)        │              │ (Character      │                │  │
│  │         │                 │              │ Spelling)       │                │  │
│  │         └─────────────────┘              └─────────────────┘                │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            🔄 REAL-TIME PROCESSING PIPELINE                            │
│                                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │    🎤       │    │    📝       │    │    🤖       │    │    🔊       │            │
│  │  DEEPGRAM   │───▶│   EVENTS    │───▶│   AGENT     │───▶│ ELEVENLABS  │            │
│  │ (Speech-to- │    │  MANAGER    │    │ PROCESSING  │    │   / 60db    │            │
│  │   Text)     │    │(Transcript) │    │(AI Response)│    │(Text-to-    │            │
│  │             │    │             │    │             │    │ Speech)     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘            │
│         ▲                                      │                   │                 │
│         │                                      ▼                   ▼                 │
│  ┌─────────────┐                    ┌─────────────────────────────────┐              │
│  │ 🌐 TWILIO   │◀───────────────────│      🎯 EVENTS MANAGER          │              │
│  │ (Audio      │                    │     (Response Routing)          │              │
│  │ Streaming)  │                    └─────────────────────────────────┘              │
│  └─────────────┘                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          📊 MONITORING & ANALYTICS LAYER                              │
│                                                                                         │
│  ┌─────────────────────┐              ┌─────────────────────┐                         │
│  │ 📈 PROMETHEUS       │              │ 📋 EVENT LOGGING    │                         │
│  │ METRICS             │              │ & ANALYTICS         │                         │
│  │                     │              │                     │                         │
│  │ • Session Counter   │              │ • Call Duration     │                         │
│  │ • Active Sessions   │              │ • Transcript Logs   │                         │
│  │ • Call Analytics    │              │ • Error Tracking    │                         │
│  │                     │              │ • Performance Data  │                         │
│  └─────────────────────┘              └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              🔧 EXTERNAL SERVICES                                      │
│                                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ 🌐 TWILIO   │  │ 🎤 DEEPGRAM │  │ 🧠 OPENAI   │  │ 🔊 ELEVEN   │                  │
│  │ Telephony   │  │ Speech-to-  │  │ Language    │  │ LABS / 60db │                  │
│  │ Platform    │  │ Text API    │  │ Model API   │  │ Text-to-    │                  │
│  │             │  │             │  │             │  │ Speech API  │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                  📊 DATA FLOW LEGEND
                              ═══════════════════════════
                              ───▶  Audio/Voice Stream
                              ═══▶  Text/Data Processing  
                              ┄┄▶   Configuration/Control
                              ▲▼    Bidirectional Communication
```

### Workflow Description

#### 1. **Call Initiation Phase**
```
User ──(Phone Call)──▶ Twilio ──(Webhook/API)──▶ Voice Bot Application
```
- **Inbound**: User dials Twilio number → Webhook triggers `inbound.py`
- **Outbound**: Application calls `outbound_call.py` → Twilio connects to user

#### 2. **Session Management & Event Processing**
```
Call Handler ──▶ VoiceBotEventsManager ──▶ Agent Factory ──▶ Selected Agent
```
- Events Manager handles all call lifecycle events
- Session metrics tracked via Prometheus
- Agent Factory selects appropriate AI agent based on configuration

#### 3. **Real-Time Voice Processing Pipeline**
```
User Audio ──▶ Deepgram ──▶ Text ──▶ AI Agent ──▶ Response ──▶ ElevenLabs / 60db ──▶ Audio ──▶ User
```
- **Step 1**: Deepgram converts speech to text in real-time
- **Step 2**: Selected agent (ChatGPT/Speller) processes the text
- **Step 3**: The configured TTS provider (ElevenLabs or 60db, per `TTS_PROVIDER`) synthesizes the AI response back to audio
- **Step 4**: Twilio streams audio response to user

#### 4. **Agent Types & Processing**
- **🤖 ChatGPT Agent**: Uses OpenAI API for intelligent conversations
- **🔤 Speller Agent**: Simple character-by-character spelling functionality
- **📝 Prompt Handler**: Loads system prompts from `system_prompt.md`

#### 5. **Event Types Handled**
- `TRANSCRIPT`: Real-time speech transcription updates
- `PHONE_CALL_CONNECTED`: Session initialization and metrics increment
- `PHONE_CALL_ENDED`: Session cleanup and metrics decrement
- `RECORDING`: Call recording management and storage
- `ACTION`: Custom action execution and logging

#### 6. **Monitoring & Analytics**
- **📈 Prometheus Metrics**: Session counters, active call tracking
- **📋 Event Logging**: Comprehensive call analytics and debugging
- **🔍 Real-time Monitoring**: Performance tracking and error detection

## Prerequisites

### Required Dependencies
- Docker and Docker Compose
- Python 3.8+ with Poetry (for development)

### API Keys Required
- **Deepgram**: Speech transcription services
- **OpenAI**: Language model and conversation management
- **ElevenLabs**: Text-to-speech synthesis (default TTS provider)
- **60db** _(optional)_: Alternative text-to-speech provider, enabled with `TTS_PROVIDER=60db`
- **Twilio**: Telephony services and phone number management

### Development Tools (Optional)
- Ngrok or Cloudflare Tunnels for local testing
- Kubernetes cluster for production deployment
- Helm 3.0+ for Kubernetes deployments

## Quick Start

### 1. Environment Configuration

```bash
cp .env.template .env
```

Configure your `.env` file with the required API keys:

```env
# Telephony Configuration
BASE_URI=your-domain.com
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
FROM_PHONE=+1234567890
TO_PHONE=+1234567890

# AI Services
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
ELEVEN_LABS_API_KEY=your_eleven_labs_key
ELEVEN_LABS_VOICE_ID=your_voice_id
```

### 2. Local Development Setup

For local testing, expose your development server:

```bash
ngrok http 6000
```

Update your `.env` with the ngrok URL (without `https://`):
```env
BASE_URI=abc123.ngrok.app
```

### 3. Start the Application

```bash
docker-compose up --build
```

The application will be available at `http://localhost:6000`

## Telephony Configuration

### Inbound Call Setup

1. **Acquire Phone Number**
   - Log into your Twilio Console
   - Navigate to Phone Numbers → Manage → Buy a number
   - Purchase a phone number for your region

2. **Configure Webhook**
   - Go to Phone Numbers → Manage → Active Numbers
   - Select your purchased number
   - Set Webhook URL to: `https://your-domain.com/inbound_call`
   - Set HTTP method to `POST`
   - Save configuration

### Outbound Call Execution

Ensure your environment variables are configured, then execute:

```bash
poetry install
# Run as a module from the repo root so package-relative imports resolve.
poetry run python -m app.outbound_call
```

## Monitoring and Observability

The system exposes Prometheus metrics on port 8000:

- `voicebot_session_count`: Total number of sessions initiated
- `voicebot_active_sessions`: Current active session count

Access metrics at: `http://localhost:8000/metrics`

## Production Deployment

### Kubernetes with Helm

#### Prerequisites
- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- Helm 3.0+
- kubectl configured for your cluster

#### Deployment Process

1. **Clone Repository**
```bash
git clone https://github.com/danieladdisonorg/AI-Agent-for-Telephony-voice-bot
cd AI-Agent-for-Telephony-voice-bot
```

2. **Create Configuration**

Create `production-values.yaml`:

```yaml
env:
  BASE_URI: "your-production-domain.com"
  DEEPGRAM_API_KEY: "your-deepgram-key"
  OPENAI_API_KEY: "your-openai-key"
  OPENAI_BASE_URL: "https://api.openai.com/v1"
  ELEVEN_LABS_API_KEY: "your-eleven-labs-key"
  ELEVEN_LABS_VOICE_ID: "your-voice-id"
  TWILIO_ACCOUNT_SID: "your-twilio-sid"
  TWILIO_AUTH_TOKEN: "your-twilio-token"
  FROM_PHONE: "your-twilio-number"
  TO_PHONE: "your-target-number"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

replicas: 3
```

3. **Deploy Application**
```bash
helm install voice-bot ./kubernetes/voice-bot-helm/voice-bot -f production-values.yaml
```

4. **Verify Deployment**
```bash
kubectl get pods -l app=voice-bot
kubectl get services voice-bot
```

#### Management Commands

**Update Deployment:**
```bash
helm upgrade voice-bot ./kubernetes/voice-bot-helm/voice-bot -f production-values.yaml
```

**Remove Deployment:**
```bash
helm uninstall voice-bot
```

**View Logs:**
```bash
kubectl logs -f deployment/voice-bot
```

## Configuration Options

### Agent Configuration
Customize conversation behavior through `AgentConfig` parameters in your deployment configuration.

#### ChatGPT Agent Configuration
```python
ChatGPTAgentConfig(
    initial_message=BaseMessage(text="Hello! How can I help you today?"),
    prompt_preamble="You are a helpful customer service representative...",
    generate_responses=True,
    model_name="gpt-3.5-turbo",  # or "gpt-4"
    temperature=0.7,
    max_tokens=150
)
```

#### Speller Agent Configuration
```python
SpellerAgentConfig(
    # Simple configuration for character spelling functionality
    # Automatically spells out each character with spaces
)
```

### System Prompt Customization

Create or modify `app/system_prompt.md` to customize your AI agent's behavior:

```markdown
# Example System Prompt

You are a professional customer service representative for [Your Company]. 

## Your Role:
- Provide helpful and accurate information
- Maintain a friendly and professional tone
- Ask clarifying questions when needed
- Keep responses concise and clear

## Guidelines:
- Always greet customers warmly
- Listen actively to their concerns
- Provide step-by-step solutions
- End calls with next steps or follow-up information

## Restrictions:
- Do not provide personal information
- Escalate complex technical issues
- Stay within your knowledge domain
```

### Transcriber Options
- **Default**: Deepgram (recommended for production)
  - High accuracy speech recognition
  - Real-time processing
  - Multiple language support
- **Alternative**: Configure custom transcription services through Vocode

### Synthesizer Options

The TTS provider is selected at runtime with the `TTS_PROVIDER` environment
variable — no code changes required. Both providers run at telephony-native
MULAW / 8000 Hz, and the choice applies to inbound and outbound calls alike.

- **`elevenlabs`** (default): ElevenLabs high-quality voice synthesis
  - Natural-sounding voices, emotional expression, multiple voice options
  - Uses ElevenLabs' low-latency experimental websocket streaming for inbound calls
- **`60db`**: [60db](https://60db.ai) voice synthesis
  - Implemented as a custom Vocode synthesizer (`app/sixtydb_synthesizer.py`)
    streaming over 60db's WebSocket TTS API (`wss://api.60db.ai/ws/tts`)
  - Emits G.711 μ-law at 8 kHz directly, so no transcoding is needed for Twilio
  - Registered with the telephony server via `VoiceBotSynthesizerFactory`
    (`app/synthesizer_factory.py`); ElevenLabs keeps working unchanged

**Switching to 60db:**

```env
TTS_PROVIDER=60db
SIXTYDB_API_KEY=your_60db_api_key
SIXTYDB_VOICE_ID=your_60db_voice_id   # from GET https://api.60db.ai/myvoices
# Optional tuning (defaults shown)
SIXTYDB_SPEED=1.0
SIXTYDB_STABILITY=50
SIXTYDB_SIMILARITY=75
```

To list your available 60db voices and their IDs:

```bash
curl https://api.60db.ai/myvoices -H "Authorization: Bearer $SIXTYDB_API_KEY"
```

## Advanced Configuration

### Environment Variables Reference

```env
# Core Application
BASE_URI=your-domain.com
PORT=6000

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
FROM_PHONE=+1234567890
TO_PHONE=+1234567890

# AI Services
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Text-to-Speech provider: "elevenlabs" (default) or "60db"
TTS_PROVIDER=elevenlabs

# ElevenLabs (used when TTS_PROVIDER=elevenlabs)
ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
ELEVEN_LABS_VOICE_ID=your_preferred_voice_id

# 60db (used when TTS_PROVIDER=60db)
SIXTYDB_API_KEY=your_60db_api_key
SIXTYDB_VOICE_ID=your_60db_voice_id
SIXTYDB_SPEED=1.0
SIXTYDB_STABILITY=50
SIXTYDB_SIMILARITY=75

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# Monitoring
PROMETHEUS_PORT=8000
LOG_LEVEL=INFO

# Audio Configuration
AUDIO_ENCODING=mulaw
SAMPLING_RATE=8000
CHUNK_SIZE=8192
```

### Docker Compose Configuration

For development and testing:

```yaml
version: '3.8'
services:
  voice-bot:
    build: .
    ports:
      - "6000:6000"
      - "8000:8000"
    environment:
      - BASE_URI=${BASE_URI}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ELEVEN_LABS_API_KEY=${ELEVEN_LABS_API_KEY}
      - ELEVEN_LABS_VOICE_ID=${ELEVEN_LABS_VOICE_ID}
    volumes:
      - ./app:/app
      - ./logs:/logs
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Troubleshooting

### Common Issues

#### Connection Problems
- **Symptom**: Calls not connecting or dropping
- **Solutions**:
  - Verify all API keys are valid and have sufficient credits
  - Check network connectivity and firewall rules
  - Ensure webhook URLs are publicly accessible
  - Test with ngrok for local development

#### Audio Quality Issues
- **Symptom**: Poor audio quality or delays
- **Solutions**:
  - Verify Deepgram and ElevenLabs configurations
  - Check network latency and bandwidth
  - Review audio codec settings (mulaw recommended)
  - Monitor CPU and memory usage

#### Agent Response Issues
- **Symptom**: AI not responding appropriately
- **Solutions**:
  - Check OpenAI API key and quota
  - Review system prompt configuration
  - Verify agent factory configuration
  - Check event manager logs

#### Deployment Issues
```bash
# Check pod status
kubectl describe pod <pod-name>

# View detailed logs
kubectl logs <pod-name> --previous

# Check service connectivity
kubectl port-forward service/voice-bot 6000:3000

# Debug configuration
kubectl get configmap voice-bot-config -o yaml
```

### Debugging Commands

#### Local Development
```bash
# View application logs
docker-compose logs -f voice-bot

# Check Redis connection
docker-compose exec redis redis-cli ping

# Monitor metrics
curl http://localhost:8000/metrics

# Test webhook endpoint
curl -X POST http://localhost:6000/inbound_call \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&To=+1234567890"
```

#### Production Monitoring
```bash
# Monitor active sessions
kubectl exec -it deployment/voice-bot -- python -c "
from app.metrics import SESSION_GAUGE
print(f'Active sessions: {SESSION_GAUGE._value.get()}')
"

# Check system resources
kubectl top pods -l app=voice-bot

# View recent events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Performance Optimization

#### Scaling Recommendations
- **Low Traffic** (< 10 concurrent calls): 1-2 replicas, 512Mi memory
- **Medium Traffic** (10-50 concurrent calls): 3-5 replicas, 1Gi memory
- **High Traffic** (50+ concurrent calls): 5+ replicas, 2Gi memory, dedicated nodes

#### Resource Monitoring
```bash
# Monitor resource usage
kubectl top pods -l app=voice-bot --containers

# Check HPA status (if configured)
kubectl get hpa voice-bot

# View resource quotas
kubectl describe quota
```

## API Reference

### Webhook Endpoints

#### Inbound Call Webhook
```
POST /inbound_call
Content-Type: application/x-www-form-urlencoded

Parameters:
- From: Caller's phone number
- To: Called phone number
- CallSid: Twilio call identifier
```

#### Health Check
```
GET /health
Response: {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

#### Metrics Endpoint
```
GET /metrics
Content-Type: text/plain
Response: Prometheus metrics format
```

### Event Types

The system handles the following event types through `VoiceBotEventsManager`:

| Event Type | Description | Metrics Impact |
|------------|-------------|----------------|
| `TRANSCRIPT` | Real-time speech transcription | Logging only |
| `TRANSCRIPT_COMPLETE` | Complete utterance transcribed | Logging only |
| `PHONE_CALL_CONNECTED` | Call successfully connected | Increments session counters |
| `PHONE_CALL_ENDED` | Call terminated | Decrements active sessions |
| `PHONE_CALL_DID_NOT_CONNECT` | Call failed to connect | Error logging |
| `RECORDING` | Call recording available | Logging with URL |
| `ACTION` | Custom action executed | Action logging |

## Support and Contributing

### Getting Help
- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via [GitHub Issues](https://github.com/danieladdisonorg/AI-Agent-for-Telephony-voice-bot/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/danieladdisonorg/AI-Agent-for-Telephony-voice-bot/discussions)

### Contributing Guidelines
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone repository
git clone https://github.com/danieladdisonorg/AI-Agent-for-Telephony-voice-bot
cd AI-Agent-for-Telephony-voice-bot

# Install dependencies
poetry install

# Set up pre-commit hooks
pre-commit install

# Run tests
poetry run pytest

# Run linting
poetry run flake8 app/
poetry run black app/
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Changelog

### Unreleased
- Added **60db** as a selectable text-to-speech provider alongside ElevenLabs, switchable via the `TTS_PROVIDER` environment variable (no code changes required)
- New custom Vocode synthesizer (`app/sixtydb_synthesizer.py`) streaming 60db's WebSocket TTS at telephony-native μ-law / 8 kHz
- New synthesizer factory (`app/synthesizer_factory.py`) and provider selector (`app/tts_config.py`)
- Outbound script now runs as a module: `poetry run python -m app.outbound_call`

### v1.0.0
- Initial release with Vocode integration
- Support for Deepgram, OpenAI, and ElevenLabs
- Docker and Kubernetes deployment support
- Prometheus metrics and monitoring
- Inbound and outbound call handling
- Multiple agent types (ChatGPT, Speller)

### Roadmap
- [x] Support for additional TTS providers (60db added)
- [ ] Support for further TTS providers
- [ ] Advanced conversation analytics
- [ ] Multi-language support
- [ ] Call recording and playback features
- [ ] Advanced routing and IVR capabilities
- [ ] Integration with CRM systems
