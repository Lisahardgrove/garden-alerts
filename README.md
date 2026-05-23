# Garden Weather Alerts — Setup Guide

This app checks the weather in Rupert, VT every morning at 6 AM and sends a
push notification to your phone **only** when there's an outlier worth acting
on (frost, freeze, heat, heavy rain, strong wind). On normal days it stays
silent — your garden gets watered daily as usual, so there's nothing to say.

It is completely silent outside the growing season (mid-May to early October),
so no tomato alerts in February.

Each notification includes, all in English:
- What's happening and what to do (for you)
- A ready-to-send message for staff — paste it into your translation app,
  then send the result

You do **not** need to know how to code to set this up. It's three accounts,
some copy/pasting, and about 30 minutes once.

---

## What you'll need
1. A free **GitHub** account (stores the app's files)
2. A free **Render** account (runs the daily check)
3. **Pushover** on your phone (receives the notifications — $5 one-time, no subscription)

---

## STEP 1 — Pushover (your phone, ~5 min)

1. Install the **Pushover** app from the App Store / Google Play.
2. Create an account in the app and complete the $5 one-time purchase
   (there's a 30-day free trial first if you want to test before paying).
3. On the app's main screen you'll see **"Your User Key"** — a long string of
   letters and numbers. Write it down. This is your `PUSHOVER_USER`.
4. Go to **pushover.net** in a browser, log in, scroll to **"Create an
   Application/API Token"**, name it "Garden Alerts", and create it. It gives
   you an **API Token**. Write it down. This is your `PUSHOVER_TOKEN`.

You now have two keys. Keep them handy for Step 4.

---

## STEP 2 — Put the app on GitHub (~10 min)

1. Go to **github.com** and create a free account if you don't have one.
2. Click the **+** in the top-right → **New repository**.
3. Name it `garden-alerts`, leave it Public, click **Create repository**.
4. On the new repo page, click **"uploading an existing file"**.
5. Drag in all four files from this folder:
   - `app.py`
   - `requirements.txt`
   - `render.yaml`
   - `README.md`
6. Click **Commit changes**.

Your app now lives on GitHub.

---

## STEP 3 — Connect Render (~10 min)

1. Go to **render.com** and sign up — choose **"Sign in with GitHub"** so they
   can see your repo.
2. On the Render dashboard, click **New +** → **Blueprint**.
3. Select your `garden-alerts` repository.
4. Render reads `render.yaml` and shows it'll create a **cron job** called
   "garden-weather-alerts." Click **Apply**.

---

## STEP 4 — Add your two keys (~3 min)

1. In Render, open the **garden-weather-alerts** job.
2. Go to the **Environment** tab.
3. You'll see `PUSHOVER_TOKEN` and `PUSHOVER_USER` waiting for values.
4. Paste in the two keys from Step 1. Save.

Done. From now on it runs every morning at 6 AM Eastern automatically.

---

## STEP 5 — Test it right now (~2 min)

You don't have to wait for real bad weather to confirm it works:

1. In Render, open the job and click **"Trigger Run"** (or "Run now").
2. Watch the **Logs** tab. You'll see the forecast it pulled and whether it
   decided to send anything.
3. If conditions happen to be normal, it won't send — that's correct. To force
   a test notification, you can temporarily lower a threshold (see "Tuning"
   below), trigger a run, then change it back.

---

## TUNING (optional — only if you want to adjust it later)

Open `app.py` on GitHub and click the pencil ✏️ to edit. Everything adjustable
is at the top in the **CONFIG** section, clearly marked:

- **Thresholds**: change `FROST_LOW_F`, `HEAT_HIGH_F`, etc. to get more or
  fewer alerts.
- **Season**: change `SEASON_START` / `SEASON_END` if you plant earlier under
  cover or run later.
- **Messages**: edit any of the English text in the `MESSAGES` section. The
  `{name}` fills in automatically. (You send these through your own translation
  app, so they're written in plain English.)
- **Staff name**: change `STAFF_NAME = "Rosa"` to whoever you're sending to.

After editing, click **Commit changes** on GitHub. Render picks up the change
automatically — nothing else to do.

---

## If something seems off
- **No notifications ever**: check that both keys are in Render's Environment
  tab, and that today's date is inside the growing season.
- **Want a different check time**: edit the `schedule` line in `render.yaml`
  (it's in UTC; 10:00 UTC = 6 AM Eastern in summer).
- **Forecast fetch failed in the logs**: usually a temporary NWS hiccup; it'll
  try again the next morning. If it persists, the NWS service may be down.
