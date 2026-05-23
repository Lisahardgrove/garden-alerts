"""
Garden Weather Alerts — Rupert, Vermont
----------------------------------------
Checks the forecast each morning and sends a Pushover notification to your
phone ONLY when the weather is an outlier that changes the daily routine
(the garden is watered every day by default, so "water as usual" days are
silent).

Season-aware: outdoor growing season is mid-May to early October. Outside
that window the app stays completely silent.

Each notification gives you, in plain English:
  - what's happening and what you should know
  - a ready-to-send message for staff (paste into your translation app)

Staff messages use short, simple sentences — one idea per sentence — so they
translate cleanly and are easy to read.

You do not need to edit any code to run this. The only things you set are
two secrets (your Pushover keys), and those go in Render's dashboard, NOT in
this file. See README.md.

If you ever want to TUNE the behavior, every adjustable number and message is
in the clearly-marked CONFIG section directly below. Nothing else needs to be
touched.
"""

import os
import sys
import datetime
import urllib.request
import urllib.parse
import json

# =====================================================================
# ============================  CONFIG  ===============================
# =====  Everything you might ever want to change lives here.  ========
# =====================================================================

# --- Your location (Rupert, VT) ---
LATITUDE = 43.27
LONGITUDE = -73.22
LOCATION_NAME = "Rupert, VT"

# --- Growing season (no alerts outside this window) ---
# Months are numbers: 1=Jan, 5=May, 10=Oct, 12=Dec.
# Default: mid-May (5/15) through early October (10/7).
SEASON_START = (5, 15)   # (month, day)
SEASON_END   = (10, 7)   # (month, day)

# --- Alert thresholds (degrees Fahrenheit, inches, mph) ---
# Tweak these after a season if you want more or fewer alerts.
FROST_LOW_F        = 38   # below this overnight low -> frost risk
HARD_FROST_LOW_F   = 34   # below this -> hard frost
FREEZE_LOW_F       = 28   # below this -> freeze
HEAT_HIGH_F        = 1   # at/above this high -> water more / earlier
EXTREME_HEAT_F     = 90   # at/above this -> extreme heat
SKIP_WATER_RAIN_IN = 0.5  # forecast rain (inches) at/above which to skip watering
HEAVY_RAIN_IN      = 1.0  # forecast rain at/above which to check beds/erosion
HIGH_WIND_GUST_MPH = 30   # gusts at/above this -> secure plants

# --- The name you address staff messages to ---
STAFF_NAME = "Rosa & Mario"

