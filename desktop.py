"""
Runs the same FastAPI app (app.py) in a background thread and opens it in a
native OS window via pywebview — no browser chrome, no Electron. This is the
whole difference between "web app" and "desktop app" here: same server, same
HTML, different window.

Also exposes a small JS-callable API (window.pywebview.api) so the page's
"+ הוסף תיקייה" button can open a real native folder-picker — pywebview's
own dialog already lets you browse every drive/folder on the machine, so
there's no need to build a custom in-app file browser.
"""
import threading

import uvicorn
import webview

HOST, PORT = "127.0.0.1", 8000


def run_server():
    uvicorn.run("app:app", host=HOST, port=PORT, log_level="warning")


class Api:
    def choose_folder(self):
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        return list(result) if result else []


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    window = webview.create_window(
        "קטלוג תמונות", f"http://{HOST}:{PORT}/", width=1200, height=800, js_api=Api()
    )
    webview.start()
