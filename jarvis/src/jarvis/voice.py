"""Voice I/O: wake word (double-clap), STT (faster-whisper), TTS (ElevenLabs).

These are working skeletons with the real libraries referenced. Fill in the
TODOs against your mic/keys. Each piece degrades gracefully so you can run in
text mode first, then turn on voice one layer at a time.
"""
import os

# ---------------------------------------------------------------- wake word
def wait_for_wake(mode: str = "double_clap") -> None:
    """Block until the wake trigger fires.

    double_clap: two sharp audio-energy peaks within ~600ms (no model needed).
    Implementation sketch: stream mic frames with sounddevice, compute RMS,
    detect two peaks above a threshold separated by a short gap.
    """
    if mode == "hotkey":
        input("[wake] press Enter to talk... ")
        return
    if mode == "always_on":
        return
    # TODO: real double-clap detection. Placeholder = press Enter.
    input("[wake] (double-clap detector TODO) press Enter to talk... ")


# ---------------------------------------------------------------- speech in
_whisper = None


def _get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel  # local, fast
        _whisper = WhisperModel("base.en", device="auto", compute_type="int8")
    return _whisper


def listen(seconds: float = 6.0) -> str:
    """Record a phrase from the mic and transcribe it locally."""
    try:
        import numpy as np
        import sounddevice as sd

        sr = 16000
        audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype="float32")
        sd.wait()
        segments, _ = _get_whisper().transcribe(np.squeeze(audio), language="en")
        return " ".join(s.text for s in segments).strip()
    except Exception as e:  # noqa: BLE001
        print(f"[stt] falling back to typing ({e})")
        return input("you> ")


# ---------------------------------------------------------------- speech out
def speak(text: str) -> None:
    """Speak a reply. ElevenLabs if configured, else offline pyttsx3."""
    if not text:
        return
    key = os.getenv("ELEVENLABS_API_KEY")
    voice = os.getenv("ELEVENLABS_VOICE_ID")
    if key and voice:
        try:
            from elevenlabs import play
            from elevenlabs.client import ElevenLabs

            client = ElevenLabs(api_key=key)
            audio = client.text_to_speech.convert(
                voice_id=voice, model_id="eleven_flash_v2_5", text=text
            )
            play(audio)
            return
        except Exception as e:  # noqa: BLE001
            print(f"[tts] ElevenLabs failed, using offline voice ({e})")
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:  # noqa: BLE001
        print(f"jarvis> {text}")
