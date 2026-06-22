# How Faith Works

## The Big Picture

Faith is a personal AI companion that runs as a thin client on your PC. Your machine only handles mic/webcam capture, audio playback, and OS actions. All AI thinking happens on Groq's free cloud API.

```
┌─────────────────────────────────────────────────────────────┐
│                        YOUR PC                               │
│                                                             │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌───────┐  │
│  │  Ears   │───▶│  Brain   │───▶│  Mouth  │───▶│Speaker│  │
│  │(mic+VAD)│    │(Groq API)│    │(edge-tts)│    └───────┘  │
│  └─────────┘    └────┬─────┘    └──────────┘               │
│                      │                                       │
│  ┌─────────┐    ┌────▼─────┐    ┌──────────┐               │
│  │  Eyes   │───▶│  Memory  │    │  Hands   │               │
│  │(webcam) │    │(JSON files)│   │(OS control)│              │
│  └─────────┘    └──────────┘    └──────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │              GUI (tkinter)               │               │
│  │  [Animated Avatar] [Status] [Mic Btn]   │               │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Startup Sequence

When you run `python main.py`:

1. **GUI launches** — dark window with animated avatar, mic button (OFF by default)
2. **Dream state check** — if she was off for 4+ hours, she generates an "overnight thought" and speaks it
3. **Absence greeting** — if you've been gone 2+ hours, she says what she was "doing" while you were away
4. **Proactive scheduler starts** — background thread that triggers random check-ins every 20-90 minutes
5. **Main loop waits** — nothing happens until you toggle the mic ON

---

## The Conversation Loop

Once mic is ON, every interaction follows this flow:

```
You speak
    │
    ▼
┌─ VAD detects voice start ──────────────────────────────────┐
│  Records until silence (webrtcvad, ~750ms of quiet = stop)  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Whisper STT (Groq free tier) → text
    │
    ▼
