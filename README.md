# Faith - Personal AI Companion

A personal companion that runs on weak hardware (built for Windows 10, Intel i3,
no GPU) by doing almost nothing locally: your PC only captures mic/webcam input
and plays audio output, while Groq's free API handles the actual thinking,
seeing, and listening.

## 1. Get your free API key

Go to https://console.groq.com, sign up (no credit card needed), and create
an API key.

In PowerShell, set it for your current session:

```
$env:GROQ_API_KEY = "your-key-here"
```

To make it permanent, set it as a Windows environment variable
(search "Edit environment variables for your account" in the Start menu).

## 2. Install Python dependencies

```
pip install -r requirements.txt
```

PyAudio sometimes fails to install directly on Windows. If it errors out:

```
pip install pipwin
pipwin install pyaudio
```

## 3. Make her yours

Open `personality.py` and rewrite `BASE_PERSONA`. This is the single most
important file - it's the closest thing to who she actually is.

Open `config.py` if you want to change her voice. Run this to see all options:

```
edge-tts --list-voices
```

## 4. Run her

```
python main.py
```

Talk normally - she starts recording once she hears your voice and stops
once you go quiet. Say something with "look" or "check this out" in it and
she'll glance at your webcam before replying. She'll also occasionally speak
up on her own at random intervals.

## What's here

| File | Purpose |
|------|---------|
| `personality.py` | Who she is, mood/memory folded into system prompt |
| `memory.py` | Journal of impressions and persistent mood |
| `brain.py` | Groq API for reasoning, vision, and journal summarization |
| `ears.py` | VAD-based mic recording + Whisper transcription |
| `mouth.py` | edge-tts speech with mid-sentence interrupt support |
| `eyes.py` | Single webcam frame capture on demand |
| `hands.py` | Deterministic OS actions (open app, write file, search) |
| `scheduler.py` | Randomized proactive check-in timing |
| `main.py` | Main event loop tying everything together |