# --- Your messages (all English) ---
# Each alert has:
#   title    -> short push-notification headline you see on your phone
#   body_en  -> what's happening / what you should know (for you)
#   staff    -> message to send staff, in simple English. Short sentences,
#               one idea each. Paste into your translation app, then send.
#               The {name} placeholder fills in STAFF_NAME.
MESSAGES = {
    "freeze": {
        "title": "🥶 GARDEN: FREEZE tonight — act today",
        "body_en": (
            "Freeze forecast overnight. Protect everything tender and harvest "
            "what's ready. Cold air pools at the bottom — raised bed first, then "
            "lower beds 5 & 6, then the rest."
        ),
        "staff": (
            "Hi {name}! Tonight it will freeze. We need to cover all the plants "
            "before dark. Please start with the raised bed at the bottom. It has "
            "strawberries, onion, and kale. The cold hits there first. Then cover "
            "beds 5 and 6. Then cover the rest, including the tomatoes in bed 7 and "
            "the mini field. Please also pick any vegetables that are ready today. "
            "Use plastic or sheets. Cover the plants well so the wind does not blow "
            "them off. Thank you so much!"
        ),
    },
    "hard_frost": {
        "title": "❄️ GARDEN: Hard frost tonight — cover crops",
        "body_en": (
            "Hard frost forecast. Cover ALL frost-sensitive crops, including the "
            "tomatoes at the top (bed 7) and the mini field. Raised bed at the "
            "bottom is most at risk — do it first."
        ),
        "staff": (
            "Hi {name}! Tonight there will be a hard frost. We need to cover all "
            "the plants. This includes the tomatoes at the top in bed 7. It also "
            "includes the mini field. Please start with the raised bed at the "
            "bottom. It has strawberries, onion, and kale. The cold hits there "
            "first. Then cover beds 5 and 6. Use plastic or old sheets. Cover the "
            "plants well so the wind does not blow them off. Please do this before "
            "dark. Thank you so much!"
        ),  # (unchanged from your version)
    },
    "frost": {
        "title": "🌡️ GARDEN: Frost risk tonight",
        "body_en": (
            "Frost possible at the bottom of the slope tonight. Cover tender crops "
            "in the raised bed and lower beds (5 & 6). Tomatoes at the top (bed 7) "
            "and the mini field should be OK but worth a check."
        ),
        "staff": (
            "Hi {name}! Tonight there may be frost at the bottom of the garden. "
            "Please cover the plants before dark. The most important is the raised "
            "bed at the bottom. It has strawberries, onion, and kale. Also cover "
            "garden beds 5 and 6. The tomatoes at the top in bed 7 should be fine. "
            "The mini field should be fine too. But please check them if you can. "
            "Use plastic or sheets. Thank you so much!"
        ),
    },
    "extreme_heat": {
        "title": "🔥 GARDEN: Extreme heat — water deeply, very early",
        "body_en": (
            "Extreme heat forecast. Water deeply at first light, not midday. "
            "Tomatoes, peppers, eggplant may drop blossoms. Mini field "
            "(south-facing) and bed 7 are most exposed."
        ),
        "staff": (
            "Hi {name}! Today will be very hot. Please water a lot. Water early in "
            "the morning and not at midday. The heat is very hard on the tomatoes, "
            "peppers, and eggplant. Please give them extra water, and the mini "
            "field as well. Thank you so much!"
        ),
    },
    "heat": {
        "title": "☀️ GARDEN: Hot day — water more, water early",
        "body_en": (
            "Hot day ahead. Water more than usual and do it early morning before "
            "the sun is strong. Watch the mini field and bed 7 (most sun-exposed)."
        ),
        "staff": (
            "Hi {name}! Today will be hot. Please water more than usual. Water "
            "early in the morning, before the sun is strong. Please give the "
            "tomatoes, peppers, and eggplant extra water, and the mini field as "
            "well. Thank you so much!"
        ),
    },
    "skip_water": {
        "title": "🌧️ GARDEN: Rain coming — skip watering today",
        "body_en": (
            "Significant rain forecast. Skip today's watering; the rain will cover "
            "it. Check the raised bed at the bottom afterward for pooling."
        ),
        "staff": (
            "Hi {name}! Today it will rain a lot. You do not need to water today. "
            "The rain will do it. After the rain, please check the beds to see if "
            "water has collected. If you see a lot of water, please tell me so we "
            "can find a solution. Thank you so much!"
        ),
    },
    "heavy_rain": {
        "title": "⛈️ GARDEN: Heavy rain — check beds after",
        "body_en": (
            "Heavy rain forecast. Skip watering. After it passes, check the lower "
            "beds and raised bed for pooling and erosion, and check corn/tomatoes "
            "for damage."
        ),
        "staff": (
            "Hi {name}! Today there will be heavy rain. Please do not water. After "
            "the rain stops, please check the beds for standing water and if any "
            "soil has washed away. Please also check the mini field. Please tell me "
            "what you find. Thank you so much!"
        ),
    },
    "high_wind": {
        "title": "💨 GARDEN: Strong wind — secure plants",
        "body_en": (
            "Strong wind gusts forecast. Stake/tie tomatoes and check the corn in "
            "the mini field for lodging risk. Secure anything covered or loose."
        ),
        "staff": (
            "Hi {name}! Today there will be strong wind. Please check the "
            "trellises and make sure all the vegetables are tied well to their "
            "stakes. Then check the corn in the mini field. Strong wind can knock "
            "it down. If you see anything loose, please tie it down before the wind "
            "comes. Thank you so much!"
        ),
    },
}

# Priority order: if multiple conditions hit on the same day, we send the most
# urgent one (top of this list wins). Cold emergencies beat everything.
PRIORITY = [
    "freeze",
    "hard_frost",
    "frost",
    "extreme_heat",
    "heavy_rain",
    "high_wind",
    "heat",
    "skip_water",
]

# =====================================================================
# =========================  END CONFIG  ==============================
# ===========  You don't need to edit anything below.  ================
# =====================================================================


def in_season(today):
    """True if today's date is within the outdoor growing season."""
    start = datetime.date(today.year, SEASON_START[0], SEASON_START[1])
    end = datetime.date(today.year, SEASON_END[0], SEASON_END[1])
    return start <= today <= end


