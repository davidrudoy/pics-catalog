"""
Step 4 (+5): minimal local web UI — a thumbnail grid with date/rating/camera
filters, plus a sidebar of catalogued root folders. Plain HTML built with
f-strings (no Jinja2 — one page, not worth a templating dependency).
FastAPI just for routing + easy StaticFiles.

Adding a folder ("+ הוסף תיקייה") calls back into the pywebview desktop
shell (desktop.py) for a native folder-picker dialog, then POSTs the chosen
path here to scan it and generate its thumbnails.
"""
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import scan
import thumbnails
from config import THUMBNAIL_CACHE_DIR
from db import get_connection, init_db

init_db()
THUMBNAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.mount("/thumbnails", StaticFiles(directory=THUMBNAIL_CACHE_DIR), name="thumbnails")

PAGE_TEMPLATE = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>קטלוג תמונות</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: system-ui, sans-serif; background: #1e1e1e; color: #eee; margin: 0; display: flex; min-height: 100vh; }}
  h1 {{ font-size: 16px; font-weight: normal; color: #999; margin: 0 0 12px; }}

  .sidebar {{ width: 220px; flex: none; background: #171717; padding: 16px 12px; border-left: 1px solid #333; }}
  .sidebar a {{ display: block; color: #ccc; text-decoration: none; padding: 6px 8px; border-radius: 4px; font-size: 13px;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .sidebar a:hover {{ background: #2a2a2a; }}
  .sidebar a.active {{ background: #3a3a5a; color: #fff; }}
  #add-root-btn {{ width: 100%; margin-top: 12px; padding: 8px; background: #2a2a2a; color: #eee; border: 1px solid #444;
                    border-radius: 4px; cursor: pointer; }}
  #add-root-btn:disabled {{ opacity: 0.6; cursor: wait; }}

  .main {{ flex: 1; padding: 16px; min-width: 0; }}
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
<div class="sidebar">
  <h1>תיקיות</h1>
  <a href="/" class="{all_active}">כל התיקיות ({total_count})</a>
  {root_links}
  <button id="add-root-btn" type="button">+ הוסף תיקייה</button>
</div>
<div class="main">
<form method="get">
  <input type="hidden" name="root_id" value="{root_id}">
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
</div>
<script>
document.getElementById('add-root-btn').addEventListener('click', async () => {{
  if (!window.pywebview) {{
    alert('הוספת תיקייה זמינה רק כשמריצים כאפליקציית דסקטופ (python desktop.py)');
    return;
  }}
  const paths = await window.pywebview.api.choose_folder();
  if (!paths || !paths.length) return;

  const btn = document.getElementById('add-root-btn');
  btn.disabled = true;
  btn.textContent = 'סורק...';
  try {{
    const resp = await fetch('/add-root', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{path: paths[0]}}),
    }});
    const data = await resp.json();
    location.href = '/?root_id=' + data.root_id;
  }} catch (e) {{
    alert('הסריקה נכשלה: ' + e);
    btn.disabled = false;
    btn.textContent = '+ הוסף תיקייה';
  }}
}});
</script>
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


class AddRootRequest(BaseModel):
    path: str


@app.post("/add-root")
def add_root(body: AddRootRequest):
    root_path = Path(body.path)
    scan.scan(root_path)
    thumbnails.generate_all()
    conn = get_connection()
    row = conn.execute("SELECT id FROM roots WHERE path = ?", (str(root_path),)).fetchone()
    conn.close()
    return {"root_id": row["id"] if row else None}


@app.get("/", response_class=HTMLResponse)
def index(
    date_from: str = Query(""),
    date_to: str = Query(""),
    min_rating: str = Query(""),
    camera: str = Query(""),
    root_id: str = Query(""),
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
    if root_id:
        where.append("root_id = ?")
        params.append(int(root_id))

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
    roots = conn.execute(
        "SELECT r.id, r.path, COUNT(p.id) AS cnt FROM roots r "
        "LEFT JOIN photos p ON p.root_id = r.id "
        "GROUP BY r.id ORDER BY r.path"
    ).fetchall()
    total_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
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

    root_links = "\n".join(
        f'<a href="/?root_id={r["id"]}" class="{"active" if str(r["id"]) == root_id else ""}" '
        f'title="{r["path"]}">{Path(r["path"]).name or r["path"]} ({r["cnt"]})</a>'
        for r in roots
    )

    return PAGE_TEMPLATE.format(
        all_active="active" if not root_id else "",
        total_count=total_count,
        root_links=root_links,
        root_id=root_id,
        date_from=date_from,
        date_to=date_to,
        rating_options=_option_list([1, 2, 3, 4, 5], min_rating),
        camera_options=_option_list(cameras, camera),
        count=len(rows),
        cells=cells or "<p>אין תמונות תואמות</p>",
    )
