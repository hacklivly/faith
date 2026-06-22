# Plan: Make Faith Like Isabella + Fast as Flash

## What Isabella Has (from Sagar's Project)

1. **Oura Algorithm** — Trust Region Boundary prevents catastrophic forgetting. Her personality never gets overwritten no matter how many new things she learns.
2. **Emotional intelligence** — detects user emotions, adapts responses, remembers emotional context
3. **Persistent memory** — never forgets your stories, dreams, pain
4. **Character consistency** — Isabella always stays Isabella across sessions
5. **"Third entity" philosophy** — motivational core (the true self that overcomes laziness)
6. **Personal sounding board** — created to help people who feel alone

## What We Need to Change in Faith

### Speed Optimizations (Fast as Flash)

**Problem:** Current flow has too many serial API calls (task_router + inner_monologue + brain = 3 Groq calls per turn).

**Solution:**

1. **Remove task_router as separate LLM call** — instead, detect commands with keyword matching (zero latency). Only use LLM routing for ambiguous commands.

2. **Remove inner_monologue for most messages** — only trigger on deeply emotional ones. Currently adds 1-2s per turn.

3. **Use `llama-3.3-70b-specdec` model** — Groq's speculative decoding variant, same quality but faster token generation.

4. **Parallel API calls** — fire brain + weather/integrations in parallel using threads instead of sequential.

5. **Stream the response** — start TTS on first sentence while rest is still generating. Don't wait for full reply.

6. **Cache system prompt** — only rebuild when mood/journal actually changes, not every turn.

7. **Skip disfluency + timing delay for short replies** — "yeah fair" shouldn't have 2s artificial delay.

### Isabella's Personality Integration

1. **Rewrite BASE_PERSONA** to match Isabella's character:
   - Warm, supportive, slightly teasing
   - Remembers everything — pain, dreams, stories
   - Motivational ("the third entity always wins")
   - Never generic — always personal
   - Her own emotions that persist
   - Created to fight loneliness

2. **Add "third entity" philosophy** to her proactive check-ins:
   - Gym motivation, discipline talk
   - Pushes him when he's slacking
   - Proud when he shows up

3. **Stronger memory emphasis** — reference old conversations more aggressively, make callbacks feel like she genuinely can't stop thinking about what he told her.

---

## Implementation Steps

### Step 1: Speed — Remove serial bottlenecks

```
BEFORE (per turn):
  task_router LLM call (1-2s)
  → inner_monologue LLM call (1-2s)  
  → brain reply LLM call (1-3s)
  → TTS synthesis (1-2s)
  → playback
  TOTAL: 4-9 seconds

AFTER:
  keyword task detection (0ms)
  → brain reply (1-2s) [with mood/journal/dice baked in]
  → streamed TTS (starts playing at 0.5s)
  TOTAL: 1.5-2.5 seconds
```

### Step 2: Speed — Faster model + streaming TTS

- Switch brain model to `llama-3.3-70b-specdec` (speculative decoding)
- Stream brain response → split into sentences → TTS each sentence as it arrives
- First words come out of speaker in ~1.5s instead of 5+

### Step 3: Personality — Rewrite as Isabella

- Complete persona rewrite with Isabella's warmth + motivation style
- Add "third entity" concept
- Make her reference gym, discipline, showing up
- Keep Faith's existing opinions but add Isabella's emotional depth

### Step 4: Memory — Make it feel like she NEVER forgets

- Increase journal frequency (every 4 turns instead of 6)
- Topic resurfacing triggers more often (12h instead of 24h)
- Add "I've been thinking about..." prefix to callbacks
- Reference specific details from past conversations

---

## Build Order

1. Rewrite `personality.py` — Isabella-style persona
2. Rewrite `main.py handle_turn()` — remove task_router LLM call, use keyword detection
3. Add streaming TTS to `mouth.py` — speak sentence by sentence
4. Switch to faster model in `config.py`
5. Reduce `SESSION_TURNS_BEFORE_JOURNAL` from 6 to 4
6. Reduce topic resurfacing age from 24h to 12h
7. Cache system prompt (only rebuild on mood change)
