"""HUD bridge: broadcast Jarvis's state to the orb UI over WebSocket.

main.py starts `serve()` in the background if `websockets` is installed. The orb
(ui/orb/index.html) connects to ws://localhost:8765 and reacts to {state, level}.
Everything here is best-effort and a safe no-op if websockets isn't available.

States: idle | listening | thinking | speaking
"""
import asyncio
import contextlib
import json

_clients: set = set()
_state = {"state": "idle", "level": 0.0}


async def _handler(ws):
    _clients.add(ws)
    with contextlib.suppress(Exception):
        await ws.send(json.dumps(_state))
        async for _ in ws:  # we don't expect inbound messages; just keep open
            pass
    _clients.discard(ws)


async def serve(host: str = "localhost", port: int = 8765) -> None:
    try:
        import websockets
    except ImportError:
        print("[hud] websockets not installed; orb HUD disabled.")
        return
    async with websockets.serve(_handler, host, port):
        print(f"[hud] orb HUD on ws://{host}:{port}")
        await asyncio.Future()  # run forever


async def _safe_send(ws, msg):
    with contextlib.suppress(Exception):
        await ws.send(msg)


def set_state(state: str, level: float = 0.0) -> None:
    """Update the orb. Safe to call from anywhere; broadcasts if a loop is live."""
    _state.update(state=state, level=round(float(level), 3))
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    msg = json.dumps(_state)
    for ws in list(_clients):
        loop.create_task(_safe_send(ws, msg))
