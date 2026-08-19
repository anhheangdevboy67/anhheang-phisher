#!/usr/bin/env python3
"""
Backend for the AnhHeang inbox website.
Serves the static site (index.html / style.css / script.js) and a tiny
JSON API that stores messages people send from the website.

Run locally:
    pip install flask waitress
    python3 server.py
Then open http://localhost:5000
"""

import json
import os
import shutil
import sys
import time
from flask import Flask, jsonify, request, send_from_directory

try:
    import pyfiglet
    HAS_FIGLET = True
except ImportError:
    HAS_FIGLET = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "messages.json")

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")

# ---------- ANSI helpers ----------

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[38;2;0;255;100m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def rainbow_color(offset):
    import colorsys
    hue = offset % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def rainbow_text(text, offset=0.0, step=0.035):
    out = []
    i = offset
    for ch in text:
        if ch == "\n":
            out.append("\n")
            continue
        if ch == " ":
            out.append(" ")
            i += step
            continue
        r, g, b = rainbow_color(i)
        out.append(f"{rgb(r, g, b)}{BOLD}{ch}{RESET}")
        i += step
    return "".join(out)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def get_banner_text(text="AnhHeang"):
    if HAS_FIGLET:
        try:
            return pyfiglet.figlet_format(text, font="slant")
        except Exception:
            pass
    width = shutil.get_terminal_size((80, 20)).columns
    border = "=" * min(len(text) + 10, width)
    return f"{border}\n   {text.upper()}\n{border}"


def animate_banner(banner, cycles=18, delay=0.05):
    for c in range(cycles):
        clear()
        print(rainbow_text(banner, offset=c * 0.05))
        time.sleep(delay)
    clear()
    print(rainbow_text(banner, offset=cycles * 0.05))


# ---------- Message box display ----------

def print_message_box(name, message, when):
    """Print a message as a green boxed card in this terminal."""

    def wrap(text, w):
        words, lines, cur = text.split(), [], ""
        for word in words:
            if len(cur) + len(word) + 1 <= w:
                cur = f"{cur} {word}".strip()
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or [""]

    width = max(len(name) + 10, len(message) + 4, 32)
    width = min(width, shutil.get_terminal_size((80, 20)).columns - 2)
    inner = width - 4

    print(f"{GREEN}╔{'═' * (width - 2)}╗{RESET}")
    print(f"{GREEN}║{BOLD} Name: {name:<{width - 10}}{RESET}{GREEN} ║{RESET}")
    print(f"{GREEN}╟{'─' * (width - 2)}╢{RESET}")
    for line in wrap(message, inner):
        print(f"{GREEN}║ {line:<{width - 4}} ║{RESET}")
    print(f"{GREEN}╟{'─' * (width - 2)}╢{RESET}")
    print(f"{GREEN}║ {when:<{width - 4}} ║{RESET}")
    print(f"{GREEN}╚{'═' * (width - 2)}╝{RESET}\n")


def print_new_message(name, message, when):
    print()
    print(f"{GREEN}{BOLD}>>> New message received!{RESET}")
    print_message_box(name, message, when)


# ---------- Menu ----------

def print_menu():
    print(f"{GREEN}{BOLD}Choose an option:{RESET}\n")
    print(f"  {GREEN}{BOLD}1. Inbox{RESET}\n")


def show_inbox():
    print(f"\n{GREEN}{BOLD}--- Inbox ---{RESET}")
    print(f"  {GREEN}1. Custom Url{RESET}")
    print(f"  {GREEN}2. Normal Url{RESET}\n")
    sub = input(f"{BOLD}Choose (1-2): {RESET}").strip()

    if sub == "1":
        while True:
            url = input(f"{BOLD}Enter website URL (e.g. https://your-site.com): {RESET}").strip()
            if not url:
                print(f"\n{rgb(255,80,80)}No URL entered.{RESET}\n")
                return

            # Be forgiving about how people type URLs
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            messages = fetch_remote_messages(url)
            if messages is None:
                retry = input(f"{BOLD}Try a different URL? (y/n): {RESET}").strip().lower()
                if retry == "y":
                    continue
                return

            print()
            if not messages:
                print(f"{rgb(255,80,80)}Inbox is empty.{RESET}\n")
                return
            for m in messages:
                print_message_box(m["name"], m["message"], m["when"])
            return

    elif sub == "2":
        messages = load_messages()
        print()
        if not messages:
            print(f"{rgb(255,80,80)}Inbox is empty.{RESET}\n")
            return
        for m in messages:
            print_message_box(m["name"], m["message"], m["when"])

    else:
        print(f"\n{rgb(255,80,80)}Invalid choice.{RESET}\n")


def fetch_remote_messages(url):
    """GET messages from a website's /api/messages endpoint. Returns a list, or None on failure."""
    import urllib.request
    import urllib.error
    import socket

    full_url = f"{url.rstrip('/')}/api/messages"
    try:
        req = urllib.request.Request(full_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"\n{rgb(255,80,80)}That site responded with an error ({e.code}). "
              f"Is it running the /api/messages endpoint?{RESET}\n")
        return None
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.gaierror):
            print(
                f"\n{rgb(255,80,80)}Couldn't find that address ({url}).{RESET}\n"
                f"{rgb(255,80,80)}Make sure the site is actually deployed and the URL is typed "
                f"exactly as it works in your browser (e.g. https://anhheang.onrender.com).{RESET}\n"
            )
        else:
            print(f"\n{rgb(255,80,80)}Couldn't reach that URL ({e.reason}).{RESET}\n")
        return None
    except TimeoutError:
        print(f"\n{rgb(255,80,80)}That site took too long to respond. Try again.{RESET}\n")
        return None
    except ValueError:
        print(f"\n{rgb(255,80,80)}That URL didn't return valid data. "
              f"Make sure it's running this same server.py backend.{RESET}\n")
        return None


def run_menu():
    text = "AnhHeang"
    banner = get_banner_text(text)

    try:
        animate_banner(banner)
    except KeyboardInterrupt:
        clear()
        print(rainbow_text(banner))

    print_menu()
    choice = input(f"{BOLD}Enter choice (1): {RESET}").strip()

    if choice == "1":
        show_inbox()
    else:
        print(f"\n{rgb(255,80,80)}Invalid choice.{RESET}\n")


# ---------- Flask app ----------

@app.after_request
def add_cors_headers(response):
    # Allow the frontend to call this API even if it's hosted on another domain.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def load_messages():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_messages(messages):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/messages", methods=["GET"])
def get_messages():
    return jsonify(load_messages())


@app.route("/api/messages", methods=["POST"])
def post_message():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:60]
    message = str(data.get("message", "")).strip()[:600]

    if not name or not message:
        return jsonify({"error": "name and message are required"}), 400

    messages = load_messages()
    entry = {
        "name": name,
        "message": message,
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    messages.append(entry)
    save_messages(messages)

    print_new_message(entry["name"], entry["message"], entry["when"])

    return jsonify(entry), 201


if __name__ == "__main__":
    run_menu()

    port = int(os.environ.get("PORT", 5000))
    print(f"{GREEN}{BOLD}Server running at http://localhost:{port}{RESET}")
    print(f"{GREEN}Waiting for new messages...{RESET}\n")

    try:
        # Production-grade server — no dev-server warning, works on Windows too.
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        print(f"{GREEN}(Tip: run 'pip install waitress' for a cleaner server with no warnings){RESET}\n")
        app.run(host="0.0.0.0", port=port, debug=False)