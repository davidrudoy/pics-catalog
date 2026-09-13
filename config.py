"""
Reads settings from config.json (single source of truth, no CLI flags / env vars).
Edit config.json to point photos_dir at your archive.
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.json"

with open(_CONFIG_PATH, encoding="utf-8") as f:
    _raw = json.load(f)

PHOTOS_DIR = Path(_raw["photos_dir"])
DB_PATH = Path(_raw["db_path"])
THUMBNAIL_CACHE_DIR = Path(_raw["thumbnail_cache_dir"])
THUMBNAIL_SIZE = _raw["thumbnail_size"]

# File extensions we catalog. RAW formats first (require rawpy), then plain JPEG.
RAW_EXTENSIONS = {".rw2", ".arw"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
SUPPORTED_EXTENSIONS = RAW_EXTENSIONS | JPEG_EXTENSIONS
