import time
import requests
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional

# ===================== CONFIG =====================
# Required
TARGET_URL = "https://m.bookmyshow.com/bengaluru/movies/your-movie/event-id"
KEYWORDS = ["Book Tickets", "07:30 PM", "PVR INOX GSM"]  # updated keyword
INTERVAL_SECONDS = 90  # be polite: 60–180 seconds recommended

# Optional: Telegram bot notification
TELEGRAM_BOT_TOKEN = ""   # e.g., "123456:ABC-DEF..."
TELEGRAM_CHAT_ID = ""     # e.g., "123456789"

# Optional: Pushbullet notification
PUSHBULLET_TOKEN = ""     # e.g., "o.xxxxxxxxxxxxxxxxxxxx"

# Optional: Email (SMTP) notification (Gmail example)
SMTP_HOST = ""            # e.g., "smtp.gmail.com"
SMTP_PORT = 587           # 587 for TLS
SMTP_USER = ""            # your email address
SMTP_PASS = ""            # app password (recommended)
EMAIL_TO = ""             # destination email address
# =================== END CONFIG ===================


def validate_config():
    if not TARGET_URL or not isinstance(TARGET_URL, str):
        raise RuntimeError("Please set TARGET_URL to a valid BookMyShow page URL.")
    if not KEYWORDS or not isinstance(KEYWORDS, list):
        raise RuntimeError("Please set KEYWORDS to a non-empty list of strings.")
    if INTERVAL_SECONDS < 15:
        print("Warning: INTERVAL_SECONDS is quite low. Consider >=60s to be polite and avoid rate-limits.")


def fetch_text(url: str, timeout: int = 20) -> str:
    # Using a mobile user-agent often yields simpler HTML
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def text_contains_any(text: str, needles: List[str]) -> List[str]:
    t = text.lower()
    found = []
    for s in needles:
        if s and s.lower() in t:
            found.append(s)
    return found


def notify_console(message: str):
    print(f"[ALERT] {message}")


def notify_telegram(message: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"[WARN] Telegram notify failed: {e}")


def notify_pushbullet(message: str):
    if not PUSHBULLET_TOKEN:
        return
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"}
    payload = {"type": "note", "title": "BookMyShow Alert", "body": message}
    try:
        requests.post(url, json=payload, headers=headers, timeout=15)
    except Exception as e:
        print(f"[WARN] Pushbullet notify failed: {e}")


def notify_email(subject: str, body: str):
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and EMAIL_TO):
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [EMAIL_TO], msg.as_string())
    except Exception as e:
        print(f"[WARN] Email notify failed: {e}")


def notify_all(message: str):
    notify_console(message)
    notify_telegram(message)
    notify_pushbullet(message)
    notify_email("BookMyShow Alert", message)


def main():
    validate_config()
    print("BookMyShow monitor started.")
    print(f"- URL: {TARGET_URL}")
    print(f"- Keywords: {KEYWORDS}")
    print(f"- Interval: {INTERVAL_SECONDS}s")
    print("Waiting for availability...")

    last_seen_hit: Optional[str] = None

    while True:
        try:
            html = fetch_text(TARGET_URL)
            hits = text_contains_any(html, KEYWORDS)
            if hits:
                # Build a signature to avoid spamming the same alert repeatedly
                signature = ", ".join(sorted(set(hits)))
                if signature != last_seen_hit:
                    msg = (
                        f"Tickets likely available! Found keywords: {signature}\n"
                        f"URL: {TARGET_URL}"
                    )
                    notify_all(msg)
                    last_seen_hit = signature
                else:
                    print(f"[Info] Still available (keywords: {signature})")
            else:
                print("[Info] Not available yet.")
        except requests.HTTPError as e:
            print(f"[HTTP] {e}")
        except Exception as e:
            print(f"[Error] {e}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
