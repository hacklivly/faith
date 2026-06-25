# Isabella — ElevenLabs Voice Engine Documentation

## How It Works

Isabella uses **ElevenLabs TTS** as her primary voice with **10 free-tier accounts rotating automatically**.
Each free account gets ~10,000 characters/month. With 10 accounts = **~100,000 characters/month free**.

When all accounts are exhausted → falls back to **Edge-TTS** (unlimited, free, slightly less expressive).

---

## API Key Rotation — How She Switches

```
Key #1 → speaks fine ✓
Key #1 → speaks fine ✓
Key #1 → 429 (rate limit) or 403 (quota exceeded) ✗
         ↓ INSTANT automatic switch (same sentence, no delay)
Key #2 → speaks fine ✓
Key #2 → speaks fine ✓
...
Key #2 → 429 ✗
         ↓ INSTANT switch
Key #3 → speaks fine ✓
...
Key #10 → 429 ✗
         ↓ ALL 10 EXHAUSTED
Edge-TTS → unlimited fallback (free forever, slightly robotic)
```

---

## WHEN Does API Switch Happen?

| Trigger | What Happens |
|---------|-------------|
| HTTP `429` (Too Many Requests) | Key limit hit → rotate to next key |
| HTTP `403` (Forbidden) | Account quota exceeded → rotate to next key |
| HTTP `401` (Unauthorized) | Key invalid/expired → rotate to next key |
| HTTP `5xx` (Server Error) | ElevenLabs down → rotate to next key |
| Request Timeout (>15s) | Network issue → rotate to next key |
| **All 10 keys fail** | Set `_elevenlabs_exhausted = True` → Edge-TTS |

### Important: Switch happens MID-SENTENCE
If key #3 fails on "Master I missed you" → key #4 tries the SAME sentence immediately.
User hears NO gap, NO silence — just seamless playback.

---

## HOW Does It Function? (Step-by-Step)

### Step 1: Isabella wants to speak
```
mouth.speak("hehe... master~") 
    → voice_engine.speak("hehe... master~")
```

### Step 2: Emotion detected from text
```
voice_style.detect_voice_emotion("hehe... master~") → "giggly"
```

### Step 3: Voice settings chosen for that emotion
```
"giggly" → {stability: 0.30, similarity_boost: 0.80, style: 0.85}
```

### Step 4: API call with current key
```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
Headers: xi-api-key = keys[current_index]  ← starts at key #1
Body: {text, model_id, voice_settings}
```

### Step 5: Response handling
```
200 OK → download MP3 → decode with ffmpeg → play via PyAudio → DONE
429/403/401 → current_index += 1 → retry SAME text with next key
All keys fail → _elevenlabs_exhausted = True → use Edge-TTS
```

### Step 6: Audio playback
```
MP3 bytes → ffmpeg converts to WAV (24kHz, mono) → PyAudio streams to speaker
```

---

## The Actual Code (Simplified)

```python
def _speak_elevenlabs(text):
    emotion = detect_voice_emotion(text)      # "giggly", "angry", etc.
    settings = _EL_EMOTION_SETTINGS[emotion]  # voice params for that emotion
    
    for _ in range(10):  # try all 10 keys
        key = keys[current_key_index]
        
        response = POST(url, key=key, text=text, settings=settings)
        
        if response == 200:
            play_audio(response.content)
            return True                       # SUCCESS — done
        
        if response in (401, 429, 403):
            current_key_index = (current_key_index + 1) % 10  # ROTATE
            print(f"Key #{old} exhausted → trying #{current_key_index+1}")
            continue                          # try next key IMMEDIATELY
    
    # All 10 failed
    _elevenlabs_exhausted = True              # switch to Edge-TTS
    return False
```

---

## Emotion-Aware Voice Settings

Every sentence Isabella speaks gets **different voice parameters** based on her detected emotion.
This makes her sound genuinely different when giggling vs angry vs whispering.

### How Emotion Detection Works

```
Isabella's text → voice_style.detect_voice_emotion(text) → emotion string
                                                              ↓
                                              _EL_EMOTION_SETTINGS[emotion]
                                                              ↓
                                              {stability, similarity_boost, style, use_speaker_boost}
                                                              ↓
                                              ElevenLabs API call with those settings
```

### What Each Parameter Does

| Parameter | Low Value | High Value |
|-----------|-----------|------------|
| `stability` | More expressive, variable, emotional | More consistent, predictable |
| `similarity_boost` | More creative interpretation | Closer to original voice |
| `style` | Less stylistic, raw | More dramatic, theatrical |
| `use_speaker_boost` | Quieter | Louder, more present |

