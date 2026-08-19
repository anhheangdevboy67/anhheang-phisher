import os
import sys
import time
import shutil
import json
import urllib.request
import urllib.error
 
try:
    import pyfiglet
    HAS_FIGLET = True
except ImportError:
    HAS_FIGLET = False
 
# ---------- ANSI helpers ----------
 
RESET = "\033[0m"
BOLD = "\033[1m"
 
def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"
 
def rainbow_color(offset, speed=1.0):
    """Return a smooth rainbow RGB color based on a moving offset."""
    import colorsys
    hue = (offset * speed) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)
 
def rainbow_text(text, offset=0.0, step=0.035):
    """Color each character of a (possibly multi-line) string in a rainbow gradient."""
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
    # Fallback simple block banner if pyfiglet isn't installed
    width = shutil.get_terminal_size((80, 20)).columns
    border = "=" * min(len(text) + 10, width)
    return f"{border}\n   {text.upper()}\n{border}"
 
# ---------- Animation ----------
 
def animate_banner(banner, cycles=18, delay=0.05):
    for c in range(cycles):
        clear()
        offset = c * 0.05
        print(rainbow_text(banner, offset=offset))
        time.sleep(delay)
    clear()
    print(rainbow_text(banner, offset=cycles * 0.05))
 
# ---------- Menu ----------
 
GREEN = (0, 255, 100)
 
# 👉 Put your own website's URL here — it'll show up as option 4 in the menu.
MY_WEBSITE_URL = "https://your-website.com"
 
# 👉 Once you deploy the website (with server.py), put its base URL here,
# e.g. "https://anhheang.onrender.com" — no trailing slash.
# Leave as "" to keep the inbox local-only (saved to a file on this computer).
WEBSITE_API_URL = ""
 
MENU_ITEMS = [
    ("1", "Facebook", "https://facebook.com"),
    ("2", "Roblox", "https://roblox.com"),
    ("3", "Instagram", "https://instagram.com"),
    ("4", "My Website", MY_WEBSITE_URL),
    ("5", "Inbox", None),
]
 
INBOX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbox_messages.json")
 
def print_menu():
    r, g, b = GREEN
    print(f"{rgb(r,g,b)}{BOLD}Choose an option:{RESET}\n")
    for key, label, _url in MENU_ITEMS:
        print(f"  {rgb(r,g,b)}{BOLD}{key}. {label}{RESET}")
    print()
 
# ---------- Inbox ----------
 
def fetch_remote_messages():
    """GET messages from the deployed website. Returns a list, or None on failure."""
    url = f"{WEBSITE_API_URL.rstrip('/')}/api/messages"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"{rgb(255,80,80)}Couldn't reach the website ({e}).{RESET}")
        return None
 
def post_remote_message(name, message):
    """POST a new message to the deployed website. Returns True on success."""
    url = f"{WEBSITE_API_URL.rstrip('/')}/api/messages"
    payload = json.dumps({"name": name, "message": message}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"{rgb(255,80,80)}Couldn't reach the website ({e}).{RESET}")
        return False
 
def load_inbox():
    """Load messages from the website if configured, otherwise from the local file."""
    if WEBSITE_API_URL:
        remote = fetch_remote_messages()
        if remote is not None:
            return remote
    if not os.path.exists(INBOX_FILE):
        return []
    try:
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
 
def save_inbox(messages):
    with open(INBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
 
def print_box(name, message, when):
    r, g, b = GREEN
    color = rgb(r, g, b)
    width = max(len(name) + 8, len(message) + 4, 30)
    width = min(width, shutil.get_terminal_size((80, 20)).columns - 2)
 
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
 
    inner = width - 4
    print(f"{color}╔{'═' * (width - 2)}╗{RESET}")
    print(f"{color}║{BOLD} Name: {name:<{width - 10}}{RESET}{color} ║{RESET}")
    print(f"{color}╟{'─' * (width - 2)}╢{RESET}")
    for line in wrap(message, inner):
        print(f"{color}║ {line:<{width - 4}} ║{RESET}")
    print(f"{color}╟{'─' * (width - 2)}╢{RESET}")
    print(f"{color}║ {when:<{width - 4}} ║{RESET}")
    print(f"{color}╚{'═' * (width - 2)}╝{RESET}\n")
 
def inbox_menu():
    r, g, b = GREEN
    color = rgb(r, g, b)
    while True:
        print(f"\n{color}{BOLD}--- Inbox ---{RESET}")
        print(f"  {color}1. Send a message{RESET}")
        print(f"  {color}2. View inbox{RESET}")
        print(f"  {color}3. Back to main menu{RESET}\n")
        sub = input(f"{BOLD}Choose (1-3): {RESET}").strip()
 
        if sub == "1":
            name = input(f"{BOLD}Name: {RESET}").strip() or "Anonymous"
            message = input(f"{BOLD}Message: {RESET}").strip()
            if not message:
                print(f"{rgb(255,80,80)}Message can't be empty.{RESET}")
                continue
            when = time.strftime("%Y-%m-%d %H:%M:%S")
 
            if WEBSITE_API_URL and post_remote_message(name, message):
                print(f"\n{color}{BOLD}Message sent to your website's inbox!{RESET}")
                print_box(name, message, when)
            else:
                local = []
                if os.path.exists(INBOX_FILE):
                    try:
                        with open(INBOX_FILE, "r", encoding="utf-8") as f:
                            local = json.load(f)
                    except Exception:
                        local = []
                local.append({"name": name, "message": message, "when": when})
                save_inbox(local)
                note = " (couldn't reach the website, saved locally instead)" if WEBSITE_API_URL else ""
                print(f"\n{color}{BOLD}Message saved!{note}{RESET}")
                print_box(name, message, when)
 
        elif sub == "2":
            messages = load_inbox()
            if not messages:
                print(f"\n{rgb(255,80,80)}Inbox is empty.{RESET}\n")
                continue
            print()
            for m in messages:
                print_box(m["name"], m["message"], m["when"])
 
        elif sub == "3":
            return
        else:
            print(f"{rgb(255,80,80)}Invalid choice.{RESET}")
 
def main():
    text = "AnhHeang"
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
 
    banner = get_banner_text(text)
 
    try:
        animate_banner(banner)
    except KeyboardInterrupt:
        clear()
        print(rainbow_text(banner))
 
    print_menu()
 
    last = MENU_ITEMS[-1][0]
    choice = input(f"{BOLD}Enter choice (1-{last}): {RESET}").strip()
 
    match = next((item for item in MENU_ITEMS if item[0] == choice), None)
    if not match:
        print(f"\n{rgb(255,80,80)}Invalid choice. Please run again and pick 1-{last}.{RESET}\n")
        return
 
    key, label, url = match
 
    if label == "Inbox":
        inbox_menu()
        return
 
    print(f"\n{rainbow_text(f'>> You picked {label}!')}")
    print(f"{rgb(200,200,200)}{url}{RESET}\n")
 
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
 
if __name__ == "__main__":
    main()