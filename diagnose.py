"""Quick diagnostic - run this instead of main.py to see what's happening."""
import os, sys, time, threading

# Make sure key is set
key = os.environ.get("GROQ_API_KEY", "")
if not key:
    print("ERROR: GROQ_API_KEY not set!")
    print("Run: $env:GROQ_API_KEY = 'your-key-here'")
    sys.exit(1)
print(f"[1/6] API Key: set ({key[:8]}...)")

# Test imports
import ears, mouth, brain, gui
print("[2/6] All modules imported OK")

# Test mic
print("[3/6] Testing mic... speak for 2 seconds")
import pyaudio, webrtcvad
pa = pyaudio.PyAudio()
vad = webrtcvad.Vad(2)
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=480)
speech = 0
for _ in range(66):  # ~2 sec
    frame = stream.read(480, exception_on_overflow=False)
    if vad.is_speech(frame, 16000):
        speech += 1
stream.close()
pa.terminate()
print(f"      Speech frames: {speech}/66 {'- MIC OK' if speech > 3 else '- NO SPEECH! Check mic'}")

# Test TTS
print("[4/6] Testing TTS...")
try:
    mouth.speak("Testing")
    print("      TTS OK")
except Exception as e:
    print(f"      TTS failed: {e}")

# Test API
print("[5/6] Testing Groq API...")
try:
    reply = brain.get_reply("Say hi in 3 words.", [{"role": "user", "content": "hi"}])
    print(f"      API OK: '{reply[:50]}'")
except Exception as e:
    print(f"      API failed: {e}")

# Test full record+transcribe
print("[6/6] Full test - speak something now...")
wav = ears.record_until_silence(max_silence_frames=20)
if wav and len(wav) > 100:
    print(f"      Recorded {len(wav)} bytes")
    text = ears.transcribe(wav)
    print(f"      Transcription: '{text}'")
    if text:
        print("\n=== ALL WORKING! Run 'python main.py' ===")
    else:
        print("\n=== MIC works but transcription failed. Check API key/rate limits ===")
else:
    print("      No audio captured!")
    print("\n=== MIC ISSUE - voice not detected by VAD ===")
