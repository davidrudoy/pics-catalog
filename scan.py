"""
Step 1: walk a photos directory (a "root"), find RAW/JPEG files, and record
each one in the DB (path, size, mtime, hash), tagged with which root it came
from. Re-running only touches new or changed files — unchanged files are
skipped by comparing mtime+size.
"""
import hashlib
import sys
import time
from pathlib import Path

from config import PHOTOS_DIR, SUPPORTED_EXTENSIONS
from db import get_connection, get_or_create_root, init_db
from metadata import extract_exif


def hash_file(path, chunk_size=1024 * 1024) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_photo_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def scan(root: Path):
    root = Path(root)
    init_db()
    conn = get_connection()
    root_id = get_or_create_root(conn, str(root))

    existing = {
        row["path"]: (row["mtime"], row["file_size"])
        for row in conn.execute("SELECT path, mtime, file_size FROM photos")
    }

    new_count = updated_count = skipped_count = 0
    for path in find_photo_files(root):
        path_str = str(path)
        stat = path.stat()
        mtime, size = stat.st_mtime, stat.st_size

        prev = existing.get(path_str)
        if prev is not None and prev == (mtime, size):
            skipped_count += 1
            continue

        file_hash = hash_file(path)
        exif = extract_exif(path)
        exif_cols = (
            "date_taken", "camera_make", "camera_model", "lens",
            "exposure_time", "aperture", "iso", "focal_length",
        )
        exif_values = tuple(exif[col] for col in exif_cols)

        if prev is None:
            conn.execute(
                "INSERT INTO photos "
                "(path, root_id, extension, file_size, mtime, file_hash, "
                "date_taken, camera_make, camera_model, lens, "
                "exposure_time, aperture, iso, focal_length) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (path_str, root_id, path.suffix.lower(), size, mtime, file_hash, *exif_values),
            )
            new_count += 1
        else:
            conn.execute(
                "UPDATE photos SET root_id=?, file_size=?, mtime=?, file_hash=?, "
                "date_taken=?, camera_make=?, camera_model=?, lens=?, "
                "exposure_time=?, aperture=?, iso=?, focal_length=? WHERE path=?",
                (root_id, size, mtime, file_hash, *exif_values, path_str),
            )
            updated_count += 1

    conn.commit()
    conn.close()
    return new_count, updated_count, skipped_count


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else PHOTOS_DIR
    start = time.time()
    new_count, updated_count, skipped_count = scan(target)
    elapsed = time.time() - start
    print(
        f"Scan done in {elapsed:.1f}s — new: {new_count}, updated: {updated_count}, "
        f"unchanged (skipped): {skipped_count}"
    )
