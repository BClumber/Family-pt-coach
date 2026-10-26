# Family PT Coach

Daily physical-therapy check-off app for the family.

- **3-day rotation that repeats** — Day 1 legs & hips, Day 2 spine & abs, Day 3 arms. The next workout always follows the last one done, so a missed day doesn't skip a body area. More days can be added in the app.
- **Reps go up 2 every week** (per person setting; any exercise can be set to stay fixed, e.g. stretches).
- Check off each exercise, demo animation or your own video per exercise, guided hold/rep/rest timer, pain 0–10 and notes, week grid.
- One family passcode (`FAMILY_CODE`), entered once per phone.

## Where data lives
Everything is stored **on each phone** (browser storage + IndexedDB for uploaded videos). The server stores nothing.
Use **Settings → Save backup** now and then; **Restore backup** loads it on a new phone. Uploaded videos are not in the backup.

## Hosting (Render, free plan)
`render.yaml` is a Blueprint: Render → New → Blueprint → pick this repo → enter `FAMILY_CODE` → Deploy.
The free plan sleeps after ~15 minutes idle; the first open after that takes ~30–50 s. Once the app has been added to the home screen it opens from the saved copy even offline.

## Files
- `server.js` — no-dependency Node server: passcode gate, static files, video byte ranges.
- `public/index.html` — the whole app.
- `public/sw.js` — offline support.
- `public/demos/*.mp4` — demo animations; `tools/render-demos.py` renders them (Python + Pillow + ffmpeg). To add a demo, add a clip there and an entry in `DEMOS` in `index.html`.