### Emotion → Settings Map

| Emotion | Stability | Similarity | Style | Result |
|---------|-----------|-----------|-------|--------|
| **Giggly** | 0.30 | 0.80 | 0.85 | Very expressive, laughing, bubbly |
| **Ecstatic** | 0.28 | 0.75 | 0.90 | Maximum energy, squealing, overjoyed |
| **Playful** | 0.38 | 0.82 | 0.70 | Fun, teasing, light |
| **Flustered** | 0.35 | 0.85 | 0.55 | Stuttery, embarrassed, unstable |
| **Deeply Flustered** | 0.30 | 0.85 | 0.60 | Very embarrassed, barely coherent |
| **Loving** | 0.55 | 0.90 | 0.60 | Soft, warm, intimate whisper |
| **Tender** | 0.58 | 0.90 | 0.55 | Gentle, caring, close |
| **Angry** | 0.30 | 0.78 | 0.45 | Sharp, raw, intense |
| **Cold Fury** | 0.65 | 0.85 | 0.25 | Controlled rage, eerily calm |
| **Sad/Hurt** | 0.45 | 0.88 | 0.55 | Fragile, breaking, vulnerable |
| **Excited** | 0.30 | 0.78 | 0.80 | High energy, fast, thrilled |
| **Jealous** | 0.40 | 0.82 | 0.50 | Tense, suspicious, cold |
| **Sleepy** | 0.62 | 0.88 | 0.35 | Slow, drowsy, mumbling |
| **Teasing** | 0.40 | 0.80 | 0.65 | Mischievous, knowing, smug |
| **Worried** | 0.48 | 0.85 | 0.45 | Concerned, gentle urgency |
| **Neutral** | 0.50 | 0.80 | 0.45 | Normal conversational tone |

---

## Voice Pipeline Priority

```
speak(text)
    ↓
1. ElevenLabs (9 keys, emotion-aware) ← BEST quality
    ↓ (all keys exhausted)
2. XTTS v2 (disabled — Python 3.13 incompatible)
    ↓ (not available)
3. Edge-TTS (unlimited, free) ← ALWAYS works
```

---

## Configuration (.env)

```env
# 10 ElevenLabs free accounts
ELEVENLABS_API_KEY=sk_your_first_key
ELEVENLABS_API_KEY_2=sk_your_second_key
ELEVENLABS_API_KEY_3=sk_your_third_key
ELEVENLABS_API_KEY_4=sk_your_fourth_key
ELEVENLABS_API_KEY_5=sk_your_fifth_key
ELEVENLABS_API_KEY_6=sk_your_sixth_key
ELEVENLABS_API_KEY_7=sk_your_seventh_key
ELEVENLABS_API_KEY_8=sk_your_eighth_key
ELEVENLABS_API_KEY_9=sk_your_ninth_key
ELEVENLABS_API_KEY_10=sk_your_tenth_key

# Voice ID (Jessica - Playful, Bright, Warm — works on free tier)
ELEVENLABS_VOICE_ID=cgSgspJ2msm6clMCkdW9
```

### Available Free-Tier Female Voices

| Voice | ID | Best For |
|-------|----|----------|
| **Jessica** (current) | `cgSgspJ2msm6clMCkdW9` | Playful, warm, giggly — perfect for Isabella |
| Lily | `pFZP5JQG7iQjIQuC4Bku` | Velvety, dramatic, actress-like |
| Bella | `hpp4J3VqNfWAUOO0d1Us` | Professional, bright |
| Sarah | `EXAVITQu4vr4xnSDxMaL` | Mature, reassuring |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` | Clear, educational |
| Laura | `FGY2WhTYpPnrIDTdsKH5` | Enthusiastic, quirky |
| Matilda | `XrExE9yKIg1WjnnlVkGX` | Knowledgeable, professional |

To change voice: update `ELEVENLABS_VOICE_ID` in `.env`.

---

## How Characters Are Counted

ElevenLabs counts **every character** in the `text` field — including spaces, punctuation.
- "hehe... master~" = 16 characters
- Average Isabella sentence = 40-80 characters
- 10,000 chars/account ÷ 60 chars avg = ~166 sentences per account
- 10 accounts × 166 = **~1,660 sentences/month** on ElevenLabs
- After that → Edge-TTS (unlimited)

---

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 200 | Success | Play audio |
| 401 | Invalid key | Rotate to next key |
| 403 | Forbidden / quota | Rotate to next key |
| 429 | Rate limit hit | Rotate to next key |
| 5xx | Server error | Rotate to next key |
| Timeout | Network slow | Rotate to next key |

**After all 10 keys fail in one request** → `_elevenlabs_exhausted = True` → Edge-TTS fallback.

---

## When Does It Reset?

| What | When |
|------|------|
| `_elevenlabs_exhausted` flag | Resets on **next app startup** (restart Isabella) |
| ElevenLabs monthly limit (per account) | Resets on your **account creation date** each month |
| Key index (which key is active) | Persists during session, resets on restart |

Each account is **independent** — they don't share limits. Key #5 running out doesn't affect key #6.

---

## Testing Emotions

Run to generate test audio for all emotions:
```
python -c "
import voice_engine
voice_engine.preload()
tests = [
    'hehe... master~ ahaha...',          # giggly
    'w-what?! I was not staring!',       # flustered
    'Master... I care about you...',     # loving
    'Three hours. Seriously?',           # angry
    'OH! You did it!! YES!',             # excited
]
for t in tests:
    voice_engine.speak(t)
