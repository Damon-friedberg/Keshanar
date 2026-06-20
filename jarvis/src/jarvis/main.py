"""Entry point: the talk-back-and-forth loop, with the orb HUD and capture mode.

    wake -> listen -> [normal turn | capture] -> speak -> repeat

Run:  py -m jarvis.main
Open the orb separately: ui/orb/index.html
"""
import asyncio

from . import capture, config, hud, profile, vision, voice
from .agent import run_turn

# phrases that mean "learn something durable about me"
_LEARN = ("remember", "i prefer", "from now on", "call me", "note about me",
          "i like", "i don't like", "i hate", "my name is", "fyi")

# phrases that start a multi-step "walk me through it" capture
_SESSION = ("start capture", "capture session", "capture mode")
# phrases for a one-shot screen+voice snapshot
_ONESHOT = ("capture this", "log this", "take a note", "make a task",
            "make tasks", "note this", "remember this")
_STOP = {"stop", "exit", "goodbye", "shut down"}
_DONE = ("done", "finished", "that's it", "that is it", "stop capture")


async def _capture_session() -> None:
    voice.speak("Capture mode. Walk me through it on screen and out loud. Say 'done' when finished.")
    steps: list = []
    while True:
        hud.set_state("listening")
        text = voice.listen(seconds=8)
        if not text:
            continue
        if any(w in text.lower() for w in _DONE):
            break
        steps.append((text, vision.grab_screen()))
        voice.speak("Got it — keep going.")
    if not steps:
        voice.speak("Nothing captured.")
        return
    hud.set_state("thinking")
    voice.speak(capture.spoken_summary(capture.compile_session(steps)))


async def loop() -> None:
    asyncio.create_task(hud.serve())
    hud.set_state("idle")
    voice.speak("Jarvis online.")
    print(f"[jarvis] fast={config.MODEL_FAST}  heavy={config.MODEL_HEAVY}")

    while True:
        hud.set_state("idle")
        voice.wait_for_wake(config.WAKE_MODE)

        hud.set_state("listening")
        user_text = voice.listen()
        if not user_text:
            continue
        low = user_text.strip().lower()

        if low in _STOP:
            hud.set_state("speaking")
            voice.speak("Goodbye.")
            return
        if any(k in low for k in _SESSION):
            await _capture_session()
            continue
        if any(k in low for k in _ONESHOT):
            hud.set_state("thinking")
            data = capture.capture(user_text, vision.grab_screen())
            hud.set_state("speaking")
            voice.speak(capture.spoken_summary(data))
            continue

        print(f"you> {user_text}")
        if any(k in low for k in _LEARN):
            try:
                profile.learn(user_text)          # adapt to you, then answer
            except Exception as e:                # noqa: BLE001
                print(f"[profile] learn skipped ({e})")
        hud.set_state("thinking")
        reply = await run_turn(user_text)
        print(f"jarvis> {reply}")
        hud.set_state("speaking")
        voice.speak(reply)


def main() -> None:
    try:
        asyncio.run(loop())
    except KeyboardInterrupt:
        print("\n[jarvis] stopped.")


if __name__ == "__main__":
    main()
