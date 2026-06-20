"""Screen capture for 'show Jarvis your screen' workflows."""
import base64
import io


def grab_screen(region: dict | None = None) -> bytes:
    """Return a PNG of the primary screen (or an mss-style region dict)."""
    try:
        import mss
        import mss.tools

        with mss.mss() as s:
            mon = region or s.monitors[1]
            shot = s.grab(mon)
            return mss.tools.to_png(shot.rgb, shot.size)
    except Exception:  # noqa: BLE001 — fall back to Pillow on Windows
        from PIL import ImageGrab

        buf = io.BytesIO()
        ImageGrab.grab().save(buf, format="PNG")
        return buf.getvalue()


def to_b64(png: bytes) -> str:
    return base64.standard_b64encode(png).decode("ascii")
