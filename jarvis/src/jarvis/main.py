"""Entry point: the talk-back-and-forth loop.

    wake -> listen -> think (Claude + tools) -> speak -> repeat

Run:  py -m jarvis.main           (from the src/ dir, or install -e .)
"""
import asyncio

from . import config, voice
from .agent import run_turn


async def loop() -> None:
    voice.speak("Jarvis online.")
    print(f"[jarvis] fast={config.MODEL_FAST}  heavy={config.MODEL_HEAVY}")
    while True:
        voice.wait_for_wake(config.WAKE_MODE)
        user_text = voice.listen()
        if not user_text:
            continue
        if user_text.strip().lower() in {"stop", "exit", "goodbye", "shut down"}:
            voice.speak("Goodbye.")
            return
        print(f"you> {user_text}")
        reply = await run_turn(user_text)
        print(f"jarvis> {reply}")
        voice.speak(reply)


def main() -> None:
    try:
        asyncio.run(loop())
    except KeyboardInterrupt:
        print("\n[jarvis] stopped.")


if __name__ == "__main__":
    main()
