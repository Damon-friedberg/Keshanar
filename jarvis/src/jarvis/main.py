"""Entry point: the talk-back-and-forth loop, with the orb HUD and capture mode.

    wake -> listen -> [normal turn | capture] -> speak -> repeat

Run:  py -m jarvis.main
Open the orb separately: ui/orb/index.html
"""
import asyncio
import re

from . import capture, config, context, hud, profile, vision, voice
from .agent import run_turn

_SWITCH = re.compile(r"^(?:switch to|work on|working on|focus on|context)\s+(.+)$", re.I)
_LINK = re.compile(r"^link(?:\s+this)?(?:\s+to)?\s+(.+)$", re.I)
# phrases that mean "learn something durable"
_LEARN = ("remember", "i prefer", "from now on", "call me", "note about me",
          "i like", "i don't like", "i hate", "my name is", "fyi")


def _classify_link(v: str):
    v = v.strip().strip('"').strip("'")
    if v.lower().startswith(("http://", "https://")):
        return "cowork", v
    if v.startswith(("~", "/", ".")) or re.match(r"^[a-zA-Z]:[\\/]", v) or "\\" in v or "/" in v:
        return "code", v
    return "note", v

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
        msw = _SWITCH.match(user_text.strip())
        if msw:
            slug = context.switch(msw.group(1))
            hud.set_state("speaking")
            voice.speak("Back to personal." if slug == context.GENERAL
                        else f"Now working on {msw.group(1).strip()}.")
            continue
        mlk = _LINK.match(user_text.strip())
        if mlk:
            if context.active() == context.GENERAL:
                voice.speak("Switch to a customer first, then link it.")
                continue
            kind, val = _classify_link(mlk.group(1))
            context.set_link(kind, val)
            voice.speak(f"Linked this customer's {kind}.")
            continue
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
            learner = context.learn if context.active() != context.GENERAL else profile.learn
            try:
                learner(user_text)                # adapt (to this customer, or to you)
            except Exception as e:                # noqa: BLE001
                print(f"[learn] skipped ({e})")
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