def get_forecast():
    """
    Fetch the next ~36h forecast from the National Weather Service.
    Returns a dict with the day's high, tonight's low, max rain, max gust.
    Uses only the Python standard library (no installs needed).
    """
    headers = {"User-Agent": "garden-alerts (personal use)"}

    # Step 1: get the gridpoint for our coordinates
    points_url = f"https://api.weather.gov/points/{LATITUDE},{LONGITUDE}"
    grid = _get_json(points_url, headers)
    forecast_url = grid["properties"]["forecast"]
    hourly_url = grid["properties"]["forecastHourly"]

    # Step 2: pull the period forecast (day/night blocks) for temps
    periods = _get_json(forecast_url, headers)["properties"]["periods"]

    day_high = None
    night_low = None
    for p in periods[:4]:
        if p["isDaytime"] and day_high is None:
            day_high = p["temperature"]
        if not p["isDaytime"] and night_low is None:
            night_low = p["temperature"]

    # Step 3: pull hourly for wind gusts and rain amount over next 24h
    hourly = _get_json(hourly_url, headers)["properties"]["periods"][:24]
    max_gust = 0
    total_rain = 0.0
    for h in hourly:
        gust = _parse_speed(h.get("windGust") or h.get("windSpeed") or "0 mph")
        max_gust = max(max_gust, gust)
        amt = h.get("quantitativePrecipitation", {})
        val = amt.get("value")
        if val:
            total_rain += val / 25.4  # mm -> inches

    return {
        "high_f": day_high,
        "low_f": night_low,
        "rain_in": round(total_rain, 2),
        "gust_mph": max_gust,
    }


def _get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _parse_speed(text):
    """Pull the largest number out of a string like '20 to 30 mph'."""
    nums = [int(s) for s in text.replace("mph", "").replace("to", " ").split() if s.isdigit()]
    return max(nums) if nums else 0


def decide_alerts(fc):
    """Return the list of triggered alert keys for this forecast."""
    hits = []
    low = fc["low_f"]
    high = fc["high_f"]
    rain = fc["rain_in"]
    gust = fc["gust_mph"]

    if low is not None:
        if low < FREEZE_LOW_F:
            hits.append("freeze")
        elif low < HARD_FROST_LOW_F:
            hits.append("hard_frost")
        elif low < FROST_LOW_F:
            hits.append("frost")

    if high is not None:
        if high >= EXTREME_HEAT_F:
            hits.append("extreme_heat")
        elif high >= HEAT_HIGH_F:
            hits.append("heat")

    if rain >= HEAVY_RAIN_IN:
        hits.append("heavy_rain")
    elif rain >= SKIP_WATER_RAIN_IN:
        hits.append("skip_water")

    if gust >= HIGH_WIND_GUST_MPH:
        hits.append("high_wind")

    return hits


def pick_top(hits):
    """Choose the single most urgent alert to send today."""
    for key in PRIORITY:
        if key in hits:
            return key
    return None


def send_pushover(title, message):
    """Send one push notification via Pushover."""
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    if not token or not user:
        print("ERROR: PUSHOVER_TOKEN / PUSHOVER_USER not set in environment.")
        sys.exit(1)

    data = urllib.parse.urlencode({
        "token": token,
        "user": user,
        "title": title,
        "message": message,
        "priority": 0,
    }).encode()

    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        print("Pushover response:", r.status)


def build_message(key):
    """Assemble the full notification body from a message template."""
    m = MESSAGES[key]
    name = STAFF_NAME
    return m["title"], (
        f"{m['body_en'].strip()}\n\n"
        f"--- MESSAGE TO SEND {name.upper()} (copy, translate, send) ---\n"
        f"{m['staff'].format(name=name).strip()}"
    )


def main():
    today = datetime.date.today()

    # Season gate: silent outside the growing window.
    if not in_season(today):
        print(f"{today}: out of season ({SEASON_START}-{SEASON_END}). No check.")
        return

    try:
        fc = get_forecast()
    except Exception as e:
        print("Forecast fetch failed:", e)
        return

    print(f"{today} forecast for {LOCATION_NAME}: {fc}")

    hits = decide_alerts(fc)
    if not hits:
        print("Normal conditions — water as usual. No notification sent.")
        return

    key = pick_top(hits)
    title, message = build_message(key)
    print(f"Sending alert: {key}")
    send_pushover(title, message)


if __name__ == "__main__":
    main()
