"""Test Chatterbox TTS - load model, generate audio."""
from chatterbox.tts import ChatterboxTTS
import torch
import torchaudio
import os
import time

print("Loading Chatterbox model on CPU...")
start = time.time()
model = ChatterboxTTS.from_pretrained(device="cpu")
print(f"Model loaded in {time.time()-start:.1f}s")

# Test 1: Generate without voice clone (default voice)
print("\nTest 1: Default voice generation...")
start = time.time()
wav = model.generate("hello master, main isabella hoon.")
torchaudio.save("data/voice_pack/_test_default.wav", wav, model.sr)
elapsed = time.time() - start
size = os.path.getsize("data/voice_pack/_test_default.wav")
print(f"  Generated in {elapsed:.1f}s, size: {size} bytes")

# Test 2: With voice clone (if sample exists)
sample_dir = "data/voice_sample"
samples = [f for f in os.listdir(sample_dir) if f.endswith((".wav", ".mp3", ".m4a"))] if os.path.isdir(sample_dir) else []

if samples:
    sample_path = os.path.join(sample_dir, samples[0])
    print(f"\nTest 2: Voice clone from '{samples[0]}'...")
    start = time.time()
    wav = model.generate("master, aap kaise ho? main isabella hoon.", audio_prompt_path=sample_path)
    torchaudio.save("data/voice_pack/_test_cloned.wav", wav, model.sr)
    elapsed = time.time() - start
    print(f"  Cloned voice generated in {elapsed:.1f}s")
else:
    print(f"\nTest 2: SKIPPED - No voice sample found in {sample_dir}/")
    print("  Put a .wav file (5-30 sec of clear speech) in: C:\\faith\\data\\voice_sample\\")

print("\n=== CHATTERBOX READY ===")
print(f"Voice sample location: C:\\faith\\data\\voice_sample\\")
print("Put your YouTube voice clip there (wav/mp3, 5-30 seconds)")
