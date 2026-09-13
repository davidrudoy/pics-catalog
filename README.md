# pics-catalog

Local photo cataloging tool — a search/filter/rating layer on top of a RAW+JPEG
archive, meant to sit alongside Lightroom, not replace its develop engine.

- Reads metadata only (EXIF), never decodes full RAW sensor data.
- Thumbnails come from the RAW's embedded preview (`rawpy.extract_thumb`),
  not a full render — this is what keeps browsing thousands of files fast.
- Ratings/tags are meant to be written to XMP sidecar files, never into the
  original RAW/JPEG.
- Single local user, no accounts, no cloud/sync.

## Setup

```
pip install -r requirements.txt
cp config.example.json config.json   # then edit photos_dir
python scan.py                        # step 1+2: walk folder, hash, EXIF
python thumbnails.py                  # step 3: generate thumbnails
python -m uvicorn app:app --reload    # step 4+5: browse at http://127.0.0.1:8000
```

Re-running `scan.py` only processes new/changed files (by mtime+size).

## Status

Level 1 (catalog only) — steps 0–5 done: scan, EXIF, thumbnails, browsing
grid with date/rating/camera filters. Step 6 (rating/tagging from the UI,
written to XMP sidecars) is next.
