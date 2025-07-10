from app.main import app
import json
from pathlib import Path


def load_config() -> dict:
    """Load settings from ``config.json`` if present."""
    path = Path(__file__).resolve().parent / "config.json"
    if path.exists():
        with path.open() as f:
            try:
                return json.load(f)
            except Exception:
                pass
    return {}

if __name__ == '__main__':
    config = load_config()
    port = int(config.get("port", 7860))
    app.run(host="0.0.0.0", port=port)
