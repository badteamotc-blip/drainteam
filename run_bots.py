import os
import sys
import time
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Make the project root importable, including for config.py.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/healthz"):
            body = b"OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Keep Render logs clean.
        return


def start_web_server():
    # Render provides PORT for Web Services.
    port = int(os.environ.get("PORT", "10000"))

    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"HTTP health server listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


def start_bot():
    bot_path = os.path.join(PROJECT_ROOT, "tworker", "run.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = (
        PROJECT_ROOT
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )

    print("Starting tworker bot...", flush=True)

    return subprocess.Popen(
        [sys.executable, bot_path],
        cwd=os.path.join(PROJECT_ROOT, "tworker"),
        env=env,
    )


def main():
    # Web Service MUST listen on Render's PORT.
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    if not config.BOT_ENABLED:
        print("BOT_ENABLED=False; HTTP server is running.", flush=True)
        while True:
            time.sleep(60)

    # Restart the bot if it unexpectedly exits.
    while True:
        process = None
        try:
            process = start_bot()
            exit_code = process.wait()
            print(f"Bot process exited with code {exit_code}. Restarting in 5 seconds...", flush=True)
        except KeyboardInterrupt:
            print("Stopping...", flush=True)
            if process and process.poll() is None:
                process.terminate()
            break
        except Exception as e:
            print(f"Failed to start bot: {e}. Retrying in 5 seconds...", flush=True)

        time.sleep(5)


if __name__ == "__main__":
    main()
