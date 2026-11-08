"""Demo clips: chair squat, band row, counter push-up. Uses the helpers in render-demos.py.
Usage: python3 render_basics.py OUT_DIR [stills] [names...]"""
import math, os, sys, importlib.util
spec = importlib.util.spec_from_file_location("rd", os.path.join(os.path.dirname(__file__), "render-demos.py"))
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
from math import ceil
Frame, view, ik, pol, lerp, ease, timeline = rd.Frame, rd.view, rd.ik, rd.pol, rd.lerp, rd.ease, rd.timeline
NEAR, FAR, HOLD, INK, MAT, SS = rd.NEAR, rd.FAR, rd.HOLD, rd.INK, rd.MAT, rd.SS
THIGH, SHIN, FOOT, TORSO, UARM, FARM = rd.THIGH, rd.SHIN, rd.FOOT, rd.TORSO, rd.UARM, rd.FARM
ARM = UARM + FARM


def cyc(t, segs):
    L = sum(d for _, d in segs); rep = int(t // L)
    name, u, left = timeline(segs, t % L)
    k = {"rest": 0, "go": ease(u), "hold": 1, "back": 1 - ease(u)}[name]
    return name, k, left, rep, L


def floorline(f):
    f.d.line([0, (rd.FLOOR_Y + 2) * SS, rd.W * SS, (rd.FLOOR_Y + 2) * SS], fill=rd.FLOOR, width=3 * SS)


def box(f, x0, y0, x1, y1, col=MAT):
    a = rd.P(x0, y1); b = rd.P(x1, y0)
    f.d.rectangle([a[0], a[1], b[0], b[1]], fill=col)


def chair_squat(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.6), ("hold", .5), ("back", 1.4)])
    view(0.72, 430); f = Frame(); floorline(f)
    # chair (seat, legs, back)
    box(f, 300, 150, 420, 166); box(f, 304, 0, 316, 150); box(f, 404, 0, 416, 150); box(f, 300, 166, 314, 330)
    ank = (470, 12)
    hip = (lerp(470, 400, k), lerp(12 + THIGH + SHIN - 6, 178, k))
    lean = lerp(4, 38, k)  # torso tilt forward from vertical, degrees
    sh = (hip[0] + TORSO * math.sin(math.radians(lean)), hip[1] + TORSO * math.cos(math.radians(lean)))
    for col, dx in ((FAR, -6), (NEAR, 0)):
        h2 = (hip[0] + dx, hip[1]); a2 = (ank[0] + dx, ank[1])
        k1, k2 = ik(h2, a2, THIGH, SHIN, 1), ik(h2, a2, THIGH, SHIN, -1)
        kn = k1 if k1[0] > k2[0] else k2  # knee always forward
        f.limb([h2, kn, a2, (a2[0] + FOOT, 4)], col)
    f.limb([hip, sh], NEAR, 40)
    hand = (sh[0] + ARM - 4, sh[1] - 6)
    f.limb([sh, pol(sh, UARM, -3), hand], NEAR, 18)
    f.head(pol(sh, 50, 90 - lean * .7))
    if name == "go": f.arrow((560, hip[1] + 40), (560, hip[1] - 30))
    if name == "back": f.arrow((560, hip[1] - 20), (560, hip[1] + 50))
    ph = {"rest": "", "go": "SIT BACK", "hold": "TOUCH", "back": "STAND"}[name]
    f.text("Chair squat", "Sit back until you just touch the chair, then stand. Push through your heels", ph, INK, f"Rep {rep + 1} · knees track over toes")
    return f.out(), L * 2


