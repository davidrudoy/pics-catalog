"""
Step 4 (+5): minimal local web UI — a thumbnail grid with date/rating/camera
filters. Plain HTML built with f-strings (no Jinja2 — one page, not worth
a templating dependency). FastAPI just for routing + easy StaticFiles.
"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import THUMBNAIL_CACHE_DIR
from db import get_connection

app = FastAPI()
app.mount("/thumbnails", StaticFiles(directory=THUMBNAIL_CACHE_DIR), name="thumbnails")

PAGE_TEMPLATE = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>קטלוג תמונות</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #1e1e1e; color: #eee; margin: 0; padding: 16px; }}
  h1 {{ font-size: 18px; font-weight: normal; color: #999; }}
  form {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; align-items: center; }}
  form input, form select {{ background: #2a2a2a; color: #eee; border: 1px solid #444; border-radius: 4px; padding: 4px 8px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px; }}
  .cell {{ background: #2a2a2a; border-radius: 6px; overflow: hidden; }}
  .cell img {{ width: 100%; height: 160px; object-fit: cover; display: block; }}
  .meta {{ padding: 6px 8px; font-size: 12px; color: #aaa; }}
  .stars {{ color: gold; }}
  .count {{ color: #888; font-size: 13px; margin-bottom: 12px; }}
</style>
</head>
<body>
<h1>קטלוג תמונות</h1>
<form method="get">
  <label>מתאריך <input type="date" name="date_from" value="{date_from}"></label>
  <label>עד תאריך <input type="date" name="date_to" value="{date_to}"></label>
  <label>דירוג מינימלי
    <select name="min_rating">{rating_options}</select>
  </label>
  <label>מצלמה
    <select name="camera">{camera_options}</select>
  </label>
  <button type="submit">סנן</button>
</form>
<div class="count">{count} תמונות</div>
<div class="grid">
{cells}
</div>
</body>
</html>
"""

CELL_TEMPLATE = """<div class="cell">
  <img src="/thumbnails/{thumb_name}" loading="lazy">
  <div class="meta">
    {date_taken}<br>
    {camera}<br>
    <span class="stars">{stars}</span>
  </div>
</div>"""


def _option_list(values, selected, label_all="הכל"):
    opts = [f'<option value="" {"selected" if not selected else ""}>{label_all}</option>']
    for v in values:
        sel = "selected" if str(v) == str(selected) else ""
        opts.append(f'<option value="{v}" {sel}>{v}</option>')
    return "".join(opts)


@app.get("/", response_class=HTMLResponse)
def index(
    date_from: str = Query(""),
    date_to: str = Query(""),
    min_rating: str = Query(""),
    camera: str = Query(""),
):
    conn = get_connection()

    where = ["thumbnail_path IS NOT NULL"]
    params = []
    if date_from:
        where.append("date_taken >= ?")
        params.append(date_from.replace("-", ":") + " 00:00:00")
    if date_to:
        where.append("date_taken <= ?")
        params.append(date_to.replace("-", ":") + " 23:59:59")
    if min_rating:
        where.append("rating >= ?")
        params.append(int(min_rating))
    if camera:
        where.append("camera_model = ?")
        params.append(camera)

    sql = (
        "SELECT thumbnail_path, date_taken, camera_model, rating FROM photos "
        f"WHERE {' AND '.join(where)} ORDER BY date_taken DESC"
    )
    rows = conn.execute(sql, params).fetchall()

    cameras = [
        r["camera_model"]
        for r in conn.execute(
            "SELECT DISTINCT camera_model FROM photos WHERE camera_model IS NOT NULL ORDER BY 1"
        )
    ]
    conn.close()

    cells = "\n".join(
        CELL_TEMPLATE.format(
            thumb_name=row["thumbnail_path"].split("\\")[-1].split("/")[-1],
            date_taken=row["date_taken"] or "—",
            camera=row["camera_model"] or "—",
            stars="★" * row["rating"] + "☆" * (5 - row["rating"]),
        )
        for row in rows
    )

    return PAGE_TEMPLATE.format(
        date_from=date_from,
        date_to=date_to,
        rating_options=_option_list([1, 2, 3, 4, 5], min_rating),
        camera_options=_option_list(cameras, camera),
        count=len(rows),
        cells=cells or "<p>אין תמונות תואמות</p>",
    )
