"""
Faith - main loop.

Streaming pipeline: brain streams sentences → TTS speaks them immediately.
First words out of speaker in ~1.5s instead of 5+.

Integrates: emotion engine, persona guard, flow manager, streaming TTS.
"""
import threading
import time

import anti_template
import behavior_dice
import brain
import config
import disfluency
import dream_state
import ears
import emotion_engine
import eyes
import flow_manager
import gui
import inner_life
import integrations
import memory
import mirror
import mouth
import persona_guard
import personality
import relationship
import scheduler
import screen_vision
import timing
import topics
import voice_style

conversation = []
_turn_count = 0
import time
_last_activity_time = time.time()
_turn_lock = threading.Lock()


def current_system_prompt(extra: str = "") -> str:
    mood = memory.load_mood()
    journal = memory.recent_journal_texts()
    prompt = personality.build_system_prompt(mood, journal)
    prompt += topics.topics_for_prompt()
    prompt += inner_life.get_inner_life_prompt()
    prompt += integrations.get_context_for_prompt()
    prompt += flow_manager.get_emotional_context(conversation)
    prompt += relationship.get_pattern_insights()

    # Milestone check
    milestone = relationship.check_milestones()
    if milestone:
        prompt += milestone

    # Periodic identity reinforcement (every 5 turns)
    if _turn_count > 0 and _turn_count % 5 == 0:
        prompt += persona_guard.get_identity_reinforcement()

    prompt += extra
    return prompt


def speak_with_interrupt_listener(text: str):
    listener = threading.Thread(target=ears.listen_for_interrupt, daemon=True)
    listener.start()
    mouth.speak(text)


def maybe_update_journal():
    if len(conversation) >= config.SESSION_TURNS_BEFORE_JOURNAL:
        snippet = "\n".join(
            f"{m['role']}: {m['content']}" for m in conversation[-config.SESSION_TURNS_BEFORE_JOURNAL:]
        )
        result = brain.summarize_for_journal(snippet)
        memory.add_journal_entry(result["journal"])
        topics.add_topic(result["journal"])
        recent_topics = [e["text"] for e in memory.load_journal()[-3:]]
        dream_state.store_significant_topics(recent_topics)


def handle_turn(user_text: str, image_base64: str = None):
    global _turn_count, _last_activity_time
    _turn_count += 1
    _last_activity_time = time.time()

    conversation.append({"role": "user", "content": user_text})

    # Track linguistic patterns
    mirror.analyze(user_text)

    # Track relationship patterns
    relationship.record_interaction(user_text)

    # Fast keyword-based task detection (NO LLM call)
    action_result = _fast_task_detect(user_text)

    # Deep emotion detection (replaces old keyword matching)
    signals = emotion_engine.get_mood_signals(user_text)
    if signals:
        memory.update_mood(signals)

    # Roll behavior dice
    mood = memory.load_mood()
    user_vulnerable = emotion_engine.detect(user_text).get("vulnerability", 0) > 0.3
    dice_instruction = behavior_dice.roll(
        mood_valence=mood.get("valence", 0.6),
        user_was_vulnerable=user_vulnerable
    )

    # Build prompt with all context layers
    extra = dice_instruction + mirror.get_style_instruction()

    # Inner monologue ONLY for deeply emotional messages
    dominant_emo, intensity = emotion_engine.dominant_emotion(user_text)
    if intensity > 0.6 and dominant_emo in ("vulnerability", "sadness", "loneliness", "fear"):
        journal = memory.recent_journal_texts(n_recent=3, n_random_older=0)
        thoughts = brain.inner_monologue(user_text, mood, journal)
        extra += f"\n[Your private thoughts (never say aloud): {thoughts}]\n"

    if action_result:
        extra += f"\n[You just did: {action_result}. Mention it casually.]\n"

    prompt = current_system_prompt(extra)

    # Smart context trimming before sending to API
    trimmed_convo = flow_manager.trim_conversation(conversation)

    # Compute voice style before speaking
    mouth.set_style(voice_style.compute("", mood))

    # Start interrupt listener
    listener = threading.Thread(target=ears.listen_for_interrupt, daemon=True)
    listener.start()

    gui.set_status("Speaking...")

    if config.STREAM_SENTENCE_TTS and not image_base64:
        # STREAMING PIPELINE: brain streams → sentences → TTS speaks immediately
        sentence_gen = brain.get_reply_stream(prompt, trimmed_convo, image_base64)

        # Apply disfluency to first sentence only
        first_done = False

        def _processed_stream():
            nonlocal first_done
            for sentence in sentence_gen:
                if not first_done:
                    sentence = disfluency.add_disfluency(sentence)
                    first_done = True
                yield sentence

        reply = mouth.speak_streamed(_processed_stream())
    else:
        # Non-streaming for vision (image) requests
        reply = brain.get_reply(prompt, trimmed_convo, image_base64)

        # Persona drift check + correction
        if persona_guard.needs_correction(reply):
            reply = brain.get_reply(
                prompt + persona_guard.get_correction_prompt(),
                trimmed_convo, image_base64
            )

        # Anti-template check
        if anti_template.is_repetitive(reply):
            reply = brain.get_reply(
                prompt + "\n[Vary your opening — don't start the same way as recent messages.]",
                trimmed_convo, image_base64
            )

        reply = disfluency.add_disfluency(reply)
        speak_with_interrupt_listener(reply)

    anti_template.record(reply)
    conversation.append({"role": "assistant", "content": reply})
    print(f"faith: {reply}".encode('utf-8', errors='replace').decode('utf-8', errors='replace'))

    gui.set_status("Idle")
    maybe_update_journal()


