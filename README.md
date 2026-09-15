# pics-catalog

Local photo cataloging tool — a search/filter/rating layer on top of a RAW+JPEG
archive, meant to sit alongside Lightroom, not replace its develop engine.

- Reads metadata only (EXIF), never decodes full RAW sensor data.
- Thumbnails come from the RAW's embedded preview (`rawpy.extract_thumb`),
  not a full render — this is what keeps browsing thousands of files fast.
- Ratings/tags are meant to be written to XMP sidecar files, never into the
  original RAW/JPEG.
- Browse and catalog multiple folders ("roots") — add any folder from any
  drive via a native folder picker, switch between them from the sidebar.
- Single local user, no accounts, no cloud/sync.

## Setup

```
pip install -r requirements.txt
python desktop.py   # opens as a native desktop window (recommended)
```

or as a plain local website:

```
python -m uvicorn app:app --reload   # browse at http://127.0.0.1:8000
```

Either way, the DB and thumbnail cache are created automatically on first
run. Click "+ הוסף תיקייה" in the sidebar to catalog a folder — no config
file editing required. (`config.json` / `config.example.json` still exist
for scripted/CLI scanning via `python scan.py <folder>`.)

Re-scanning a folder only processes new/changed files (by mtime+size).

### Desktop shortcut

A Windows desktop shortcut ("Photo Catalog") launches `desktop.py` with
`pythonw.exe` (no console window). To recreate it or make your own:

```
python make_icon.py   # regenerates assets/icon.ico
```

then create a `.lnk` pointing at `pythonw.exe "<repo>\desktop.py"` with that
icon (e.g. via PowerShell's `WScript.Shell` COM object).

## Status

Level 1 (catalog only) — steps 0–5 done: scan, EXIF, thumbnails, browsing
grid with date/rating/camera filters, multi-root folder browsing, desktop
app shell. Step 6 (rating/tagging from the UI, written to XMP sidecars) is
next.
