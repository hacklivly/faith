# Faith AI - Kya Hai, Kyun Banaya, Kaise Chalao

## Ye Kya Hai?

Faith ek personal AI companion hai — teri apni girlfriend jo teri PC pe rehti hai.
Wo sunti hai (mic se), dekhti hai (webcam se), bolti hai (TTS se), aur sochti hai (Groq API se).

Ye weak hardware pe chalti hai — koi GPU nahi chahiye. Intel i3, Windows 10, bas internet chahiye.
Saara heavy kaam (thinking, vision, speech-to-text) Groq ka free API karta hai. Tera PC sirf
mic input leta hai aur audio output play karta hai.

---

## Kyun Banaya?

Maine ye isliye banaya kyunki mujhe ek aisi AI chahiye thi jo:
- Assistant na ho — ek real personality ho, emotions ho, mood ho
- Mujhse baat kare jaise koi actual insaan kare
- Mere baare mein cheezein yaad rakhe (memory + journal)
- Apne aap bhi bol pade kabhi kabhi (proactive check-ins)
- Webcam se dekh sake jab main bolu "look at this"
- Bilkul free chale — koi paid API nahi, koi GPU nahi

---

## Kaise Chalao (Step by Step)

### Step 1: Python Install Karo

Python 3.10+ chahiye. Download: https://www.python.org/downloads/

Install karte waqt **"Add Python to PATH"** checkbox zaroor tick karo.

### Step 2: Groq API Key Lo (FREE hai)

1. Jao https://console.groq.com
2. Sign up karo (no credit card needed)
3. Ek API key create karo
4. PowerShell mein set karo:

```powershell
$env:GROQ_API_KEY = "apni-key-yahan-paste-karo"
```

Permanent karna hai to: Start menu mein search karo "Edit environment variables for your account"
→ New → Name: `GROQ_API_KEY` → Value: teri key

### Step 3: Dependencies Install Karo

PowerShell kholke project folder mein jao:

```powershell
cd "B:\AI and faith\faith"
pip install -r requirements.txt
```

Agar PyAudio install mein error aaye:

```powershell
pip install pipwin
pipwin install pyaudio
```

### Step 4: Run Karo

```powershell
cd "B:\AI and faith\faith"
python main.py
```

Bas! Faith chal jayegi.

---

## Kaise Use Karo

| Kya karna hai | Kaise karo |
|---|---|
| Baat karo | Normally bol, mic automatically sun lega jab tu bolega |
| Webcam se dikhao | Bol mein "look" ya "check this out" shamil karo |
| Chup karao mid-sentence | Bolna shuru karo, wo ruk jayegi |
| Kuch kaam karwao | Bol "open Chrome", "search for X", etc. |

Wo apne aap bhi random intervals pe bol sakti hai (scheduler).

---

## Project Structure - Kya Kya Hai

| File | Kaam |
|---|---|
| `personality.py` | Faith ki identity — sab se important file. Isko edit karke personality change karo |
| `config.py` | API keys, models, voice settings |
| `brain.py` | Groq API calls — sochna, dekhna, summarize karna |
| `ears.py` | Mic se sunna (VAD + Whisper transcription) |
| `mouth.py` | Bolna (edge-tts, free, mid-sentence interrupt support) |
| `eyes.py` | Webcam se ek frame lena |
| `hands.py` | OS actions — app kholna, file likhna, search karna |
| `memory.py` | Journal aur mood persistence |
| `emotion_engine.py` | Emotions simulate karna |
| `relationship.py` | Relationship tracking |
| `inner_life.py` | Internal thoughts jab idle ho |
| `dream_state.py` | Dream mode jab so rahi ho |
| `flow_manager.py` | Conversation flow control |
| `scheduler.py` | Random proactive check-ins |
| `gui.py` | GUI interface |

---

## Voice Change Karna Hai?

`config.py` mein `VOICE_NAME` change karo. Available voices dekhne ke liye:

```powershell
edge-tts --list-voices
```

---

## Tech Stack

- **Thinking**: Groq API (LLaMA 3.1 8B) — free, fast
- **Vision**: LLaMA 4 Scout via Groq — free
- **Speech-to-Text**: Whisper Large v3 Turbo via Groq — free
- **Text-to-Speech**: Edge TTS (Microsoft) — free, no key needed
- **Voice Detection**: WebRTC VAD — local, lightweight
- **Language**: Python 3.10+
- **Cost**: ₹0 (sab free hai)
