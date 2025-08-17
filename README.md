# BookMyShow Ticket Notifier

Two Python scripts to notify when tickets for a particular event on BookMyShow likely open:

- Console script: bms_notifier.py
- GUI app: bms_notifier_gui.py

Both look for specific keywords on the event page (e.g., “Book Tickets”, “07:30 PM”, “PVR INOX GSM”) and send alerts when matches are found.

Important
- Prefer mobile URLs (m.bookmyshow.com) for simpler HTML that often includes booking text and showtimes.
- Keep polling intervals polite (60–180s) to avoid rate-limiting.
- Choose keywords that only appear when booking is open to reduce false positives.

## Features

- Checks a target BookMyShow event page at fixed intervals.
- Detects ticket availability using user-defined keywords.
- Multiple notifications:
  - Console (always on)
  - Telegram (optional)
  - Pushbullet (optional)
  - Email via SMTP (optional)
- GUI version includes:
  - Inputs for URL, keywords, interval
  - Start/Stop controls
  - Live log window
  - Desktop notification (using plyer)

## Requirements

- Python 3.8+
- Console script dependencies:
  - requests
- GUI script dependencies:
  - requests
  - plyer (for desktop notifications)

Install dependencies:
- Console: pip install requests
- GUI: pip install requests plyer

## Usage

### 1) Console script (bms_notifier.py)

1. Open bms_notifier.py and edit the CONFIG section at the top:
   - TARGET_URL: Set to the exact BookMyShow event URL (prefer m.bookmyshow.com).
   - KEYWORDS: List of strings to detect (default includes “PVR INOX GSM”).
   - INTERVAL_SECONDS: Recommended 60–180.

2. Optional notifications:
   - Telegram: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
   - Pushbullet: set PUSHBULLET_TOKEN.
   - Email (Gmail example): set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO.
     - Use an app password and enable 2FA for security.

3. Run:
   - python bms_notifier.py

4. Behavior:
   - The script prints status updates.
   - When any keyword is found, it sends alerts through enabled channels.
   - It avoids spamming repeated alerts by tracking the last matched set of keywords.

### 2) GUI app (bms_notifier_gui.py)

1. Run:
   - python bms_notifier_gui.py

2. In the app:
   - Enter the BookMyShow URL.
   - Enter keywords (one per line). Defaults include:
     - Book Tickets
     - 07:30 PM
     - PVR INOX GSM
   - Set the interval (seconds).
   - Optionally fill Telegram, Pushbullet, and Email settings.
   - Click Start Monitoring to begin, Stop to end.

3. Behavior:
   - Logs status messages in the window.
   - Pops a desktop notification when matches are found.
   - Sends Telegram/Pushbullet/Email if configured.

## Configuration Tips

- URL:
  - Use the city-specific, mobile page URL for the event or venue (e.g., https://m.bookmyshow.com/<city>/movies/<movie>/<event-id>).
- Keywords:
  - Use a showtime (e.g., 07:30 PM), venue name (e.g., PVR INOX GSM), or booking prompt (Book Tickets).
  - Add multiple keywords to increase reliability.
- Interval:
  - 60–180 seconds is a good balance between responsiveness and politeness.

## Notifications

- Telegram:
  - Create a bot using @BotFather to get TELEGRAM_BOT_TOKEN.
  - Retrieve TELEGRAM_CHAT_ID by sending a message to your bot and checking getUpdates for chat.id.
- Pushbullet:
  - Create an access token in your Pushbullet account and set PUSHBULLET_TOKEN.
- Email (Gmail example):
  - SMTP_HOST: smtp.gmail.com
  - SMTP_PORT: 587
  - SMTP_USER: your Gmail address
  - SMTP_PASS: app password (not your normal password)
  - EMAIL_TO: destination email address

## Troubleshooting

- No alerts even when tickets are open:
  - Verify the URL is the correct mobile version with city context.
  - View page source and confirm your keywords appear in the HTML (not injected dynamically).
  - Try different or more specific keywords (exact showtime or venue string).
- Too many false positives:
  - Use more specific keywords that only appear after bookings open.
- Network/HTTP errors:
  - Temporary server issues or rate-limiting; increase INTERVAL_SECONDS.
- Desktop notifications not showing (GUI):
  - Ensure OS notifications are enabled for Python apps, or rely on Telegram/Email/Pushbullet.

## Security

- Do not commit personal tokens or passwords to version control.
- If using the console script in hosted environments, store secrets using environment variables or secret management tools.
- Use app passwords for email and enable two-factor authentication where possible.

## Disclaimer

- This tool performs polite polling of publicly accessible pages and does not bypass authentication.
- Respect the website’s terms and avoid aggressive scraping behavior. Adjust intervals responsibly.

## Quick Start Examples

Console
- Edit bms_notifier.py:
  - TARGET_URL = "https://m.bookmyshow.com/bengaluru/movies/your-movie/event-id"
  - KEYWORDS = ["Book Tickets", "07:30 PM", "PVR INOX GSM"]
  - INTERVAL_SECONDS = 90
- Run: python bms_notifier.py

GUI
- Run: python bms_notifier_gui.py
- Paste URL, keep default keywords (includes PVR INOX GSM), set interval to 90, click Start Monitoring.

