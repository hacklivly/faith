# Isabella — Personal AI Companion

A voice-interactive AI companion that runs on weak hardware (Windows 10, Intel i3, no GPU).
Your PC only captures mic/webcam and plays audio. Groq's free API handles thinking, seeing, listening.
Chatterbox provides voice-cloned TTS — she speaks in YOUR chosen voice.

## Quick Start

### 1. Get Groq API key (free)
Go to https://console.groq.com → sign up → create API key.

Create a `.env` file in the project root:
```
GROQ_API_KEY=gsk_your_key_here
```
Or set as Windows environment variable.

### 2. Add voice sample
Put a clear `.wav` file (5-30 seconds of speech) in:
```
data/voice_sample/
```
This is the voice she'll clone and speak in.

### 3. Install dependencies
```
pip install -r requirements.txt
```
PyAudio fix for Windows:
```
pip install pipwin
pipwin install pyaudio
```

### 4. Pre-generate common phrases (optional but recommended)
```
python voice_engine.py --generate
```
This takes time on CPU (~15-30 sec per phrase). Do it once. Go get chai.

### 5. Run
```
python main.py
```

## How It Works

Talk normally. She listens via VAD (voice activity detection), transcribes with Whisper,
thinks with Llama on Groq, and speaks back in the cloned voice via Chatterbox.

**First time** she says something = Chatterbox synthesizes it (slow on CPU, ~15-30s).
**Every time after** = instant playback from cache.

The more you talk, the more gets cached, the faster she gets.

## Voice Commands

Just speak naturally. She understands:

### General
- Talk normally — she'll respond conversationally
- Say "look" / "see this" / "how do I look" — she'll look at webcam
- Say "my screen" / "what am I doing" — she'll look at your screen

### Apps & Websites
- "open chrome" / "open notepad" / "open spotify"
- "close chrome" / "close notepad"
- "open youtube" / "open github" / "open whatsapp"

### Music & Media
- "play [song name]" — searches and plays on YouTube
- "play [song] on spotify" — plays on Spotify
- "pause" / "next song" / "skip" / "previous song"

### Search
- "search for [query]" — Google search
- "search on youtube [query]" — YouTube search

### System Control
- "volume 50" / "mute"
- "brightness 70"
- "battery" / "system info"
- "screenshot"
- "lock pc" / "sleep pc"
- "shutdown" / "restart" / "cancel shutdown"
- "what time is it"
- "what wifi"

### Files & Tabs
- "list files in [path]"
- "what apps are running"
- "close tab" / "next tab" / "previous tab"
- "read clipboard"

### Complex Tasks
- "create a file..." / "write..." / "delete..." / "rename..."
- "remind me..." / "timer..."
- "email..." / "send..."
- She'll ask clarifying questions if needed

## Personality

Edit `personality.py` to change who she is. This is the soul of the project.

She has:
- **Mood** — changes based on conversations, affects tone
- **Memory** — journals conversations, remembers topics
- **Emotions** — detects your mood, responds empathetically
- **Proactive check-ins** — looks at you/screen randomly, asks if you're okay
- **Relationship tracking** — inside jokes, milestones, favorites
- **Human traits** — overthinking, shyness, protectiveness, jealousy

## Voice Configuration

Voice is cloned from your sample via Chatterbox TTS (offline, no API).

```
data/voice_sample/   ← put .wav here (5-30s of clear speech)
data/voice_pack/     ← pre-generated common phrases
data/tts_cache/      ← runtime-cached phrases (auto-grows)
```

### Pre-generate common phrases:
```
python voice_engine.py --generate
```

### Speed tips:
- Shorter voice sample (5-10s) = faster conditioning
- Pre-generate common phrases = zero latency for those
- More RAM helps (model is ~2GB)
- If you ever get a GPU: change `device="cpu"` to `device="cuda"` in voice_engine.py

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | Main event loop, turn handling, command routing |
| `personality.py` | Who she is — mood/memory/identity in system prompt |
| `brain.py` | Groq API calls for reasoning, vision, journaling |
| `ears.py` | VAD mic recording + Whisper transcription |
| `mouth.py` | Chatterbox TTS playback with interrupt support |
| `voice_engine.py` | Chatterbox model, caching, voice synthesis |
| `eyes.py` | Webcam frame capture |
| `screen_vision.py` | Screen capture for screen-reading |
| `hands.py` | OS actions (open app, volume, shutdown, etc.) |
| `memory.py` | Journal + persistent mood storage |
| `emotion_engine.py` | Detects user emotions from text |
| `personality.py` | Core identity + system prompt builder |
| `config.py` | All settings (API keys, models, voice) |
| `gui.py` | Tkinter GUI with mic toggle + text input |
| `scheduler.py` | Proactive check-in timing |
| `knowledge.py` | Book/document knowledge base |
| `browser_control.py` | YouTube/Spotify playback |
| `self_solve.py` | Multi-step task decomposition |
| `screen_agent.py` | Vision-based screen clicking |

## Multiple API Keys

Put multiple Groq keys in `.env` to avoid rate limits:
```
GROQ_API_KEY=gsk_key1
GROQ_API_KEY_2=gsk_key2
GROQ_API_KEY_3=gsk_key3
```
Each module (brain, STT, vision) uses its own key.

## ElevenLabs Multi-Account TTS

Got multiple free ElevenLabs accounts? Add all keys — Isabella auto-rotates through them.
When one account's monthly limit is hit, she instantly switches to the next.
When ALL accounts are exhausted, she falls back to Edge-TTS (unlimited, free).

```
ELEVENLABS_API_KEY=sk_your_first_key
ELEVENLABS_API_KEY_2=sk_your_second_key
ELEVENLABS_API_KEY_3=sk_your_third_key
ELEVENLABS_API_KEY_4=sk_your_fourth_key
ELEVENLABS_API_KEY_5=sk_your_fifth_key
ELEVENLABS_API_KEY_6=sk_your_sixth_key
ELEVENLABS_API_KEY_7=sk_your_seventh_key
ELEVENLABS_API_KEY_8=sk_your_eighth_key
ELEVENLABS_VOICE_ID=your_isabella_voice_id
```

### Setup:
1. Create voice on any one ElevenLabs account (voice ID is shared across all)
2. Copy the voice ID → set as `ELEVENLABS_VOICE_ID`
3. Add API keys from each account

### How it works:
- Tries key #1 first → if 429/401/403 → rotates to key #2 → ... → key #8
- Only falls back to Edge-TTS after ALL keys are exhausted
- Resets on next session (monthly limits refresh on their own)
