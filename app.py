import requests
import hashlib
import smtplib
import os
from flask import Flask, Response

app = Flask(__name__)

URL_TO_MONITOR = "https://www.kicker.de"
HASH_FILE = "last_hash.txt"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO   = os.environ["EMAIL_TO"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Website Monitoring Script)"
}

def send_email(subject, body):
    msg = f"Subject: {subject}\n\n{body}"
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.sendmail(EMAIL_USER, EMAIL_TO, msg)

def get_hash():
    r = requests.get(URL_TO_MONITOR, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return hashlib.sha256(r.text.encode()).hexdigest()

@app.route("/")
def index():
    return "Service läuft. Verwende /check"

@app.route("/check")
def check():
    try:
        new_hash = get_hash()
    except Exception as e:
        return Response(f"FETCH ERROR: {e}", status=500)

    try:
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                old_hash = f.read()

            if new_hash != old_hash:
                send_email(
                    "🔔 Webseite geändert",
                    f"Änderung erkannt:\n{URL_TO_MONITOR}"
                )
                with open(HASH_FILE, "w") as f:
                    f.write(new_hash)
                return Response("CHANGED", status=200)
        else:
            with open(HASH_FILE, "w") as f:
                f.write(new_hash)

        return Response("NO CHANGE", status=200)

    except Exception as e:
        return Response(f"LOGIC ERROR: {e}", status=500)