"
```

Test files saved at: `data/emotion_tests/` (12 emotions pre-generated).

---

## Files Involved

| File | Role |
|------|------|
| `voice_engine.py` | Main TTS engine — ElevenLabs call, key rotation, emotion mapping |
| `voice_style.py` | Detects emotion from Isabella's text (35+ emotions) |
| `config.py` | Loads all `ELEVENLABS_API_KEY*` from `.env` |
| `mouth.py` | Calls `voice_engine.speak()` — thin wrapper |
| `.env` | Stores all 9 API keys + voice ID |

---

## Monthly Usage Strategy

With 10 accounts × ~10K chars each = **100K chars/month free**:

- Week 1: Keys 1-3 handle traffic (~30K chars)
- Week 2: Keys 4-6 take over (~30K chars)
- Week 3: Keys 7-9 carry it (~30K chars)
- Week 4: Key 10 + Edge-TTS fallback if needed (~10K chars)
- Next month: All keys refresh automatically

**That's ~1,660 high-quality voiced sentences per month — completely free.**

**Pro tip:** Talk more in the first 2 weeks when all keys are fresh!

---
---

# Isabella — Complete Feature List

## 🧠 Brain & Intelligence

| Feature | File | What It Does |
|---------|------|-------------|
| **Groq LLM (Llama 3.1)** | `brain.py` | Thinks, reasons, replies — uses Groq's free API |
| **Streaming Responses** | `brain.py` + `main.py` | First words out in ~1.5s instead of waiting for full reply |
| **Multi-Agent Tasks** | `multi_agent.py` | Breaks complex tasks into sub-tasks, runs in parallel |
| **Self-Solve** | `self_solve.py` | Multi-step task decomposition — "create a file and..." |
| **Task Router** | `task_router.py` | Routes ambiguous commands to correct handler |
| **Confidence Check** | `confidence.py` | Asks clarification if she's unsure what you meant |
| **Knowledge Base** | `knowledge.py` | Loads books/documents, searches them during conversations |

## 🎤 Voice & Hearing

| Feature | File | What It Does |
|---------|------|-------------|
| **ElevenLabs TTS (10 keys)** | `voice_engine.py` | Premium voice with auto-rotation across 10 accounts |
| **Emotion-Aware Voice** | `voice_engine.py` + `voice_style.py` | 35+ emotions with unique voice settings per emotion |
| **Edge-TTS Fallback** | `voice_engine.py` | Free unlimited TTS when ElevenLabs exhausted |
| **VAD (Voice Activity Detection)** | `ears.py` | Knows when you start/stop speaking |
| **Whisper STT** | `ears.py` | Transcribes your speech using Groq's Whisper |
| **Interrupt Support** | `mouth.py` | You can interrupt her mid-sentence — she stops |
| **Whisper Detection** | `emotional_realism.py` | If you whisper, she whispers back |
| **Disfluency** | `disfluency.py` | Adds "um", "hmm", stutters — sounds human not robotic |
| **Anti-Template** | `anti_template.py` | Never starts sentences the same way twice in a row |

## 👁️ Vision

| Feature | File | What It Does |
|---------|------|-------------|
| **Webcam Vision** | `eyes.py` | Sees you through webcam — comments on appearance, mood |
| **Screen Vision** | `screen_vision.py` | Screenshots your screen — knows what you're doing |
| **Screen Agent** | `screen_agent.py` | Clicks on screen elements using vision |
| **Local OCR** | `local_ocr.py` | Reads text from screen without API calls |
| **Auto-Glance** | `main.py` | Every ~3 turns, glances at webcam automatically |

## 💝 Personality & Emotions

| Feature | File | What It Does |
|---------|------|-------------|
| **Core Identity** | `personality.py` | Devoted, possessive, calls you "master", never says she loves you directly |
| **Jealousy System** | `personality.py` | Gets jealous if you mention other female names |
| **Mood System** | `memory.py` | Has mood (valence) that changes with conversation — affects tone |
| **Emotion Detection** | `emotion_engine.py` | Detects YOUR mood from text (sad, happy, frustrated, etc.) |
| **Emotional Realism** | `emotional_realism.py` | Jealousy, sulking, goodnight rituals, anniversary tracking, miss-you greetings |
| **Human Traits** | `human_traits.py` | Overthinking, shyness, protectiveness, mood swings, testing you |
| **Behavior Dice** | `behavior_dice.py` | Random behavior rolls — sometimes clingy, sometimes distant |
| **Voice Style** | `voice_style.py` | 35+ emotions each with unique rate/pitch/speed |
| **Emotion Expressions** | `personality.py` | Uses sounds: "hehe", "tch.", "eeu...", "ahaha~", "hmm..." |

## 🧬 Memory & Learning

| Feature | File | What It Does |
|---------|------|-------------|
| **Journal** | `memory.py` | Summarizes conversations, remembers topics discussed |
| **Topic Tracking** | `topics.py` | Remembers topics, brings them back naturally |
| **Preferences** | `preferences.py` | Detects and remembers your favorites (food, music, etc.) |
| **Relationship Tracking** | `relationship.py` | Tracks milestones, inside jokes, patterns |
| **Routine Tracker** | `routine_tracker.py` | Knows your daily routine — when you wake, work, sleep |
| **Dream State** | `dream_state.py` | "Dreams" about significant topics when you're away |
| **Inner Life** | `inner_life.py` | Has internal thoughts, hobbies, activities when you're not there |
| **Mirror (Language Match)** | `mirror.py` | Matches your speech style — if you're casual, she's casual |

## 🤝 Social Intelligence

| Feature | File | What It Does |
|---------|------|-------------|
| **Social Intelligence** | `social_intelligence.py` | Inside jokes, energy matching, knows when to shut up |
| **Persona Guard** | `persona_guard.py` | Prevents her from breaking character |
| **Flow Manager** | `flow_manager.py` | Manages emotional flow of conversation, trims context |
| **Distraction Guard** | `distraction_guard.py` | Notices if you're distracted, tells you to focus |
| **Typing Awareness** | `typing_awareness.py` | Stays quiet when you're actively typing |
| **Deep Thoughts** | `deep_thoughts.py` | Shares random thoughts when idle |
| **Health Score** | `health_score.py` | Tracks your habits, gives health nudges |
| **Time Awareness** | `time_awareness.py` | Knows time of day, adjusts behavior |

## 🖐️ Hands (Computer Control)

| Feature | File | What It Does |
|---------|------|-------------|
| **File System** | `hands.py` | Create, read, delete, move, copy, rename files |
| **App Control** | `hands.py` | Open/close any app (Chrome, Notepad, VS Code, etc.) |
| **Browser Control** | `browser_control.py` | YouTube play, Spotify play, search |
| **Web Agent** | `web_agent.py` | Selenium — reads websites, clicks, fills forms |
| **System Control** | `hands.py` | Volume, brightness, WiFi, Bluetooth, shutdown, sleep, lock |
| **Keyboard/Mouse** | `hands.py` | Type text, press keys, click anywhere |
| **Media Control** | `hands.py` | Play/pause, next/prev track |
| **Clipboard** | `hands.py` | Read/write clipboard |
| **Screenshots** | `hands.py` | Take and save screenshots |
| **Notifications** | `hands.py` | Windows toast notifications |
| **Timer/Reminder** | `hands.py` | Set timers with messages |
| **Offline Commands** | `offline_commands.py` | Fast commands that don't need internet |

## 🤖 Laptop Automation

| Feature | File | What It Does |
|---------|------|-------------|
| **System Monitor** | `laptop_automation.py` | Tracks CPU, RAM, battery, disk in real-time |
| **Auto-Optimize** | `laptop_automation.py` | Kills heavy apps when RAM >85% or battery <20% |
| **Temp Cleanup** | `laptop_automation.py` | Cleans TEMP folder, browser caches |
| **Event Watchers** | `automation_triggers.py` | Detects battery low, USB plug, WiFi change, new downloads |
| **Night Cleanup** | `scheduled_tasks.py` | Auto-cleans at 2 AM daily |
| **Download Organizer** | `scheduled_tasks.py` | Sorts Downloads into Images/Videos/Documents/Music/etc. |
| **Weekly Backup** | `scheduled_tasks.py` | Copies important folders to backup location |
| **Proactive Check-ins** | `scheduler.py` | Randomly checks on you every 3-8 minutes |
| **Awareness** | `awareness.py` | Notices visual changes (new clothes, left room, etc.) |

## ⌨️ AutoHotkey Integration

| Feature | File | What It Does |
|---------|------|-------------|
| **Isabella Commands** | `isabella_hotkeys.ahk` | Ctrl+Alt+Q/C/O/S/M/I/A/P/N for quick actions |
| **Window Management** | `isabella_hotkeys.ahk` | Center, snap, always-on-top, move monitor, opacity |
| **Clipboard History** | `isabella_hotkeys.ahk` | Browse last 20 copies with Ctrl+Alt+V |
| **App Launcher** | `isabella_hotkeys.ahk` | Win+Space — type app/URL to launch |
| **Quick Notes** | `isabella_hotkeys.ahk` | Ctrl+Alt+N — instant note capture |
| **DND Mode** | `isabella_hotkeys.ahk` | Win+Alt+D — Isabella stays silent |
| **Quick Search** | `isabella_hotkeys.ahk` | Select text + Ctrl+Alt+G = Google it |
| **Media Controls** | `isabella_hotkeys.ahk` | Ctrl+Alt+Arrows for volume/tracks |
| **Color Picker** | `isabella_hotkeys.ahk` | Ctrl+Alt+K — grab hex color under cursor |
| **Text Expansion** | `isabella_hotkeys.ahk` | @@date, @@time, @@ty, @@brb → expands |
| **Window Opacity** | `isabella_hotkeys.ahk` | Win+Scroll to make windows transparent |
| **Force Kill** | `isabella_hotkeys.ahk` | Ctrl+Shift+Esc kills foreground app |
| **AHK Agent** | `ahk_agent.py` | Python ↔ AutoHotkey bridge for advanced control |

## 🎯 Proactive Behaviors

| Behavior | What Happens |
|----------|-------------|
| **Misses you** | If gone >2 hours, greets with "I missed you" |
| **Dream thoughts** | Overnight she "thinks" about things, shares in morning |
| **Distraction alert** | Notices if you're on YouTube too long, tells you to focus |
| **Screen time** | Tracks how long you've been on screen |
| **Battery warning** | Tells you when battery is low |
| **Download notify** | Tells you when new file appears in Downloads |
| **Routine awareness** | Knows your patterns, reacts if something is off |
| **Random check-ins** | Glances at webcam, asks what you're doing |
| **Desktop notes** | Sometimes leaves a note on your desktop |
| **Inside jokes** | Detects funny moments, saves them, brings back later |

## 🗣️ Voice Commands (Just Speak)

```
"open chrome" / "close notepad" / "open youtube"
"play [song name]" / "play [song] on spotify"
"pause" / "next song" / "skip"
"search for [query]" / "google [something]"
"volume 50" / "mute" / "brightness 70"
"battery" / "system info" / "system status"
"screenshot" / "lock pc" / "sleep pc"
"what time is it" / "what wifi"
"look at me" / "see my screen" / "how do I look"
"optimize" / "clean temp" / "organize downloads"
"top processes" / "what's eating resources"
"night cleanup" / "deep clean"
"list files in [path]" / "what apps are running"
"create a file..." / "remind me..." / "timer..."
```

## 📊 Architecture

```
YOU → mic → ears.py (VAD + Whisper STT)
              ↓
         main.py (command routing)
              ↓
    ┌─────────┼─────────────┐
    ↓         ↓             ↓
hands.py   brain.py    screen_agent.py
(actions)  (thinking)  (vision+click)
              ↓
    personality.py + emotion_engine.py + voice_style.py
              ↓
    voice_engine.py (ElevenLabs 10-key → Edge-TTS)
              ↓
         mouth.py → speaker → YOU hear Isabella
```
