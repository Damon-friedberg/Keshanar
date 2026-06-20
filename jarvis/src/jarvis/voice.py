"""Voice I/O: wake word (double-clap), STT (faster-whisper), TTS (ElevenLabs).

Lessons applied from VoiceMode/Vocode: don't record a fixed N seconds — use VAD
endpointing (record until ~1s of silence). Half-duplex by design (we record only
after speaking), which doubles as echo avoidance. Everything degrades to text mode
so you can run before the mic stack is set up.
"""
import os

# ---------------------------------------------------------------- wake word
def wait_for_wake(mode: str = "double_clap") -> None:
    """Block until the wake trigger fires."""
    if mode == "always_on":
        return
    if mode == "hotkey":
        input("[wake] press Enter to talk... ")
        return
    # TODO: real double-clap (sounddevice RMS, two energy peaks within ~600ms).
    input("[wake] (double-clap detector TODO) press Enter to talk... ")


# ---------------------------------------------------------------- speech in
_whisper = None


def _get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("base.en", device="auto", compute_type="int8")
    return _whisper


def _record_vad(sr: int, max_seconds: float,
                aggressiveness: int = 3, silence_ms: int = 1000,
                min_ms: int = 500) -> list | None:
    """Record until ~silence_ms of trailing silence. None if webrtcvad missing."""
    try:
        import webrtcvad
    except ImportError:
        return None
    import sounddevice as sd

    vad = webrtcvad.Vad(aggressiveness)
    frame_ms = 30
    frame_len = int(sr * frame_ms / 1000)        # 480 samples @ 16k = 960 bytes
    chunks: list[bytes] = []
    started = False
    silence = 0
    elapsed = 0
    print("[listening…]")
    with sd.RawInputStream(samplerate=sr, channels=1, dtype="int16",
                           blocksize=frame_len) as stream:
        while elapsed < max_seconds * 1000:
            data, _ = stream.read(frame_len)
            frame = bytes(data)
            elapsed += frame_ms
            speech = vad.is_speech(frame, sr)
            if speech:
                started, silence = True, 0
                chunks.append(frame)
            elif started:
                silence += frame_ms
                chunks.append(frame)
            if started and silence >= silence_ms and elapsed >= min_ms:
                break
    return chunks or None


def listen(max_seconds: float = 15.0) -> str:
    """Record a phrase (VAD-endpointed) and transcribe locally."""
    try:
        import numpy as np
        import sounddevice as sd

        sr = 16000
        frames = _record_vad(sr, max_seconds)
        if frames is None:                        # no VAD -> fixed-window fallback
            rec = sd.rec(int(6 * sr), samplerate=sr, channels=1, dtype="int16")
            sd.wait()
            audio = np.squeeze(rec).astype(np.float32) / 32768.0
        else:
            pcm = np.frombuffer(b"".join(frames), dtype=np.int16)
            audio = pcm.astype(np.float32) / 32768.0
        segments, _ = _get_whisper().transcribe(audio, language="en")
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
