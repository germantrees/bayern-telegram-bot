import os
import time
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID"))
API_KEY = os.getenv("APISPORTS_KEY")

BUNDESLIGA_ID = 78
BAYERN_TEAM_ID = 157

enabled = False
already_alerted = False
last_update_id = None


def log(message):
    print(message, flush=True)


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, data=payload)
    log(f"Telegram sendMessage status: {response.status_code}")


def check_commands():
    global enabled, last_update_id

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 10}

    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    response = requests.get(url, params=params)

    if response.status_code != 200:
        log(f"getUpdates Fehler: {response.status_code}")
        return

    data = response.json()

    for update in data.get("result", []):
        last_update_id = update["update_id"]

        message = update.get("message", {})
        chat = message.get("chat", {})
        text = message.get("text", "").strip().lower()

        log(f"Telegram Befehl empfangen: {text}")

        if str(chat.get("id")) != CHAT_ID:
            log("Falsche Chat-ID ignoriert.")
            continue

        if text in ["/start", "start"]:
            log("START wird ausgeführt.")
            enabled = True
            send_telegram_message("✅ Start wurde empfangen. Bayern Bot wird aktiviert.")

        elif text in ["/stop", "stop", "stopp"]:
            log("STOP wird ausgeführt.")
            enabled = False
            send_telegram_message("⛔ Stopp wurde empfangen. Bayern Bot wird deaktiviert.")

        elif text in ["/status", "status"]:
            log("STATUS wird ausgeführt.")
            if enabled:
                send_telegram_message("✅ Status wurde abgefragt: Bayern Bot ist AKTIV.")
            else:
                send_telegram_message("⛔ Status wurde abgefragt: Bayern Bot ist INAKTIV.")

        elif text in ["/test", "test"]:
            log("TEST wird ausgeführt.")
            send_telegram_message("Goal for Bet")

        else:
            send_telegram_message("Befehl nicht erkannt. Nutze: Start, Stopp, Status oder Test.")


def check_bayern_match():
    global already_alerted

    log("Prüfe Live-Spiele...")

    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        log(f"API-Football Fehler: {response.status_code}")
        return

    data = response.json()

    for match in data.get("response", []):
        league_id = match["league"]["id"]

        if league_id != BUNDESLIGA_ID:
            continue

        home = match["teams"]["home"]
        away = match["teams"]["away"]

        home_id = home["id"]
        away_id = away["id"]

        if BAYERN_TEAM_ID not in [home_id, away_id]:
            continue

        goals_home = match["goals"]["home"]
        goals_away = match["goals"]["away"]

        if goals_home is None or goals_away is None:
            continue

        if home_id == BAYERN_TEAM_ID:
            bayern_goals = goals_home
            opponent_goals = goals_away
        else:
            bayern_goals = goals_away
            opponent_goals = goals_home

        log(f"Bayern Spielstand: Bayern {bayern_goals} - Gegner {opponent_goals}")

        if bayern_goals < opponent_goals:
            if not already_alerted:
                log("Bayern liegt zurück. Alarm wird gesendet.")
                send_telegram_message("Goal for Bet")
                already_alerted = True
        else:
            already_alerted = False


def background_loop():
    log("Bayern Bot gestartet.")

    while True:
        try:
            check_commands()

            if enabled:
                check_bayern_match()

        except Exception as e:
            log(f"Fehler im Loop: {e}")

        time.sleep(10)


@app.route("/")
def home():
    if enabled:
        return "Bayern Bot Running - ACTIVE"
    return "Bayern Bot Running - INACTIVE"


if __name__ == "__main__":
    thread = Thread(target=background_loop)
    thread.daemon = True
    thread.start()

    app.run(host="0.0.0.0", port=10000)
