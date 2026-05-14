from __future__ import annotations

from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent / "static"
BRAIN_ICON_PATH = STATIC_DIR / "brain-icon.png"
BRAIN_APPLE_TOUCH_ICON_PATH = STATIC_DIR / "apple-touch-icon.png"
BRAIN_FAVICON_PATH = STATIC_DIR / "favicon.ico"


def brain_icon_metadata(public_base_url: str) -> list[dict[str, object]]:
    base_url = public_base_url.rstrip("/")
    return [
        {
            "src": f"{base_url}/icon.png",
            "mimeType": "image/png",
            "sizes": ["512x512"],
        }
    ]
