"""
Step 3: generate a fast-loading thumbnail for every photo already in the DB.

- JPEG: decoding straight to a small size is cheap, so we just use Pillow.
- RAW (RW2/ARW): we pull the small preview image already embedded in the
  RAW file (rawpy.extract_thumb) instead of demosaicing the full sensor
  data — this is what keeps thousands of RAW thumbnails fast.

Thumbnails are cached as files named by content hash (not by original
filename), so identical files never get re-rendered twice.
"""
import io
import time
from pathlib import Path

import rawpy
from PIL import Image

from config import THUMBNAIL_CACHE_DIR, THUMBNAIL_SIZE
from db import get_connection


def _thumbnail_from_raw(path: Path) -> Image.Image:
    with rawpy.imread(str(path)) as raw:
        thumb = raw.extract_thumb()
    if thumb.format == rawpy.ThumbFormat.JPEG:
        return Image.open(io.BytesIO(thumb.data))
    # Rare fallback: embedded preview is a raw bitmap, not a JPEG.
    return Image.fromarray(thumb.data)


def generate_thumbnail(path: Path, extension: str, file_hash: str) -> Path:
    THUMBNAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = THUMBNAIL_CACHE_DIR / f"{file_hash}.jpg"
    if out_path.exists():
        return out_path

    if extension in (".rw2", ".arw"):
        img = _thumbnail_from_raw(path)
    else:
        img = Image.open(path)

    img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
    img.convert("RGB").save(out_path, "JPEG", quality=85)
    return out_path


def generate_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT path, extension, file_hash FROM photos WHERE thumbnail_path IS NULL"
    ).fetchall()

    done = failed = 0
    for row in rows:
        path = Path(row["path"])
        try:
            thumb_path = generate_thumbnail(path, row["extension"], row["file_hash"])
            conn.execute(
                "UPDATE photos SET thumbnail_path=? WHERE path=?",
                (str(thumb_path), row["path"]),
            )
            done += 1
        except Exception as e:
            print(f"  failed: {path} ({e})")
            failed += 1

    conn.commit()
    conn.close()
    return done, failed


if __name__ == "__main__":
    start = time.time()
    done, failed = generate_all()
    elapsed = time.time() - start
    print(f"Thumbnails done in {elapsed:.1f}s — generated: {done}, failed: {failed}")
