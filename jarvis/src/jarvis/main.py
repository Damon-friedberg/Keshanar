"""Entry point: the talk-back-and-forth loop, with the orb HUD.

    wake -> listen -> think (Claude + tools) -> speak -> repeat

Run:  py -m jarvis.main
Open the orb separately: ui/orb/index.html
"""
import asyncio

from . import config, hud, voice
from .agent import run_turn


async def loop() -> None:
    asyncio.create_task(hud.serve())          # orb HUD (no-op if websockets missing)
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
        if user_text.strip().lower() in {"stop", "exit", "goodbye", "shut down"}:
            hud.set_state("speaking")
            voice.speak("Goodbye.")
            return

        print(f"you> {user_text}")
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
