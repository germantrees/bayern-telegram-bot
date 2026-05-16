import os
import time
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)

# =========================================
# ENV VARS
# =========================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("APISPORTS_KEY")

# =========================================
# SETTINGS
# =========================================

BUNDESLIGA_ID = 78
BAYERN_TEAM_ID = 157

enabled = True
already_alerted = False

# =========================================
# TELEGRAM SEND
# =========================================

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, data=payload)

# =========================================
# CHECK MATCH
# =========================================

def check_bayern_match():
    global already_alerted

    url = "https://v3.football.api-sports.io/fixtures?live=all"

    headers = {
        "x-apisports-key": API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return

    data = response.json()

    fixtures = data.get("response", [])

    for match in fixtures:

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

        bayern_goals = 0
        opponent_goals = 0

        if home_id == BAYERN_TEAM_ID:
            bayern_goals = goals_home
            opponent_goals = goals_away
        else:
            bayern_goals = goals_away
            opponent_goals = goals_home

        if bayern_goals < opponent_goals:

            if not already_alerted:
                send_telegram_message("Goal for Bet")
                already_alerted = True

        else:
            already_alerted = False

# =========================================
# BOT LOOP
# =========================================

def background_loop():
    while True:

        if enabled:
            try:
                check_bayern_match()
            except Exception as e:
                print(e)

        time.sleep(60)

# =========================================
# SIMPLE WEB SERVER
# =========================================

@app.route("/")
def home():
    return "Bayern Bot Running"

# =========================================
# START
# =========================================

if __name__ == "__main__":

    thread = Thread(target=background_loop)
    thread.start()

    app.run(host="0.0.0.0", port=10000)
