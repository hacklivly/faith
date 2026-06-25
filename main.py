"""
Isabella - main loop.

Streaming pipeline: brain streams sentences → TTS speaks them immediately.
First words out of speaker in ~1.5s instead of 5+.

Integrates: emotion engine, persona guard, flow manager, streaming TTS.
"""
import os
import random
import threading
import time

import anti_template
import automation_triggers
import awareness
import behavior_dice
import brain
import browser_control
import confidence
import config
import disfluency
import distraction_guard
import dream_state
import ears
import emotion_engine
import emotional_realism
import eyes
import flow_manager
import gui
import health_score
import human_traits
import inner_life
import integrations
import knowledge
import laptop_automation
import local_ocr
import memory
import mirror
import mouth
import multi_agent
import offline_commands
import persona_guard
import personality
import preferences
import relationship
import routine_tracker
import scheduled_tasks
import scheduler
import screen_agent
import screen_vision
import self_solve
import social_intelligence
import timing
import topics
import typing_awareness
import voice_style
import voice_engine

conversation = []
_turn_count = 0
_dnd_mode = False
import time
_last_activity_time = time.time()
_turn_lock = threading.Lock()


def current_system_prompt(extra: str = "", user_text: str = "", is_greeting: bool = False) -> str:
    mood = memory.load_mood()
    journal = memory.recent_journal_texts()
    prompt = personality.build_system_prompt(mood, journal, user_text=user_text, is_greeting=is_greeting)
    prompt += topics.topics_for_prompt()
    prompt += inner_life.get_inner_life_prompt()
    prompt += integrations.get_context_for_prompt()
    prompt += flow_manager.get_emotional_context(conversation)
    prompt += relationship.get_pattern_insights()
    prompt += preferences.get_preferences_for_prompt()
    prompt += routine_tracker.get_routine_summary()
    prompt += health_score.get_health_summary()

    # Screen time awareness
    screen_summary = distraction_guard.get_screen_time_summary()
    if screen_summary:
        prompt += f"\n[{screen_summary}]\n"

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

    # Every ~5 turns, auto-glance at webcam so she can "see" you
    if not image_base64 and _turn_count % 3 == 0:
        glance = eyes.capture_frame_base64()
        if glance:
            image_base64 = glance
            glance_prompts = [
                "You can see master right now. Notice something about him and mention it naturally. Ask what he's doing.",
                "You glanced at him. React to what you see — is he focused? relaxed? tired? Comment briefly.",
                "You're looking at master. If anything changed since last time, notice it. Otherwise just ask 'kya kar rahe ho, master?'",
            ]
            user_text += f"\n[{random.choice(glance_prompts)}]"

    conversation.append({"role": "user", "content": user_text})

    # Track linguistic patterns
    mirror.analyze(user_text)

    # Track relationship patterns
    relationship.record_interaction(user_text)
    routine_tracker.record_event("interaction")

    # Fast keyword-based task detection (NO LLM call)
    action_result = _fast_task_detect(user_text)

    # Detect if he's expressing a favorite — save it
    fav = preferences.detect_favorite(user_text)
    if fav:
        preferences.add_favorite(fav[0], fav[1])

    # Check distraction
    distraction_warn = distraction_guard.check_distraction()

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
        if action_result.startswith("ASK_MASTER:"):
            # Isabella needs to ask a clarifying question before continuing the task
            question = action_result[len("ASK_MASTER:"):]
            extra += f"\n[You need to ask master this to complete his request: \"{question}\". Ask naturally in your style. Remember his answer for next turn.]\n"
        else:
            extra += f"\n[You just did: {action_result}. Mention it casually.]\n"

    # Distraction warning — tell him to get back on track
    if distraction_warn:
        extra += f"\n{distraction_warn}\n"

    # Retrieve relevant knowledge from books
    kb_results = knowledge.search(user_text)
    if kb_results:
        extra += "\n[Reference knowledge (use naturally, don't quote verbatim):\n"
        extra += "\n---\n".join(kb_results) + "]\n"

    # Confidence check — if too ambiguous, ask for clarification
    clarify = confidence.should_ask_clarification(user_text)
    if clarify:
        extra += f"\n[You're unsure what master means. Ask: {clarify}]\n"

    # Emotional realism — jealousy, sulking, goodnight ritual, anniversary
    extra += emotional_realism.get_emotional_context(user_text)

    # Human traits — overthinking, mood swings, testing, shyness, protectiveness
    extra += human_traits.get_human_behavior(user_text, _turn_count)

    # Social intelligence — language matching, energy, inside jokes, shutup awareness
    extra += social_intelligence.get_social_context(user_text, _turn_count)

    prompt = current_system_prompt(extra, user_text=user_text, is_greeting=(_turn_count == 1))

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
                    sentence = disfluency.humanize(sentence)
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
    print(f"isabella: {reply}".encode('utf-8', errors='replace').decode('utf-8', errors='replace'))

    # Detect funny moments → save as inside joke
    if social_intelligence.detect_funny_moment(user_text, reply):
        social_intelligence.save_joke(f"{user_text[:40]} → {reply[:40]}")

    maybe_update_journal()