def band_row(t):
    name, k, left, rep, L = cyc(t, [("rest", .5), ("go", 1.0), ("hold", 1.0), ("back", 1.4)])
    view(0.72, 520); f = Frame(); floorline(f)
    anchor = (760, 300)
    box(f, 770, 0, 800, 520)  # post / door edge
    ank = (360, 12); hip = (372, 12 + THIGH + SHIN - 8); sh = (378, hip[1] + TORSO)
    for col, dx in ((FAR, -8), (NEAR, 0)):
        a2 = (ank[0] + dx, ank[1]); h2 = (hip[0] + dx, hip[1])
        k1, k2 = ik(h2, a2, THIGH, SHIN, 1), ik(h2, a2, THIGH, SHIN, -1)
        kn = k1 if k1[0] > k2[0] else k2
        f.limb([h2, kn, a2, (a2[0] + FOOT, 4)], col)
    f.limb([hip, sh], NEAR, 40)
    reach = (sh[0] + ARM - 6, sh[1] - 26)
    pulled = (sh[0] + 26, sh[1] - 70)
    hand = (lerp(reach[0], pulled[0], k), lerp(reach[1], pulled[1], k))
    e1, e2 = ik(sh, hand, UARM, FARM, 1), ik(sh, hand, UARM, FARM, -1)
    el = e1 if e1[0] < e2[0] else e2  # elbow goes back
    f.d.line([rd.P(*hand), rd.P(*anchor)], fill=rd.ARROW, width=5 * SS)
    f.limb([sh, el, hand], NEAR, 18)
    f.head(pol(sh, 50, 88))
    if name == "go": f.arrow((sh[0] + 140, sh[1] + 50), (sh[0] + 70, sh[1] + 50))
    if name == "back": f.arrow((sh[0] + 70, sh[1] + 50), (sh[0] + 140, sh[1] + 50))
    ph = {"rest": "", "go": "PULL", "hold": f"SQUEEZE", "back": "SLOW BACK"}[name]
    f.text("Band row", "Pull elbows back by your sides, squeeze the shoulder blades together", ph, HOLD if name == "hold" else INK, f"Rep {rep + 1} · band anchored at chest height")
    return f.out(), L * 2


def counter_pushup(t):
    name, k, left, rep, L = cyc(t, [("rest", .5), ("go", 1.4), ("hold", .4), ("back", 1.2)])
    view(0.72, 470); f = Frame(); floorline(f)
    box(f, 600, 0, 780, 220)  # kitchen counter
    feet = (305, 14); hand = (608, 230)
    body = THIGH + SHIN + TORSO
    want = lerp(ARM - 4, 70, k)
    # find the body angle that puts the shoulders `want` away from the hands
    best = None
    for i in range(0, 800):
        a = math.radians(5 + i * 0.1)
        shp = (feet[0] + body * math.cos(a), feet[1] + body * math.sin(a))
        if shp[0] > hand[0] - 25 or shp[1] < hand[1] + 10: continue  # shoulders stay behind and above the hands
        dd = abs(math.hypot(hand[0] - shp[0], hand[1] - shp[1]) - want)
        if best is None or dd < best[0]: best = (dd, a, shp)
    _, a, sh = best
    hip = (feet[0] + (THIGH + SHIN) * math.cos(a), feet[1] + (THIGH + SHIN) * math.sin(a))
    knee = (feet[0] + SHIN * math.cos(a), feet[1] + SHIN * math.sin(a))
    f.limb([(feet[0] - 8, feet[1]), (knee[0] - 8, knee[1]), (hip[0] - 8, hip[1])], FAR)
    f.limb([(feet[0] - 18, 6), feet, knee, hip], NEAR)
    f.limb([hip, sh], NEAR, 40)
    e1, e2 = ik(sh, hand, UARM, FARM, 1), ik(sh, hand, UARM, FARM, -1)
    el = e1 if e1[0] < e2[0] else e2  # elbows bend back toward the feet
    f.limb([sh, el, hand], NEAR, 18)
    f.head(pol(sh, 50, math.degrees(a)))
    if name == "go": f.arrow((sh[0] - 10, sh[1] + 70), (sh[0] + 30, sh[1] + 30))
    if name == "back": f.arrow((sh[0] + 20, sh[1] + 40), (sh[0] - 20, sh[1] + 80))
    ph = {"rest": "", "go": "LOWER", "hold": "", "back": "PUSH"}[name]
    f.text("Counter push-up", "Hands on the counter edge, body straight from head to heels", ph, INK, f"Rep {rep + 1} · use a lower surface to make it harder")
    return f.out(), L * 2


JOBS = {"chair-squat": chair_squat, "band-row": band_row, "counter-pushup": counter_pushup}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    only = [a for a in sys.argv[2:] if a != "stills"]
    for n, fn in JOBS.items():
        if only and n not in only: continue
        if "stills" in sys.argv:
            _, dur = fn(0)
            for j, tt in enumerate([0.1, 2.3]): fn(tt)[0].save(f"{out}/{n}-{j}.png")
        else:
            rd.render(fn, f"{out}/{n}.mp4")