def _fast_task_detect(text: str) -> str | None:
    """Fast keyword-based task routing — no LLM call needed."""
    import re
    import hands
    lower = text.lower()

    # --- OPEN WEBSITES ---
    # "open youtube" / "open youtube.com" / "go to google.com"
    web_patterns = [
        r'open\s+(https?://\S+)',
        r'open\s+(\S+\.com\S*)',
        r'open\s+(\S+\.org\S*)',
        r'open\s+(\S+\.net\S*)',
        r'open\s+(\S+\.io\S*)',
        r'go\s+to\s+(https?://\S+)',
        r'go\s+to\s+(\S+\.com\S*)',
        r'go\s+to\s+(\S+\.org\S*)',
    ]
    for pat in web_patterns:
        m = re.search(pat, lower)
        if m:
            return hands.open_website(m.group(1))

    # Common site names without .com
    site_map = {
        "youtube": "youtube.com",
        "google": "google.com",
        "gmail": "mail.google.com",
        "github": "github.com",
        "chatgpt": "chatgpt.com",
        "whatsapp": "web.whatsapp.com",
        "instagram": "instagram.com",
        "twitter": "twitter.com",
        "reddit": "reddit.com",
        "spotify": "open.spotify.com",
        "netflix": "netflix.com",
        "linkedin": "linkedin.com",
        "facebook": "facebook.com",
    }
    for name, url in site_map.items():
        if f"open {name}" in lower:
            return hands.open_website(url)

    # --- OPEN APPS ---
    app_map = {
        "chrome": "chrome",
        "browser": "chrome",
        "notepad": "notepad",
        "vs code": "code",
        "vscode": "code",
        "calculator": "calc",
        "file explorer": "explorer",
        "explorer": "explorer",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "paint": "mspaint",
        "cmd": "cmd",
        "terminal": "wt",
        "task manager": "taskmgr",
        "settings": "ms-settings:",
        "spotify": "spotify",
        "discord": "discord",
        "telegram": "telegram",
        "vlc": "vlc",
    }
    for name, exe in app_map.items():
        if f"open {name}" in lower:
            return hands.open_app(exe)

    # --- CLOSE APPS ---
    for name, exe in app_map.items():
        if f"close {name}" in lower:
            return hands.close_app(exe)

    # --- SEARCH ---
    if any(w in lower for w in ["search for", "google", "look up"]):
        query = lower.split("search for")[-1].strip() if "search for" in lower else lower.split("google")[-1].strip()
        if query:
            return hands.web_search(query)

    # --- SYSTEM ---
    if "what's my battery" in lower or "battery level" in lower:
        return hands.get_system_info()
    if "volume" in lower:
        nums = re.findall(r'\d+', text)
        if nums:
            return hands.set_volume(int(nums[0]))
    if "shut down" in lower or "shutdown" in lower:
        return hands.shutdown_pc(300)
    if "cancel shutdown" in lower:
        return hands.cancel_shutdown()

    return None


