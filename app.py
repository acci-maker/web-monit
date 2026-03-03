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
