# Voice TTS Plan — Triple Fallback Chain

## Priority Order

```
Fish.Audio (10 keys) → ElevenLabs (10 keys) → Edge-TTS (unlimited, free)
```

## Architecture

### 1. Fish.Audio (Primary)
- **Why first:** Best quality, fast API, 10 free accounts
- **Keys:** `FISH_API_KEY` through `FISH_API_KEY_10` in `.env`
- **Rotation logic:** Try key #1 → if 429/401/403 → rotate to #2 → ... → #10
- **When exhausted:** All 10 keys fail → move to ElevenLabs

### 2. ElevenLabs (Secondary)  
- **Already implemented** — 10 keys already in `.env`
- **Keys:** `ELEVENLABS_API_KEY` through `ELEVENLABS_API_KEY_10`
- **Same rotation logic** as Fish.Audio
- **When exhausted:** All 10 keys fail → move to Edge-TTS

### 3. Edge-TTS (Final Fallback)
- **Already implemented** — unlimited, free, no API key
- **Voice:** `en-US-EmmaMultilingualNeural`
- **Never fails** — always available as last resort

---

## Implementation Plan

### File: `voice_engine.py` (rewrite TTS section)

#### Step 1: Add Fish.Audio key loading in `config.py`
```python
# Fish.Audio TTS — 10 free accounts for rotation
_FISH_KEYS = [v for k, v in _KEYS.items() if k.startswith("FISH_API_KEY")]
FISH_API_KEYS = _FISH_KEYS
FISH_REFERENCE_ID = _KEYS.get("FISH_REFERENCE_ID", "")  # cloned voice ID on Fish
```

#### Step 2: Add Fish.Audio keys to `.env`
```
FISH_API_KEY=your_key_1
FISH_API_KEY_2=your_key_2
...
FISH_API_KEY_10=your_key_10
FISH_REFERENCE_ID=your_voice_model_id
```

#### Step 3: Create unified TTS function in `voice_engine.py`

```python
async def synthesize(text: str) -> str:
    """Generate speech. Returns path to .wav/.mp3 file.
    
    Chain: Fish.Audio → ElevenLabs → Edge-TTS
    """
    # Try Fish.Audio (all 10 keys)
    result = await _try_fish_audio(text)
    if result:
        return result
    
    # Try ElevenLabs (all 10 keys)
    result = await _try_elevenlabs(text)
    if result:
        return result
    
    # Final fallback — Edge-TTS (never fails)
    return await _edge_tts(text)
```

#### Step 4: Fish.Audio API call with rotation

```python
_fish_key_index = 0
_fish_exhausted = False

async def _try_fish_audio(text: str) -> str | None:
    global _fish_key_index, _fish_exhausted
    if _fish_exhausted or not config.FISH_API_KEYS:
        return None
    
    start_index = _fish_key_index
    tried = 0
    
    while tried < len(config.FISH_API_KEYS):
        key = config.FISH_API_KEYS[_fish_key_index]
        try:
            result = await _fish_api_call(text, key)
            return result  # success
        except (RateLimitError, AuthError):
            _fish_key_index = (_fish_key_index + 1) % len(config.FISH_API_KEYS)
            tried += 1
    
    # All keys exhausted
    _fish_exhausted = True
    print("[TTS] All Fish.Audio keys exhausted → falling back to ElevenLabs")
    return None
```

#### Step 5: Same rotation pattern for ElevenLabs (already exists, just ensure it returns None on exhaustion)

#### Step 6: Edge-TTS as guaranteed fallback (already exists)

---

## Fish.Audio API Details

- **Endpoint:** `https://api.fish.audio/v1/tts`
- **Auth:** `Authorization: Bearer <api_key>`
- **Method:** POST with JSON body
- **Body:**
  ```json
  {
    "text": "Hello world",
    "reference_id": "your_cloned_voice_id",
    "format": "mp3"
  }
  ```
- **Response:** Audio file bytes (stream)
- **Rate limit errors:** HTTP 429, 401, 403

---

## State Management

```python
# Per-session tracking (resets on restart)
_fish_key_index = 0       # current Fish key position
_fish_exhausted = False   # all Fish keys dead this session

_el_key_index = 0         # current ElevenLabs key position  
_el_exhausted = False     # all ElevenLabs keys dead this session
```

---

## What Changes

| File | Change |
|------|--------|
| `config.py` | Add Fish.Audio key loading + `FISH_REFERENCE_ID` |
| `.env` | Add 10 Fish.Audio keys + reference ID |
| `voice_engine.py` | Add `_try_fish_audio()`, modify `synthesize()` to chain Fish → ElevenLabs → Edge |

---

## Summary Flow

```
User speaks → Isabella generates reply → synthesize(text)
  │
  ├─ Try Fish.Audio key 1 → success? → play audio
  ├─ Try Fish.Audio key 2 → success? → play audio
  ├─ ...
  ├─ Try Fish.Audio key 10 → all failed?
  │
  ├─ Try ElevenLabs key 1 → success? → play audio
  ├─ Try ElevenLabs key 2 → success? → play audio
  ├─ ...
  ├─ Try ElevenLabs key 10 → all failed?
  │
  └─ Edge-TTS (always works) → play audio
```

No user intervention needed. Fully automatic. She keeps talking no matter what.