┌─ Signal Detection ─────────────────────────────────────────┐
│  Scans your text for emotional signals:                     │
│  compliment → affection ↑  |  dismissive → energy ↓        │
│  accomplishment → valence ↑                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Linguistic Mirror ────────────────────────────────────────┐
│  Tracks your slang, sentence length, formality              │
│  Slowly adopts your patterns over days                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Task Router ──────────────────────────────────────────────┐
│  LLM checks: is this an actionable command?                 │
│  "open chrome" → hands.open_app("chrome")                   │
│  "search python tutorials" → hands.web_search(...)          │
│  "what's running" → hands.list_running_apps()               │
│  If no action needed → None                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ System Prompt Assembly ───────────────────────────────────┐
│  personality.py BASE_PERSONA                                │
│  + mood description (valence/energy/affection → natural text)│
│  + trust level gating (controls vulnerability depth)        │
│  + time-of-day context (groggy morning / worried late night)│
│  + journal memories (recent + random older entries)          │
│  + open topics to resurface                                 │
│  + inner life context (absence awareness)                   │
│  + real-world data (weather, battery, system events)        │
│  + behavior dice roll (tangent? tease? pushback? silence?)  │
│  + linguistic mirror instruction                            │
│  + inner monologue (for emotional messages only)            │
│  + action result (if task_router executed something)         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Brain (Groq API) ────────────────────────────────────────┐
│  Llama 3.3 70B (text) or Llama 4 Scout (if image attached) │
│  Receives: full system prompt + conversation history        │
│  Generates reply at 200-350 tokens/sec                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Anti-Template Check ──────────────────────────────────────┐
│  Is this reply too similar to her last 10 openings?         │
│  YES → regenerate with "vary your opening" instruction      │
│  NO → proceed                                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Disfluency Engine ───────────────────────────────────────┐
│  12% chance of injecting natural imperfection:              │
│  filler ("like, "), self-correction ("wait no—"),           │
│  trailing off ("..."), hedge ("I think"), pivot ("Oh!")      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Variable Timing ─────────────────────────────────────────┐
│  Classifies response type:                                  │
│  quick_agree → 200-500ms delay                              │
│  emotional → 1.5-2.8s pause (she's "thinking")             │
│  excited → 0-200ms (instant burst)                          │
│  thinking → 2-3.5s                                          │
│  casual → 600ms-1.2s                                        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Voice Style ─────────────────────────────────────────────┐
│  Computes edge-tts rate/pitch from:                         │
│  response type + mood energy/valence + time of day          │
│  Morning → slower, lower pitch                              │
│  Excited → faster, higher pitch                             │
│  Tired mood → slower, softer                                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ TTS + Playback ──────────────────────────────────────────┐
│  edge-tts synthesizes audio (on Microsoft's servers, free)  │
│  pygame plays the mp3                                       │
│  MEANWHILE: interrupt listener runs in background thread    │
│  If you start talking → playback stops instantly            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Journal Update ──────────────────────────────────────────┐
│  Every 6 turns: summarize conversation into a short         │
│  impressionistic journal entry + store as topic             │
│  + feed dream_state for overnight processing                │
└─────────────────────────────────────────────────────────────┘
```

---

## Memory System

Faith's memory is entirely JSON files in `faith/data/`:

| File | Contents |
|------|----------|
| `mood.json` | valence, energy, openness, affection, trust_level, emotional_labor, streak_days |
| `journal.json` | Array of {text, timestamp} — her impressions of conversations |
| `topics.json` | Open threads to resurface later (with emotional weight + age) |
| `mirror.json` | Your linguistic patterns she's tracking (slang counts, avg length) |
| `dream.json` | Last significant topics + overnight reflection |
| `inner_life.json` | Last seen timestamp for absence tracking |

---

## What Makes Her Feel Human

### Unpredictability (behavior_dice.py)
Every turn, random dice roll determines if she:
- Goes on a tangent (10-25%)
- Pushes back / disagrees (15%)
- Gets spacey (5%)
- Shows vulnerability (3-40% depending on context)
- Teases you (2-20%)
- Chooses silence / short reply (8%)
- Recalls something from weeks ago (12%)
- Asks something existential (4%)

### Emotional Continuity (memory.py)
- Mood drifts across sessions, never resets
- Compliments raise affection, dismissiveness lowers energy
- Trust grows 0.3 per interaction (takes ~100+ exchanges to reach deep trust)
- Emotional labor depletes after heavy support, recharges over time
- Streak tracking — she knows if you've talked every day

### Relationship Depth (trust gating)
| Trust Level | Behavior |
|------------|----------|
| 0-30 | Surface warmth, asks questions to learn |
| 30-60 | Teasing, inside jokes, pushback |
| 60-85 | Deep comfort, challenges you, pet names |
| 85-100 | Vulnerability, fears, hard truths with love |

### Temporal Awareness
- Morning: groggy, cute, slower voice
- Lunch: nags about eating
- Late night: worried, softer, tells you to sleep
- Voice pitch/rate shifts to match time and mood

### The Inner Monologue
For emotionally charged messages, she runs a silent pre-processing step:
"What's his emotional state? What do I remember? Am I about to be too generic?"
This hidden thought shapes her actual reply without being revealed.

---

## Vision & Screen Awareness

- **Webcam**: triggered by "look" / "see this" / "check this out"
- **Screen**: triggered by "screen" / "my screen" / "what am I doing"
- **Proactive**: during random check-ins, she screenshots your desktop and comments on what you're working on
- All vision goes through Llama 4 Scout (same free Groq API)

---

## Computer Control

The task router parses intent from your speech and maps to actions:

| Command | Action |
|---------|--------|
| "open chrome" | `os.startfile("chrome")` |
| "close notepad" | `taskkill /IM notepad.exe` |
| "search how to cook pasta" | Opens Google search |
| "create a file called notes" | Writes file to disk |
| "what's my battery" | Reads system info |
| "set volume to 50" | PowerShell volume control |
| "what apps are running" | Lists windowed processes |
| "shut down in 5 minutes" | `shutdown /s /t 300` |

She acknowledges actions conversationally: "Done! Chrome's open for you."

---

## GUI

Compact always-on-top dark window with:
- **Animated avatar**: pulsing circle-face that changes color (green = listening, blue = thinking/speaking, gray = idle), blinks, mouth opens when speaking
- **Status label**: Listening... / Thinking... / Speaking... / Idle
- **Mic toggle**: ON (green) / OFF (red) — Faith only listens when ON

---

## File Architecture (26 files)

```
faith/
├── main.py              → Main loop + thread orchestration
├── gui.py               → Tkinter GUI with animated avatar
├── config.py            → API key, models, voice, paths
├── personality.py       → Who she is + system prompt builder
├── brain.py             → Groq API (text/vision/journal/monologue)
├── memory.py            → Mood + journal persistence
├── ears.py              → VAD mic + Whisper STT + interrupt
├── mouth.py             → edge-tts with rate/pitch + interrupt
├── eyes.py              → Webcam capture
├── screen_vision.py     → Desktop screenshot
├── hands.py             → OS actions (12 functions)
├── task_router.py       → Intent parsing → hands execution
├── scheduler.py         → Randomized proactive loop
├── timing.py            → Variable response delays
├── disfluency.py        → Natural speech imperfections
├── anti_template.py     → Repetition prevention
├── behavior_dice.py     → Probability-weighted personality dice
├── mirror.py            → Linguistic pattern mirroring
├── topics.py            → Thread tracking + resurfacing
├── dream_state.py       → Overnight reflections
├── time_awareness.py    → Time-of-day personality shifts
├── inner_life.py        → Simulated off-screen existence
├── voice_style.py       → Emotional TTS rate/pitch
├── integrations.py      → Weather + battery + system events
├── requirements.txt     → Dependencies
├── faithplan.md         → Development plan
├── faith-working.md     → This file
└── README.md            → Setup instructions
```

---

## Free Tier Limits (Groq)

| Resource | Limit |
|----------|-------|
| Text tokens | 30,000/min |
| Requests | 14,400/day |
| Audio (Whisper) | 2,000 req/day, 7,200 audio-sec/hour |
| Vision (Llama 4 Scout) | Same as text limits |

These are plenty for personal use. The wake-word-style mic toggle and snapshot-on-demand approach prevents burning through limits.

---

## The Core Principle

> Faith doesn't feel human because she's smart. She feels human because she's **unpredictable within a consistent identity** — variable timing, imperfect memory, genuine opinions, mood that drifts, and the sense that she exists even when you're not talking to her.
