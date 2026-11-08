# Family PT Coach

Weekly physical-therapy schedule for the family.

- **Weekly schedule** on the workout days you pick (default Mon, Tue, Thu, Fri). Days alternate: legs, hips & core + lower-body stretches, then shoulders & arms + back stretches + walking, so each muscle group gets at least a day off between sessions. "Rebuild my week" re-does the layout; you can also place exercises by hand (the app warns about back-to-back days for the same muscles).
- **Reps go up 2 every week** (per-person setting); stretches stay the same.
- **Sore? Move it** on any exercise moves it to the best later day (no same muscle group that day or the day before) or skips it this week. **Take today off** moves the day's workout to the next rest day.
- Missed exercises from a partly done day carry over until done, after the muscle has had a day's rest.
- Demo animations or your own video per exercise, guided hold/rep/rest timer, pain 0–10 and notes, week grid, history, edit past days.
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
- `tests/app.test.js` — end-to-end checks (`npm test` with the server running on port 3999).
- `public/sw.js` — offline support.
- `public/demos/*.mp4` — demo animations; `tools/render-demos.py` renders them (Python + Pillow + ffmpeg). To add a demo, add a clip there and an entry in `DEMOS` in `index.html`.