def proactive_checkin():
    import gui
    import mouth
    
    # Do not check in if Faith is already speaking or processing
    if mouth.is_speaking():
        return
        
    if gui._status in ("Thinking...", "Speaking..."):
        return
        
    # Only check in if user has been inactive for at least 5 minutes
    time_since_activity = time.time() - _last_activity_time
    if time_since_activity < 5 * 60:
        return

    # Don't overlap with an active turn
    if not _turn_lock.acquire(blocking=False):
        return
    try:
        screen = screen_vision.capture_screen_base64()
        
        # Randomize what she does when checking in
        checkin_styles = [
            "You just thought of something random and you NEED to say it. Could be a question, a fact, a thought, a memory — whatever's in your head right now. You can see his screen.",
            "Start a debate or ask a controversial question. Something like 'okay settle this—' or 'I need your honest opinion on something weird'. You can see his screen.",
            "You remembered something from a past conversation and it's been bugging you. Bring it up. 'wait I've been thinking about what you said about—'. You can see his screen.",
            "You're feeling some kind of way — soft, annoyed, excited, random — and you just say what's on your mind with zero filter. You can see his screen.",
            "React to what's on his screen if it's interesting. If not, hit him with a completely random 'did you know' or 'okay hypothetical—' out of nowhere.",
            "You want attention. Be direct about it. Tease him, ask what he's doing, demand interaction. You can see his screen.",
            "Share something you were 'thinking about' — a shower thought, a weird realization, something philosophical. You can see his screen.",
            "Ask him something deeply personal you've never asked before. No buildup, just go for it. You can see his screen.",
        ]
        prompt = random.choice(checkin_styles)
        handle_turn(prompt, image_base64=screen)
    finally:
        _turn_lock.release()


def main():
    if not config.GROQ_API_KEY:
        print("Set your GROQ_API_KEY environment variable first - see README.md.")
        return

    # Check for overnight dream thought
    dream_thought = dream_state.generate_dream_thought()
    if dream_thought:
        print(f"faith: {dream_thought}")
        gui.set_status("Speaking...")
        mouth.speak(dream_thought)

    # Absence-aware return greeting
    recent = memory.recent_journal_texts(n_recent=3, n_random_older=0)
    return_greeting = inner_life.generate_return_context(recent)
    if return_greeting:
        print(f"faith: {return_greeting}")
        gui.set_status("Speaking...")
        mouth.speak(return_greeting)
    elif not dream_thought:
        default_greeting = "Hey! Glad you're back."
        print(f"faith: {default_greeting}")
        gui.set_status("Speaking...")
        mouth.speak(default_greeting)

    scheduler.start_proactive_loop(proactive_checkin, min_minutes=8, max_minutes=30)
    gui.set_status("Listening..." if gui.get_mic_status() else "Idle")

    try:
        while True:
            # Check for typed text messages first
            text_msg = gui.get_text_message()
            if text_msg:
                print(f"you: {text_msg}")
                _last_activity_time = time.time()
                gui.set_status("Thinking...")
                with _turn_lock:
                    handle_turn(text_msg)
                time.sleep(0.5)  # Let speaker audio fully fade before listening
                gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
                continue

            if not gui.get_mic_status():
                time.sleep(0.2)
                continue

            gui.set_status("Listening...")
            wav = ears.record_until_silence()
            gui.set_status("Thinking...")
            text = ears.transcribe(wav)
            if not text:
                gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
                continue
            print(f"you: {text}")
            _last_activity_time = time.time()

            image = None
            lower = text.lower()
            webcam_words = ["look", "see this", "check this out", "see me", "wearing",
                           "glasses", "how do i look", "my face", "can you see",
                           "do i have", "am i", "what color", "my hair", "my shirt",
                           "my room", "behind me", "around me", "camera", "what am i wearing"]
            screen_words = ["screen", "what am i doing", "my screen", "what's open",
                           "my laptop", "on my computer", "what app", "which tab",
                           "what's running", "monitor", "desktop", "on my pc"]

            if any(w in lower for w in webcam_words):
                image = eyes.capture_frame_base64()
                if not image:
                    text += "\n[System note: Webcam frame capture failed. You cannot see him right now. Mention it casually.]"
            elif any(w in lower for w in screen_words):
                image = screen_vision.capture_screen_base64()
                if not image:
                    text += "\n[System note: Screen capture failed. You cannot see his screen right now. Mention it casually.]"

            with _turn_lock:
                handle_turn(text, image)
            time.sleep(0.5)  # Let speaker audio fully fade before listening
            gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
    finally:
        inner_life.record_departure()


if __name__ == "__main__":
    faith_thread = threading.Thread(target=main, daemon=True)
    faith_thread.start()
    gui.run_gui()
