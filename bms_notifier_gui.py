import threading
import time
import requests
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# Desktop notification
try:
    from plyer import notification
except Exception:
    notification = None

# ---------------------- Core monitoring logic ----------------------

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

def fetch_text(url: str, timeout: int = 20) -> str:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def text_contains_any(text: str, needles: List[str]) -> List[str]:
    t = text.lower()
    hits = []
    for s in needles:
        s = (s or "").strip()
        if s and s.lower() in t:
            hits.append(s)
    return hits

def notify_desktop(title: str, message: str):
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=5)
        except Exception:
            pass

def notify_telegram(bot_token: str, chat_id: str, message: str):
    if not (bot_token and chat_id):
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=15)
    except Exception:
        pass

def notify_pushbullet(token: str, title: str, body: str):
    if not token:
        return
    try:
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {"Access-Token": token, "Content-Type": "application/json"}
        payload = {"type": "note", "title": title, "body": body}
        requests.post(url, json=payload, headers=headers, timeout=15)
    except Exception:
        pass

def notify_email(smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, email_to: str,
                 subject: str, body: str):
    if not (smtp_host and smtp_port and smtp_user and smtp_pass and email_to):
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = email_to
        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=20) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, [email_to], msg.as_string())
    except Exception:
        pass

# ---------------------- GUI Application ----------------------

class BMSNotifierApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BookMyShow Ticket Notifier")
        self.geometry("780x640")
        self.resizable(True, True)

        # State
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.last_signature = None
        self.config_data = {}

        self._build_ui()

    def _build_ui(self):
        # Styling
        try:
            self.style = ttk.Style(self)
            if "vista" in self.style.theme_names():
                self.style.theme_use("vista")
            elif "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        wrapper = ttk.Frame(self, padding=12)
        wrapper.pack(fill=tk.BOTH, expand=True)

        # URL
        frm_url = ttk.Frame(wrapper)
        frm_url.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frm_url, text="BookMyShow URL:").pack(anchor="w")
        self.ent_url = ttk.Entry(frm_url)
        self.ent_url.insert(0, "https://m.bookmyshow.com/...")
        self.ent_url.pack(fill=tk.X, expand=True, pady=2)

        # Keywords
        frm_kw = ttk.Frame(wrapper)
        frm_kw.pack(fill=tk.BOTH, pady=(0, 8))
        ttk.Label(frm_kw, text="Keywords (one per line):").pack(anchor="w")
        self.txt_keywords = ScrolledText(frm_kw, height=6, wrap=tk.WORD)
        # Updated defaults with "PVR INOX GSM"
        self.txt_keywords.insert(tk.END, "Book Tickets\n07:30 PM\nPVR INOX GSM")
        self.txt_keywords.pack(fill=tk.BOTH, expand=True, pady=2)

        # Interval
        frm_int = ttk.Frame(wrapper)
        frm_int.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(frm_int, text="Check interval (seconds):").grid(row=0, column=0, sticky="w")
        self.ent_interval = ttk.Entry(frm_int, width=10)
        self.ent_interval.insert(0, "90")
        self.ent_interval.grid(row=0, column=1, padx=(8, 0), sticky="w")

        # Notifications - Group
        notif_frame = ttk.LabelFrame(wrapper, text="Notifications (optional)")
        notif_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 8))

        # Telegram
        frm_tg = ttk.Frame(notif_frame)
        frm_tg.pack(fill=tk.X, pady=6, padx=8)
        ttk.Label(frm_tg, text="Telegram Bot Token:").grid(row=0, column=0, sticky="w")
        self.ent_tg_token = ttk.Entry(frm_tg, width=40)
        self.ent_tg_token.grid(row=0, column=1, sticky="we", padx=6)
        ttk.Label(frm_tg, text="Telegram Chat ID:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.ent_tg_chat = ttk.Entry(frm_tg, width=20)
        self.ent_tg_chat.grid(row=0, column=3, sticky="we", padx=6)
        frm_tg.grid_columnconfigure(1, weight=1)
        frm_tg.grid_columnconfigure(3, weight=1)

        # Pushbullet
        frm_pb = ttk.Frame(notif_frame)
        frm_pb.pack(fill=tk.X, pady=6, padx=8)
        ttk.Label(frm_pb, text="Pushbullet Token:").grid(row=0, column=0, sticky="w")
        self.ent_pb_token = ttk.Entry(frm_pb)
        self.ent_pb_token.grid(row=0, column=1, sticky="we", padx=6)
        frm_pb.grid_columnconfigure(1, weight=1)

        # Email
        frm_em = ttk.Frame(notif_frame)
        frm_em.pack(fill=tk.X, pady=6, padx=8)
        ttk.Label(frm_em, text="SMTP Host:").grid(row=0, column=0, sticky="w")
        self.ent_smtp_host = ttk.Entry(frm_em, width=18)
        self.ent_smtp_host.grid(row=0, column=1, padx=6)

        ttk.Label(frm_em, text="SMTP Port:").grid(row=0, column=2, sticky="w")
        self.ent_smtp_port = ttk.Entry(frm_em, width=8)
        self.ent_smtp_port.insert(0, "587")
        self.ent_smtp_port.grid(row=0, column=3, padx=6)

        ttk.Label(frm_em, text="SMTP User:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.ent_smtp_user = ttk.Entry(frm_em)
        self.ent_smtp_user.grid(row=1, column=1, padx=6, pady=(6, 0), sticky="we")

        ttk.Label(frm_em, text="SMTP Pass:").grid(row=1, column=2, sticky="w", pady=(6, 0))
        self.ent_smtp_pass = ttk.Entry(frm_em, show="*")
        self.ent_smtp_pass.grid(row=1, column=3, padx=6, pady=(6, 0), sticky="we")

        ttk.Label(frm_em, text="Email To:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.ent_email_to = ttk.Entry(frm_em)
        self.ent_email_to.grid(row=2, column=1, padx=6, pady=(6, 0), sticky="we")

        frm_em.grid_columnconfigure(1, weight=1)
        frm_em.grid_columnconfigure(3, weight=1)

        # Controls
        frm_ctrl = ttk.Frame(wrapper)
        frm_ctrl.pack(fill=tk.X, pady=(0, 8))
        self.btn_start = ttk.Button(frm_ctrl, text="Start Monitoring", command=self.on_start)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_stop = ttk.Button(frm_ctrl, text="Stop", command=self.on_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        # Log area
        frm_log = ttk.LabelFrame(wrapper, text="Status")
        frm_log.pack(fill=tk.BOTH, expand=True)
        self.txt_log = ScrolledText(frm_log, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Footer
        footer = ttk.Label(
            wrapper,
            text="Tip: Use the mobile page (m.bookmyshow.com) and precise keywords (e.g., a showtime or venue like PVR INOX GSM).",
            foreground="#666"
        )
        footer.pack(anchor="w", pady=(6, 0))

    def log(self, msg: str):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def on_start(self):
        url = self.ent_url.get().strip()
        keywords_raw = self.txt_keywords.get("1.0", tk.END)
        keywords = [k.strip() for k in keywords_raw.splitlines() if k.strip()]
        try:
            interval = int(self.ent_interval.get().strip() or "90")
        except ValueError:
            messagebox.showerror("Invalid Interval", "Please enter a valid number of seconds.")
            return

        if not url:
            messagebox.showerror("Missing URL", "Please enter a BookMyShow URL.")
            return
        if not keywords:
            messagebox.showerror("Missing Keywords", "Please enter at least one keyword.")
            return
        if interval < 15:
            if not messagebox.askyesno("Low Interval", "Interval is quite low. Continue anyway?"):
                return

        # Gather optional notifications
        self.config_data = {
            "url": url,
            "keywords": keywords,
            "interval": interval,
            "telegram_token": self.ent_tg_token.get().strip(),
            "telegram_chat": self.ent_tg_chat.get().strip(),
            "pushbullet_token": self.ent_pb_token.get().strip(),
            "smtp_host": self.ent_smtp_host.get().strip(),
            "smtp_port": self.ent_smtp_port.get().strip(),
            "smtp_user": self.ent_smtp_user.get().strip(),
            "smtp_pass": self.ent_smtp_pass.get().strip(),
            "email_to": self.ent_email_to.get().strip(),
        }

        self.stop_flag.clear()
        self.last_signature = None
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.log("Monitoring started.")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def on_stop(self):
        self.stop_flag.set()
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)
        self.log("Stopping...")

    def _monitor_loop(self):
        url = self.config_data["url"]
        keywords = self.config_data["keywords"]
        interval = self.config_data["interval"]
        tg_token = self.config_data["telegram_token"]
        tg_chat = self.config_data["telegram_chat"]
        pb_token = self.config_data["pushbullet_token"]
        smtp_host = self.config_data["smtp_host"]
        smtp_port = self.config_data["smtp_port"]
        smtp_user = self.config_data["smtp_user"]
        smtp_pass = self.config_data["smtp_pass"]
        email_to = self.config_data["email_to"]

        while not self.stop_flag.is_set():
            try:
                html = fetch_text(url)
                hits = text_contains_any(html, keywords)
                if hits:
                    signature = ", ".join(sorted(set(hits)))
                    if signature != self.last_signature:
                        self.last_signature = signature
                        msg = f"Tickets likely available! Found keywords: {signature}\n{url}"
                        self.log(f"ALERT: {signature}")
                        notify_desktop("BookMyShow Alert", msg)
                        notify_telegram(tg_token, tg_chat, msg)
                        notify_pushbullet(pb_token, "BookMyShow Alert", msg)
                        try:
                            smtp_port_int = int(smtp_port) if smtp_port else 0
                        except Exception:
                            smtp_port_int = 0
                        notify_email(smtp_host, smtp_port_int, smtp_user, smtp_pass, email_to,
                                     "BookMyShow Alert", msg)
                    else:
                        self.log(f"Still available (keywords: {signature})")
                else:
                    self.log("Not available yet.")
            except requests.HTTPError as e:
                self.log(f"HTTP error: {e}")
            except Exception as e:
                self.log(f"Error: {e}")

            # Sleep in small chunks so Stop responds quickly
            total_sleep = 0
            while total_sleep < interval and not self.stop_flag.is_set():
                time.sleep(0.5)
                total_sleep += 0.5

        self.log("Monitoring stopped.")

if __name__ == "__main__":
    app = BMSNotifierApp()
    app.mainloop()
