# Fitbit Air (Obsidian) restock alert

Checks the Google Store India page every 5 minutes. When Obsidian comes back in stock, it sends an alert to your phone that **keeps ringing until you swipe it away**. Tapping the alert opens the store page.

How it works: the store page includes a `schema.org/OutOfStock` or `InStock` tag for each colour. The script reads that tag. If Google changes the page and the tag disappears, you get a normal (non-ringing) "checker needs fixing" notification, so the script can't fail without you knowing.

---

## 1. Phone setup (Galaxy S22 Ultra, about 3 minutes)

1. Install **ntfy** from the Play Store (free, open source).
2. Open it, tap **+**, and subscribe to a topic with a long random name, e.g. `somil-fitbit-7f3k9q2x`.
   Topics on ntfy.sh are public to anyone who knows the name, so don't use something guessable.
3. ntfy **Settings → Notifications → "Keep alerting for highest priority"** → ON.
   This is the important setting. It makes the alert ring until you dismiss it.
4. ntfy Settings → enable **"Override Do Not Disturb"** for max priority (Android will ask for permission).
5. Samsung battery settings, so the app isn't put to sleep:
   Settings → Apps → ntfy → Battery → **Unrestricted**.
   Optional: in the topic's settings inside ntfy, turn on **Instant delivery**.

## 2. Run the checker in the cloud for free (GitHub Actions; your laptop can stay off)

1. Create a **private** GitHub repo (e.g. `fitbit-restock-alert`) and upload `check_stock.py` and `.github/workflows/check.yml`.
   The folder structure must stay the same.
2. Repo → Settings → Secrets and variables → Actions → **New repository secret**
   Name: `NTFY_TOPIC`, value: your topic name from step 1.2.
3. Repo → Actions tab → enable workflows → open "Fitbit Air restock check" → **Run workflow** once.
   The log should show `{'Obsidian': 'OutOfStock', ...}`.

After that it runs on its own every 5 minutes.

**Test the alert first** (from any computer with Python):
```
NTFY_TOPIC=your-topic python3 check_stock.py --test
```
Or open `https://ntfy.sh/your-topic` in a browser, choose priority 5, and publish.
Make sure the test alert keeps ringing until you swipe it away.

## 3. Optional: faster checks

GitHub's 5-minute schedule often runs late by 5–15 minutes. To check every minute or two:

- **When your laptop is on:** `NTFY_TOPIC=your-topic python3 check_stock.py --loop 60`
- **Always on, free:** create a free account at cron-job.org. Make a job that runs every 2 minutes and sends
  `POST https://api.github.com/repos/<you>/fitbit-restock-alert/actions/workflows/check.yml/dispatches`
  with these headers:
  - `Authorization: Bearer <fine-grained GitHub token with Actions: read & write on this repo only>`
  - `Accept: application/vnd.github+json`

  Body: `{"ref":"main"}`

## Notes

- To watch more colours, change `COLOURS: Obsidian` in `check.yml` to e.g. `Obsidian,Fog`.
- While it's in stock, you get a new alert on every run. After you've bought it, go to Actions → the workflow → **⋯ → Disable workflow**.
- Keep Google Store's own "Get notified" turned on as a backup.
