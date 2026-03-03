import socket
import requests
import hashlib
import smtplib
import os
from flask import Flask, Response
import requests.packages.urllib3.util.connection as urllib3_cn

# ---- Netzwerk: IPv4 erzwingen (ok für Render)
def force_ipv4():
    urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

force_ipv4()

app = Flask(__name__)

# ---- Monitoring
URL_TO_MONITOR = "https://www.marathondumedoc.com/en/registration-global/"
HASH_FILE = "last_hash.txt"

# ---- Mail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]   # App-Passwort!
EMAIL_TO   = os.environ["EMAIL_TO"]

# ---- Realistischer Browser-Header (sehr wichtig)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

# ---- Mail senden
def send_email(subject, body):
    msg = f"Subject: {subject}\n\n{body}"
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.sendmail(EMAIL_USER, EMAIL_TO, msg)

# ---- Seite abrufen & hashen
def get_hash():
    r = requests.get(URL_TO_MONITOR, headers=HEADERS, timeout=30)

    # 👉 Wichtig: Rate Limit sauber behandeln
    if r.status_code == 429:
        print("RATE LIMITED (429) – Skip this run")
        return None

    r.raise_for_status()
    return hashlib.sha256(r.text.encode("utf-8")).hexdigest()

@app.route("/")
def index():
    return "Service läuft. Verwende /check"

@app.route("/check")
def check():
    try:
        new_hash = get_hash()

        # Wenn Rate-Limit → kein Fehler für Cronjob
        if new_hash is None:
            return Response("RATE LIMITED – TRY LATER", status=200)

        old_hash = None
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                old_hash = f.read().strip()

        # Änderung erkannt
        if old_hash and new_hash != old_hash:
            send_email(
                "🔔 Webseite geändert",
                f"Änderung erkannt:\n{URL_TO_MONITOR}"
            )
            result = "CHANGED"
        else:
            result = "NO CHANGE"

        # Hash immer aktualisieren
        with open(HASH_FILE, "w") as f:
            f.write(new_hash)

        return Response(result, status=200)

    except Exception as e:
        # 👉 Cronjob darf NICHT fehlschlagen
        print("CHECK ERROR:", e)
        return Response("ERROR LOGGED", status=200)