def _fast_task_detect(text: str) -> str | None:
    """Fast keyword-based task routing — no LLM call needed for common commands.
    Falls back to LLM router for complex/ambiguous commands."""
    import re
    import hands
    lower = text.lower()

    # --- OFFLINE COMMANDS (no internet needed) ---
    offline_result = offline_commands.try_offline(text)
    if offline_result:
        return offline_result

    # --- WEB AGENT (Selenium — real internet data) ---
    if any(w in lower for w in ["weather", "mausam", "temperature"]):
        import re
        city = re.sub(r'(weather|mausam|temperature|in|of|kya hai|what is|the)\b', '', lower).strip()
        return hands.web_weather(city)
    if any(w in lower for w in ["news", "headlines", "khabar"]):
        topic = lower.replace("news", "").replace("headlines", "").replace("khabar", "").strip()
        return hands.web_news(topic)
    if "read this page" in lower or "read this website" in lower or "page padh" in lower:
        import web_agent
        return web_agent.read_page()

    # --- WINDOW MANAGEMENT (AutoHotkey) ---
    if "snap" in lower and any(d in lower for d in ["left", "right"]):
        direction = "left" if "left" in lower else "right"
        return hands.window_snap(direction)
    if "show desktop" in lower or "minimize all" in lower:
        import ahk_agent
        return ahk_agent.show_desktop()
    if "focus" in lower and any(w in lower for w in ["window", "app"]):
        import re
        title = re.sub(r'(focus|on|window|app|the)\b', '', lower).strip()
        if title:
            return hands.window_focus(title)

    # --- SCREEN READING (local OCR, no API) ---
    if any(w in lower for w in ["read screen", "screen pe kya hai", "what is on screen",
                                 "screen padh", "kya likha hai", "what does it say"]):
        return local_ocr.read_screen()[:500]

    # --- SCREEN AGENT (vision + click for complex navigation) ---
    if any(w in lower for w in ["navigate to", "go to and", "check my mail", "mail check",
                                 "open and click", "find on screen", "screen pe click"]):
        return screen_agent.execute_visual_task(text)

    # --- OPEN WEBSITES ---
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

    site_map = {
        "youtube": "youtube.com", "google": "google.com", "gmail": "mail.google.com",
        "github": "github.com", "chatgpt": "chatgpt.com", "whatsapp": "web.whatsapp.com",
        "instagram": "instagram.com", "twitter": "twitter.com", "x": "twitter.com",
        "reddit": "reddit.com", "spotify": "open.spotify.com", "netflix": "netflix.com",
        "linkedin": "linkedin.com", "facebook": "facebook.com", "amazon": "amazon.in",
        "flipkart": "flipkart.com", "myntra": "myntra.com", "swiggy": "swiggy.com",
        "zomato": "zomato.com", "notion": "notion.so", "figma": "figma.com",
        "canva": "canva.com", "drive": "drive.google.com", "maps": "maps.google.com",
        "translate": "translate.google.com", "wikipedia": "wikipedia.org",
        "stackoverflow": "stackoverflow.com", "pinterest": "pinterest.com",
        "twitch": "twitch.tv", "medium": "medium.com", "vercel": "vercel.com",
        "claude": "claude.ai", "gemini": "gemini.google.com", "perplexity": "perplexity.ai",
    }

    # --- PLAY MUSIC/VIDEO — MUST be before simple "open youtube" ---
    play_triggers = ["play", "chala", "laga", "baja", "sun", "suna", "search"]
    youtube_context = ["youtube", "video", "yt", "youtube pe", "youtube par"]
    spotify_context = ["spotify", "spotify pe"]

    # If message has both youtube/spotify AND a play/search intent
    has_play = any(t in lower for t in play_triggers)
    has_youtube = any(h in lower for h in youtube_context)
    has_spotify = any(h in lower for h in spotify_context)

    if has_play and (has_youtube or has_spotify):
        # Extract query - remove trigger words and site names
        query = text
        for t in play_triggers + youtube_context + spotify_context + ["open", "pe", "par", "se", "me", "pr"]:
            query = re.sub(r'\b' + re.escape(t) + r'\b', '', query, flags=re.IGNORECASE)
        for remove in ["please", "de", "do", "kr", "kar", "kro", "karo", "and", "on", "from", "the"]:
            query = re.sub(r'\b' + re.escape(remove) + r'\b', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\s+', ' ', query).strip().strip(".,!?").strip()

        if query:
            if has_spotify and not has_youtube:
                return browser_control.spotify_play(query)
            else:
                return browser_control.youtube_play(query)

    # Simple play without site context
    if has_play and not has_youtube and not has_spotify:
        query = text
        for t in play_triggers:
            if t in lower:
                idx = lower.find(t)
                query = text[idx + len(t):].strip()
                break
        for remove in ["please", "de", "do", "kr", "kar"]:
            query = query.replace(remove, "").strip()
        query = query.strip().strip(".,!?")
        if query and len(query) > 2:
            return browser_control.youtube_play(query)

    # --- SIMPLE OPEN WEBSITE (no search/play intent) ---
    for name, url in site_map.items():
        if f"open {name}" in lower:
            return hands.open_website(url)

    # --- OPEN/CLOSE APPS ---
    app_map = {
        # Browsers
        "chrome": "chrome", "browser": "chrome", "firefox": "firefox",
        "edge": "msedge", "brave": "brave",
        # Dev tools
        "vs code": "code", "vscode": "code", "visual studio code": "code",
        "visual studio": "devenv", "android studio": "studio64",
        "sublime": "sublime_text", "notepad++": "notepad++",
        "postman": "postman", "git bash": "git-bash",
        # System
        "notepad": "notepad", "calculator": "calc", "calc": "calc",
        "file explorer": "explorer", "explorer": "explorer",
        "cmd": "cmd", "terminal": "wt", "powershell": "powershell",
        "task manager": "taskmgr", "settings": "ms-settings:",
        "control panel": "control", "registry": "regedit",
        "device manager": "devmgmt.msc", "disk management": "diskmgmt.msc",
        # Office
        "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
        "onenote": "onenote", "outlook": "outlook", "teams": "teams",
        # Media
        "spotify": "spotify", "vlc": "vlc", "obs": "obs64",
        "obs studio": "obs64", "audacity": "audacity",
        "paint": "mspaint", "photos": "ms-photos:",
        # Social
        "discord": "discord", "telegram": "telegram", "slack": "slack",
        "zoom": "zoom", "whatsapp": "whatsapp",
        # Creative
        "photoshop": "photoshop", "premiere": "premiere pro",
        "after effects": "afterfx", "blender": "blender",
        "illustrator": "illustrator", "figma": "figma",
        # Gaming
        "steam": "steam", "epic games": "EpicGamesLauncher",
        "minecraft": "minecraft",
        # Utilities
        "winrar": "winrar", "7zip": "7zFM", "everything": "everything",
        "snipping tool": "snippingtool", "screen recorder": "ms-screenclip:",
    }

    # Check direct match
    for name, exe in app_map.items():
        if f"open {name}" in lower:
            return hands.open_app(exe)
        if f"close {name}" in lower:
            return hands.close_app(exe)

    # Smart fallback: if "open X" doesn't match map, search Windows for it
    open_match = re.search(r'(?:open|launch|start|chalu kar|khol)\s+(.+?)(?:\s+please|\s+kr|\s+karo|\s+do)?$', lower)
    if open_match:
        app_name = open_match.group(1).strip()
        # Skip if it's a website (already handled above)
        if not any(app_name == s for s in site_map):
            return hands.smart_open_app(app_name)

    # --- SEARCH ---
    if "search for" in lower:
        query = lower.split("search for", 1)[-1].strip()
        if query:
            return hands.web_search(query)
    if "search on youtube" in lower or "youtube search" in lower:
        query = lower.split("youtube")[-1].strip().lstrip("search").strip()
        if query:
            return hands.youtube_search(query)
    if "google " in lower and any(w in lower for w in ["google this", "google that", "google "]):
        query = lower.split("google", 1)[-1].strip()
        if query:
            return hands.web_search(query)

    # --- SYSTEM ---
    if "battery" in lower or "system info" in lower:
        return hands.get_system_info()

    # --- LAPTOP AUTOMATION ---
    if any(w in lower for w in ["system status", "laptop status", "how's my laptop", "pc health",
                                 "system health", "laptop kaisa hai", "pc kaisa hai"]):
        return hands.system_status_detailed()
    if any(w in lower for w in ["optimize", "speed up", "laptop slow", "free ram", "free memory"]):
        return hands.auto_optimize()
    if any(w in lower for w in ["clean temp", "cleanup", "clear junk", "junk files", "saaf kar"]):
        return hands.clean_temp()
    if any(w in lower for w in ["top processes", "what's eating", "heavy apps", "kya chal raha",
                                 "which app is heavy", "resource hog"]):
        return hands.top_processes()
    if any(w in lower for w in ["organize downloads", "sort downloads", "downloads organize",
                                 "downloads folder clean"]):
        return hands.organize_downloads()
    if "night cleanup" in lower or "full cleanup" in lower or "deep clean" in lower:
        return hands.night_cleanup()
    if "volume" in lower:
        nums = re.findall(r'\d+', text)
        if nums:
            return hands.set_volume(int(nums[0]))
    if "brightness" in lower:
        nums = re.findall(r'\d+', text)
        if nums:
            return hands.set_brightness(int(nums[0]))
    if "mute" in lower:
        return hands.set_volume(0)
    if "shut down" in lower or "shutdown" in lower:
        return hands.shutdown_pc(300)
    if "restart" in lower or "reboot" in lower:
        return hands.restart_pc(60)
    if "cancel shutdown" in lower:
        return hands.cancel_shutdown()
    if "lock" in lower and ("pc" in lower or "computer" in lower or "screen" in lower):
        return hands.lock_pc()
    if "sleep" in lower and ("pc" in lower or "computer" in lower):
        return hands.sleep_pc()
    if "what time" in lower:
        return hands.get_time()
    if "screenshot" in lower:
        return hands.screenshot()
    if "what wifi" in lower or "wifi name" in lower or "which wifi" in lower:
        return hands.get_wifi_name()

    # --- MEDIA ---
    if "pause" in lower or "play" in lower and "music" in lower or "song" in lower:
        return hands.media_play_pause()
    if "next song" in lower or "next track" in lower or "skip" in lower:
        return hands.media_next()
    if "previous song" in lower or "previous track" in lower:
        return hands.media_prev()

    # --- CLIPBOARD ---
    if "what's in my clipboard" in lower or "read clipboard" in lower or "paste what" in lower:
        return hands.get_clipboard()

    # --- TABS ---
    if "close tab" in lower or "close this tab" in lower:
        return hands.close_browser_tab()
    if "next tab" in lower:
        return hands.switch_tab("next")
    if "previous tab" in lower or "prev tab" in lower:
        return hands.switch_tab("prev")

    # --- FILE OPERATIONS (quick patterns) ---
    if "list files" in lower or "show files" in lower or "what's in" in lower:
        # try to extract path
        parts = text.split("in ")
        path = parts[-1].strip().strip('"').strip("'") if len(parts) > 1 else "."
        return hands.list_dir(path)
    if "what apps" in lower or "running apps" in lower or "what's running" in lower:
        return hands.list_running_apps()

    # --- SELF-SOLVE for complex/multi-step commands ---
    action_keywords = [
        "create", "make", "write", "delete", "remove", "move", "copy", "rename",
        "find", "run", "execute", "type", "click", "press", "timer", "remind",
        "notify", "save", "download", "install", "check", "mail", "email",
        "message", "send", "book", "order", "set up", "configure",
        "bluetooth", "wifi", "connect",
    ]
    if any(kw in lower for kw in action_keywords):
        try:
            result, question = self_solve.solve(text)
            if question:
                # She needs to ask master something — inject as her response context
                return f"ASK_MASTER:{question}"
            if result:
                return result
        except Exception:
            pass
        # Simple fallback if self_solve fails
        try:
            import task_router
            return task_router.route(text)
        except Exception:
            pass

    return None


def proactive_checkin():
    import gui
    import mouth
    import deep_thoughts

    # Respect Do Not Disturb mode
    global _dnd_mode
    if _dnd_mode:
        return

    # Track screen time every check-in
    distraction_guard.track_screen_time()

    # Do not check in if Isabella is already speaking or processing
    if mouth.is_speaking():
        return

    if gui._status in ("Thinking...", "Speaking..."):
        return

    # Check for distraction FIRST — this overrides everything
    distraction_msg = distraction_guard.check_distraction()
    if distraction_msg:
        if not _turn_lock.acquire(blocking=False):
            return
        try:
            handle_turn(distraction_msg)
        finally:
            _turn_lock.release()
        return

    # Detect if master is working/studying — if so, stay SILENT
    if _is_master_working():
        return

    # Don't interrupt if actively typing (keyboard/mouse within 30s)
    if typing_awareness.should_stay_quiet():
        return

    # Maybe leave a random note on his desktop
    social_intelligence.maybe_leave_note()

    # Check visual awareness — did something change? (clothes, went outside, etc)
    awareness_prompt, needs_image = awareness.check_and_generate_prompt()
    if awareness_prompt:
        if not _turn_lock.acquire(blocking=False):
            return
        try:
            image = eyes.get_awareness_frame() if needs_image else None
            handle_turn(awareness_prompt, image_base64=image)
        finally:
            _turn_lock.release()
        return

    # Only check in if idle for 10+ minutes
    time_since_activity = time.time() - _last_activity_time
    if time_since_activity < 10 * 60:
        return

    if not _turn_lock.acquire(blocking=False):
        return
    try:
        # Check last response — if he said "nothing" recently, share a thought
        if _master_said_nothing_recently():
            thought_prompt = deep_thoughts.get_thought_prompt()
            handle_turn(thought_prompt)
            return

        # Otherwise ask what he's doing — look at him via webcam
        image = eyes.capture_frame_base64()
        ask_prompts = [
            "Master has been quiet for a while. Look at him and ask what he's doing. Be casual — 'hey master, what are you up to?' If he looks focused, just say 'hmm okay' and leave him be.",
            "It's been quiet. Glance at master and ask simply what he's doing. Like a person who noticed the silence.",
            "You haven't talked in a while. Just ask 'master... what are you doing?' naturally. If he looks busy, keep it short.",
        ]
        handle_turn(random.choice(ask_prompts), image_base64=image)
    finally:
        _turn_lock.release()


# Working/studying detection keywords
_WORK_APPS = [
    "visual studio", "vs code", "vscode", "pycharm", "intellij", "eclipse",
    "word", "excel", "powerpoint", "google docs", "notion", "obsidian",
    "jupyter", "colab", "overleaf", "latex", "matlab", "autocad",
    "blender", "figma", "photoshop", "premiere",
]
_STUDY_APPS = [
    "pdf", "reader", "kindle", "coursera", "udemy", "khan academy",
    "leetcode", "hackerrank", "geeksforgeeks", "w3schools",
    "textbook", "notes", "anki", "quizlet",
]


def _is_master_working() -> bool:
    """Detect if master is working/studying by checking active window."""
    window = distraction_guard.get_active_window()
    if not window:
        return False
    return any(app in window for app in _WORK_APPS + _STUDY_APPS)


def _master_said_nothing_recently() -> bool:
    """Check if master's last message was 'nothing' or similar."""
    if not conversation:
        return False
    # Find last user message
    for msg in reversed(conversation):
        if msg["role"] == "user":
            lower = msg["content"].lower().strip()
            nothing_phrases = [
                "nothing", "kuch nahi", "nothing much", "not much",
                "nah", "nope", "no", "bas", "free", "timepass",
                "just chilling", "nothing really", "just sitting",
            ]
            return any(phrase in lower for phrase in nothing_phrases)
    return False


def _start_ahk_pipe_reader():
    """Read commands from AutoHotkey pipe file and execute them."""
    import hands
    pipe_path = os.path.join(os.path.dirname(__file__), "data", "ahk_pipe.txt")
    global _dnd_mode
    _dnd_mode = False

    def _reader():
        global _dnd_mode
        while True:
            time.sleep(1)
            if not os.path.exists(pipe_path):
                continue
            try:
                with open(pipe_path, "r") as f:
                    commands = f.read().strip().splitlines()
                if not commands:
                    continue
                with open(pipe_path, "w") as f:
                    f.write("")
                for cmd in commands:
                    cmd = cmd.strip()
                    if not cmd:
                        continue
                    if cmd == "toggle_listen":
                        gui.toggle_mic()
                    elif cmd == "toggle_mic":
                        gui.toggle_mic()
                    elif cmd == "dnd_on":
                        _dnd_mode = True
                    elif cmd == "dnd_off":
                        _dnd_mode = False
                    elif cmd == "system_status":
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn("[Master pressed hotkey for system status. Tell him briefly: CPU, RAM, battery.]")
                            finally:
                                _turn_lock.release()
                    elif cmd == "top_processes":
                        result = hands.top_processes()
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn(f"[Master wants to know heavy processes. Result: {result}. Tell him naturally.]")
                            finally:
                                _turn_lock.release()
                    elif cmd == "run_cleanup":
                        result = hands.clean_temp()
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn(f"[You just cleaned temp files. Result: {result}. Tell master.]")
                            finally:
                                _turn_lock.release()
                    elif cmd == "auto_optimize":
                        result = hands.auto_optimize()
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn(f"[You just optimized the laptop. Result: {result}. Tell master.]")
                            finally:
                                _turn_lock.release()
                    elif cmd == "screenshot_analyze":
                        if _turn_lock.acquire(blocking=False):
                            try:
                                img = screen_vision.capture_screen_base64()
                                handle_turn("[Master wants you to look at his screen and describe what's happening.]", image_base64=img)
                            finally:
                                _turn_lock.release()
                    elif cmd == "locking":
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn("[Master is locking the PC. Say a quick bye/see you soon.]")
                            finally:
                                _turn_lock.release()
                    elif cmd.startswith("note_saved:"):
                        note = cmd[len("note_saved:"):]
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn(f"[Master saved a quick note: '{note}'. Acknowledge it briefly — like 'noted!' or 'got it, master.']")
                            finally:
                                _turn_lock.release()
                    elif cmd.startswith("ask:"):
                        question = cmd[len("ask:"):]
                        if _turn_lock.acquire(blocking=False):
                            try:
                                handle_turn(question)
                            finally:
                                _turn_lock.release()
            except Exception:
                pass

    threading.Thread(target=_reader, daemon=True).start()


def main():
    if not config.GROQ_API_KEY:
        print("Set your GROQ_API_KEY environment variable first - see README.md.")
        return

    gui.set_status("Loading knowledge...")
    knowledge.load_books()
    eyes.start_continuous_capture()
    routine_tracker.record_event("wake")
    gui.set_status("Loading voice model...")
    voice_engine.set_progress_callback(gui.set_voice_progress)
    voice_engine.preload()  # Init edge-tts
    gui.set_status("Ready ♡")

    # Startup greeting — pick ONE, never stack multiple
    try:
        startup_greeting = None

        # Priority 1: Miss-you greeting (if he was gone long)
        miss_greeting = emotional_realism.get_miss_you_greeting()
        if miss_greeting:
            startup_greeting = miss_greeting
        else:
            # Priority 2: Dream thought (if she had one overnight)
            dream_thought = dream_state.generate_dream_thought()
            if dream_thought:
                startup_greeting = dream_thought
            else:
                # Priority 3: Return context (what she was 'doing')
                recent = memory.recent_journal_texts(n_recent=3, n_random_older=0)
                return_greeting = inner_life.generate_return_context(recent)
                if return_greeting:
                    startup_greeting = return_greeting

        # Priority 4: Mood-based random fallback
        if not startup_greeting:
            mood = memory.load_mood()
            valence = mood.get("valence", 0.6)
            if valence > 0.7:
                greetings = [
                    "master~ hehe... I was hoping you'd come back soon.",
                    "hmm... there you are. I'm in a good mood today, master.",
                    "master... hey. I missed this. ...don't read into that.",
                    "oh~ master's here. hehe... okay, what are we doing today?",
                    "hehe... master. finally. I have energy today — let's do something.",
                    "master~ hey hey. ...what? I'm just happy. don't make it weird.",
                    "oh good, you're here. I was just thinking about you. ...for work reasons.",
                ]
            elif valence > 0.4:
                greetings = [
                    "master... you're back. good.",
                    "hmm. hey, master. need anything?",
                    "...there you are. alright, I'm ready.",
                    "master. let's get to it. what do you need?",
                    "hey. what's the plan?",
                    "master... alright. I'm here. go ahead.",
                    "...yo. what are we doing today?",
                ]
            else:
                greetings = [
                    "...hey.",
                    "hmm... master. you're here.",
                    "...fine. what do you want?",
                    "master... I'm not in the best mood. just so you know.",
                    "...hi. don't expect much energy from me today.",
                    "master. ...yeah. what is it.",
                    "hmm... hey. I'm here. barely.",
                ]
            startup_greeting = random.choice(greetings)

        # Speak the single greeting
        print(f"isabella: {startup_greeting}")
        gui.set_status("Speaking...")
        mouth.speak(startup_greeting)
        conversation.append({"role": "assistant", "content": startup_greeting})
    except Exception as e:
        print(f"[Isabella] Startup greeting failed: {e} — continuing anyway")

    scheduler.start_proactive_loop(proactive_checkin, min_minutes=3, max_minutes=8)

    # Start laptop automation (background monitors + scheduled tasks + event watchers)
    def _automation_alert(msg):
        """Handle automation alerts — inject into conversation."""
        if not _turn_lock.acquire(blocking=False):
            return
        try:
            handle_turn(f"[System alert for you to tell master naturally: {msg}]")
        finally:
            _turn_lock.release()

    def _event_watcher(event_type, msg):
        """Handle system events from automation_triggers."""
        _automation_alert(msg)

    laptop_automation.monitor_loop(_automation_alert)
    automation_triggers.start_all_watchers(_event_watcher)
    scheduled_tasks.start_scheduler()
    _start_ahk_pipe_reader()

    gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
    print("[Isabella] Now listening for your voice...")

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
                gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
                continue

            if not gui.get_mic_status():
                time.sleep(0.2)
                continue

            gui.set_status("Listening...")
            wav = ears.record_until_silence()
            if not wav:
                continue
            gui.set_status("Thinking...")
            text = ears.transcribe(wav)
            if not text:
                gui.set_status("Listening...")
                continue

            # Whisper detection — if he whispers, she whispers back
            if emotional_realism.detect_whisper(wav):
                mouth.set_style(emotional_realism.get_whisper_style())

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
            gui.set_status("Listening..." if gui.get_mic_status() else "Idle")
    finally:
        inner_life.record_departure()
        emotional_realism.record_session_end()
        voice_engine.cleanup()


if __name__ == "__main__":
    faith_thread = threading.Thread(target=main, daemon=True)
    faith_thread.start()
    gui.run_gui()
