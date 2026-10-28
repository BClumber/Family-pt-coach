"""Demo clips for the lumbar pinched-nerve preset. Uses the helpers in render-demos.py.
Usage: python3 render_lumbar.py OUT_DIR [stills]"""
import math, os, sys, importlib.util
spec = importlib.util.spec_from_file_location("rd", os.path.join(os.path.dirname(__file__), "render-demos.py"))
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
from math import ceil
Frame, view, ik, pol, lerp, ease, timeline, render = rd.Frame, rd.view, rd.ik, rd.pol, rd.lerp, rd.ease, rd.timeline, rd.render
NEAR, FAR, HOLD, INK = rd.NEAR, rd.FAR, rd.HOLD, rd.INK
THIGH, SHIN, FOOT, TORSO, UARM, FARM = rd.THIGH, rd.SHIN, rd.FOOT, rd.TORSO, rd.UARM, rd.FARM
ARM = UARM + FARM


def ik_up(a, c, l1, l2):
    e1, e2 = ik(a, c, l1, l2, 1), ik(a, c, l1, l2, -1)
    return e1 if e1[1] >= e2[1] else e2


def cyc(t, segs):
    """segs of (kind, seconds) where kind is rest/go/hold/back; returns kind, k (0..1 pose), seconds left, rep index."""
    L = sum(d for _, d in segs); rep = int(t // L)
    name, u, left = timeline(segs, t % L)
    k = {"rest": 0, "go": ease(u), "hold": 1, "back": 1 - ease(u)}[name]
    return name, k, left, rep, L


def floor(f, x0=120, x1=840): f.mat(x0, x1)


# 1 ---------------------------------------------------------------
def prone_press_up(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.4), ("hold", 2.0), ("back", 1.4), ("rest", .4)])
    view(1.25, 430); f = Frame(); floor(f, 150, 760)
    hip = (380, 22)
    # legs straight back, toes down
    for col, dy in ((FAR, 2), (NEAR, 0)):
        kn = (hip[0] - THIGH, 18 + dy); an = (kn[0] - SHIN, 15 + dy)
        f.limb([hip, kn, an, (an[0] - 14, 4)], col)
    ang = lerp(4, 34, k); sh = pol(hip, TORSO, ang)
    hand = (hip[0] + 126, 10)
    for col, dx in ((FAR, 6), (NEAR, 0)):
        s2 = (sh[0] + dx, sh[1]); h2 = (hand[0] + dx, hand[1])
        el = ik_up(s2, h2, UARM, FARM)
        if col == FAR: f.limb([s2, el, h2], col, 18)
    f.limb([hip, sh], NEAR, 40)
    el = ik_up(sh, hand, UARM, FARM); f.limb([sh, el, hand], NEAR, 18)
    f.head(pol(sh, 50, ang + 8))
    if name == "go": f.arrow((sh[0] + 40, sh[1] + 10), (sh[0] + 40, sh[1] + 70))
    if name == "back": f.arrow((sh[0] + 40, sh[1] + 60), (sh[0] + 40, sh[1] + 0))
    ph = {"rest": "", "go": "PRESS UP", "hold": f"HOLD {ceil(left)}", "back": "LOWER"}[name]
    f.text("Prone press-up", "Hips stay down, let the low back sag, arms do the work", ph, HOLD if name == "hold" else INK, f"Rep {rep + 1} · stop if leg pain spreads")
    return f.out(), L * 2


# 2 ---------------------------------------------------------------
def pelvic_tilt(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.0), ("hold", 5.0), ("back", 1.0), ("rest", .4)])
    view(1.35, 420); f = Frame(); floor(f, 170, 700)
    sh = (290, 22); hip = (sh[0] + TORSO, 22); mid = (sh[0] + TORSO * .62, lerp(40, 22, k))
    ank = (hip[0] + 128, 17)
    for col, dx in ((FAR, 10), (NEAR, 0)):
        h2 = (hip[0] + dx, hip[1]); a2 = (ank[0] + dx, ank[1])
        f.limb([h2, ik(h2, a2, THIGH, SHIN, 1), a2, (a2[0] + FOOT, 9)], col)
    f.limb([sh, mid, hip], NEAR, 40)
    f.limb([sh, (sh[0] + UARM, 12), (sh[0] + ARM, 10)], NEAR, 18)
    f.head((sh[0] - 52, 30))
    if name in ("go", "hold"): f.arrow((mid[0], mid[1] + 95), (mid[0], mid[1] + 35))
    ph = {"rest": "", "go": "FLATTEN", "hold": f"HOLD {ceil(left)}", "back": "RELAX"}[name]
    f.text("Pelvic tilt", "Tighten your belly and press the low back flat into the floor", ph, HOLD if name == "hold" else INK, f"Rep {rep + 1}")
    return f.out(), L * 2


# 3 ---------------------------------------------------------------
def nerve_glide(t):
    name, k, left, rep, L = cyc(t, [("rest", .5), ("go", 1.6), ("hold", .4), ("back", 1.6)])
    view(0.8, 450); f = Frame()
    f.d.line([0, (rd.FLOOR_Y + 2) * rd.SS, rd.W * rd.SS, (rd.FLOOR_Y + 2) * rd.SS], fill=rd.FLOOR, width=3 * rd.SS)
    seat_y = 170
    # chair
    for a, b in (((330, seat_y - 14), (500, seat_y - 14)), ((340, seat_y - 14), (340, 0)), ((490, seat_y - 14), (490, 0)), ((335, seat_y - 14), (320, 380))):
        f.limb([a, b], rd.MAT, 14)
    hip = (380, seat_y + 6)
    sh = pol(hip, TORSO, 86)
    kn = (hip[0] + THIGH, seat_y + 4)
    for col, dx in ((FAR, -8), (NEAR, 0)):
        k2 = (kn[0] + dx, kn[1])
        if col == FAR:
            an = (k2[0] + 6, k2[1] - SHIN); f.limb([(hip[0] + dx, hip[1]), k2, an, (an[0] + FOOT, an[1] - 4)], col)
        else:
            sang = lerp(-86, -8, k); an = pol(k2, SHIN, sang)
            toe = pol(an, FOOT, sang + lerp(92, 100, k))
            f.limb([hip, k2, an, toe], col)
    f.limb([hip, sh], NEAR, 40)
    f.limb([sh, (sh[0] + 30, sh[1] - UARM + 6), (hip[0] + 60, seat_y + 10)], NEAR, 18)
    f.head(pol(sh, 50, lerp(58, 108, k)))
    if name == "go": f.arrow((kn[0] + 50, kn[1] - 120), (kn[0] + 110, kn[1] - 50))
    if name == "back": f.arrow((kn[0] + 110, kn[1] - 30), (kn[0] + 50, kn[1] - 110))
    ph = {"rest": "", "go": "STRAIGHTEN", "hold": "", "back": "BEND"}[name]
    f.text("Sciatic nerve glide", "Knee straightens as you look up; bends as you tuck your chin", ph, INK, f"Rep {rep + 1} · sore leg")
    return f.out(), L * 3


# 4 ---------------------------------------------------------------
def dead_bug(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.6), ("hold", .6), ("back", 1.4)])
    view(1.25, 420); f = Frame(); floor(f, 160, 720)
    sh = (290, 22); hip = (sh[0] + TORSO, 22)
    near_moves = rep % 2 == 0  # alternate sides each rep
    def leg(col, kk):
        a = lerp(90, 18, kk); knee = pol(hip, THIGH, a)
        sa = lerp(0, 18, kk); an = pol(knee, SHIN, sa)
        f.limb([hip, knee, an, pol(an, FOOT * .8, sa + 80)], col)
    def arm(col, kk):
        a = lerp(90, 168, kk); f.limb([sh, pol(sh, UARM, a), pol(sh, ARM, a)], col, 18)
    arm(FAR, 0 if near_moves else k)
    leg(FAR, k if near_moves else 0)
    f.limb([sh, hip], NEAR, 40)
    leg(NEAR, 0 if near_moves else k)
    arm(NEAR, k if near_moves else 0)
    f.head((sh[0] - 52, 30))
    ph = {"rest": "", "go": "REACH", "hold": "", "back": "RETURN"}[name]
    f.text("Dead bug", "Low back stays pressed down. Opposite arm and leg, slow", ph, INK, f"Rep {rep // 2 + 1} · {'right' if near_moves else 'left'} arm / {'left' if near_moves else 'right'} leg")
    return f.out(), L * 2


# 5 ---------------------------------------------------------------
def quad_base():
    knee = (330, 12); hip = (330, 12 + THIGH); sh = (330 + 146, 12 + ARM - 6); hand = (sh[0], 12)
    return knee, hip, sh, hand


def bird_dog(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.4), ("hold", 5.0), ("back", 1.2)])
    view(1.15, 430); f = Frame(); floor(f, 150, 740)
    knee, hip, sh, hand = quad_base()
    near_moves = rep % 2 == 0
    def arm(col, kk, dx):
        s = (sh[0] + dx, sh[1]); a = lerp(-90, 2, kk); f.limb([s, pol(s, UARM, a), pol(s, ARM, a)], col, 18)
    def leg(col, kk, dx):
        h = (hip[0] + dx, hip[1])
        if kk < 1e-3:
            kn = (knee[0] + dx, knee[1]); f.limb([h, kn, (kn[0] - SHIN, 10), (kn[0] - SHIN - 10, 26)], col)
        else:
            a = lerp(-90, -178, kk); kn = pol(h, THIGH, a); sa = lerp(180, 182, kk) if kk > .5 else lerp(180, -178, kk)
            an = pol(kn, SHIN, 180 + lerp(0, -2, kk)) if kk > .3 else (kn[0] - SHIN, lerp(10, kn[1], kk / .3))
            f.limb([h, kn, an, (an[0] - 8, an[1] - 16)], col)
    arm(FAR, 0 if near_moves else k, 6); leg(FAR, k if near_moves else 0, -6)
    f.limb([hip, sh], NEAR, 40)
    leg(NEAR, 0 if near_moves else k, 0); arm(NEAR, k if near_moves else 0, 0)
    f.head(pol(sh, 50, 8))
    ph = {"rest": "", "go": "REACH", "hold": f"HOLD {ceil(left)}", "back": "RETURN"}[name]
    f.text("Bird dog", "Back flat like a table. Reach long, don't lift high", ph, HOLD if name == "hold" else INK, f"Rep {rep // 2 + 1} · {'right' if near_moves else 'left'} arm / {'left' if near_moves else 'right'} leg")
    return f.out(), L * 2


# 6 ---------------------------------------------------------------
def side_plank_knees(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.2), ("hold", 4.0), ("back", 1.2)])
    view(1.3, 470); f = Frame(); floor(f, 200, 760)
    el = (300, 10); sh = (300, 10 + UARM + 6); knee = (300 + TORSO + THIGH, 16)
    line_hip = (sh[0] + TORSO, lerp(sh[1], knee[1], TORSO / (TORSO + THIGH)))
    hip = (line_hip[0], lerp(24, line_hip[1], k))
    f.limb([(el[0] + 70, 8), el, sh], FAR, 18)  # forearm on the floor
    f.limb([hip, knee, (knee[0] - 40, 34)], FAR)  # bottom leg, shin bent back
    f.limb([sh, hip], NEAR, 46)
    f.limb([(hip[0] + 4, hip[1] + 14), (knee[0] + 2, knee[1] + 22), (knee[0] - 34, 58)], NEAR)
    f.limb([(sh[0] + 14, sh[1] + 12), (sh[0] + 70, sh[1] + 6), (hip[0] - 10, hip[1] + 26)], NEAR, 18)
    f.head(pol(sh, 54, 172))
    if name == "go": f.arrow((hip[0], hip[1] + 40), (hip[0], hip[1] + 100))
    ph = {"rest": "", "go": "LIFT HIPS", "hold": f"HOLD {ceil(left)}", "back": "LOWER"}[name]
    f.text("Side plank (from knees)", "Elbow under shoulder. Straight line from head to knees", ph, HOLD if name == "hold" else INK, "Hold 15–20 s each side · view from the front")
    return f.out(), L * 2


# 7 ---------------------------------------------------------------
def cat_cow(t):
    L = 5.6; tt = t % L; rep = int(t // L)
    name, u, left = timeline([("cat", 2.2), ("p1", .5), ("cow", 2.2), ("p2", .7)], tt)
    s = {"cat": ease(u), "p1": 1, "cow": 1 - 2 * ease(u), "p2": -1}[name]  # +1 rounded, -1 arched
    view(1.15, 430); f = Frame(); floor(f, 150, 740)
    knee, hip, sh, hand = quad_base()
    mid = ((hip[0] + sh[0]) / 2, (hip[1] + sh[1]) / 2 + 30 * s)
    f.limb([(sh[0] + 6, sh[1]), (hand[0] + 6, 12)], FAR, 18)
    f.limb([(hip[0] - 6, hip[1]), (knee[0] - 6, knee[1]), (knee[0] - 6 - SHIN, 10)], FAR)
    f.limb([hip, mid, sh], NEAR, 40)
    f.limb([hip, knee, (knee[0] - SHIN, 10), (knee[0] - SHIN - 10, 26)], NEAR)
    f.limb([sh, hand], NEAR, 18)
    f.head(pol(sh, 50, lerp(-48, 40, (1 - s) / 2)))
    if name == "cat": f.arrow((mid[0], mid[1] + 40), (mid[0], mid[1] + 90))
    if name == "cow": f.arrow((mid[0], mid[1] + 90), (mid[0], mid[1] + 40))
    ph = {"cat": "ROUND (CAT)", "p1": "", "cow": "ARCH (COW)", "p2": ""}[name]
    f.text("Cat-cow", "Slow and smooth, move one segment of the spine at a time", ph, INK, f"Rep {rep + 1}")
    return f.out(), L * 2


# 8 ---------------------------------------------------------------
def childs_pose(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.8), ("hold", 4.0), ("back", 1.6)])
    view(1.15, 450); f = Frame(); floor(f, 170, 760)
    knee = (420, 12); ank = (knee[0] - SHIN, 12); hand = (660, 10)
    hip = (lerp(knee[0], 340, k), lerp(12 + THIGH, 56, k))
    ang = lerp(8, -7, k); sh = pol(hip, TORSO, ang)
    f.limb([(sh[0] + 6, sh[1]), ik((sh[0] + 6, sh[1]), (hand[0] + 6, 12), UARM, FARM, 1), (hand[0] + 6, 12)], FAR, 18)
    f.limb([hip, knee, ank, (ank[0] - 14, 8)], FAR)
    f.limb([hip, sh], NEAR, 40)
    f.limb([sh, ik(sh, hand, UARM, FARM, 1), hand], NEAR, 18)
    f.head(pol(sh, 46, ang - 18))
    if name == "go": f.arrow((hip[0] + 30, hip[1] + 70), (hip[0] - 40, hip[1] + 70))
    if name == "back": f.arrow((hip[0] - 30, hip[1] + 70), (hip[0] + 40, hip[1] + 70))
    ph = {"rest": "", "go": "SIT BACK", "hold": "HOLD 30 s", "back": "COME UP"}[name]
    f.text("Child's pose", "Sit back toward your heels, arms long. Skip if leg pain increases", ph, HOLD if name == "hold" else INK, "Hold 30 s")
    return f.out(), L


# 9 ---------------------------------------------------------------
def figure_four(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.8), ("hold", 4.0), ("back", 1.6)])
    view(1.3, 420); f = Frame(); floor(f, 160, 720)
    sh = (290, 22); hip = (sh[0] + TORSO, 22)
    a = lerp(55, 95, k); fk = pol(hip, THIGH, a); fa = pol(fk, SHIN, lerp(-62, -8, k))
    f.limb([hip, fk, fa, pol(fa, FOOT, lerp(28, 82, k))], FAR)  # support leg, pulled in
    f.limb([sh, hip], NEAR, 40)
    na = (fk[0] + 12, fk[1] + 10)
    nk = ik(hip, na, THIGH, SHIN, bend=-1)
    f.limb([hip, nk, na, (na[0] + 22, na[1] + 18)], NEAR)  # crossed leg, ankle on knee
    grip = ((hip[0] + fk[0]) / 2 + 8, (hip[1] + fk[1]) / 2 + 14)
    f.limb([sh, ik(sh, grip, UARM, FARM, 1), grip], NEAR, 18)
    f.head((sh[0] - 52, 30))
    if name == "go": f.arrow((fk[0] + 60, fk[1] + 10), (fk[0] + 10, fk[1] + 40))
    ph = {"rest": "", "go": "PULL IN", "hold": "HOLD 30 s", "back": "RELEASE"}[name]
    f.text("Figure-4 stretch", "Ankle on opposite knee, pull that thigh toward you. Stretch in the buttock", ph, HOLD if name == "hold" else INK, "Hold 30 s each side")
    return f.out(), L


# 10 --------------------------------------------------------------
def hip_flexor(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.6), ("hold", 4.0), ("back", 1.4)])
    view(0.88, 440); f = Frame()
    f.d.line([0, (rd.FLOOR_Y + 2) * rd.SS, rd.W * rd.SS, (rd.FLOOR_Y + 2) * rd.SS], fill=rd.FLOOR, width=3 * rd.SS)
    bk = (350, 14); bf = (bk[0] - SHIN, 12); ff = (505, 8)
    hip = (lerp(362, 398, k), lerp(12 + THIGH - 2, 12 + THIGH - 14, k))
    fk = ik(hip, ff, THIGH, SHIN, bend=1)
    f.limb([hip, fk, ff, (ff[0] + FOOT, 4)], FAR)
    f.limb([hip, bk, bf, (bf[0] - 12, 24)], NEAR)
    sh = pol(hip, TORSO, lerp(90, 94, k))
    f.limb([hip, sh], NEAR, 40)
    f.limb([sh, (sh[0] + 26, sh[1] - UARM + 8), (hip[0] + 14, hip[1] + 20)], NEAR, 18)
    f.head(pol(sh, 50, 88))
    if name == "go": f.arrow((hip[0] - 20, hip[1] - 40), (hip[0] + 50, hip[1] - 40))
    ph = {"rest": "", "go": "TUCK & SHIFT", "hold": "HOLD 30 s", "back": "BACK"}[name]
    f.text("Hip flexor stretch", "Half-kneeling. Tuck your pelvis under, then shift forward", ph, HOLD if name == "hold" else INK, "Hold 30 s each side · pad under the knee")
    return f.out(), L


# 11 --------------------------------------------------------------
def hamstring_strap(t):
    name, k, left, rep, L = cyc(t, [("rest", .6), ("go", 1.8), ("hold", 4.0), ("back", 1.6)])
    view(1.25, 420); f = Frame(); floor(f, 160, 760)
    sh = (290, 22); hip = (sh[0] + TORSO, 22)
    f.limb([(hip[0] + 8, 22), (hip[0] + 8 + THIGH, 18), (hip[0] + 8 + THIGH + SHIN, 16), (hip[0] + 8 + THIGH + SHIN + 8, 46)], FAR)
    f.limb([sh, hip], NEAR, 40)
    a = lerp(45, 78, k); kn = pol(hip, THIGH, a); an = pol(kn, SHIN, a); toe = pol(an, FOOT, a - 90 + 180)
    f.limb([hip, kn, an, pol(an, FOOT, a + 90)], NEAR)
    hand = (sh[0] + 60, 150)
    f.d.line([rd.P(*hand), rd.P(*pol(an, 10, a + 90))], fill=rd.ARROW, width=4 * rd.SS)
    f.d.line([rd.P(*(hand[0] + 6, hand[1] - 4)), rd.P(*pol(an, 10, a - 90))], fill=rd.ARROW, width=4 * rd.SS)
    f.limb([sh, ik(sh, hand, UARM, FARM, -1), hand], NEAR, 18)
    f.head((sh[0] - 52, 30))
    ph = {"rest": "", "go": "RAISE LEG", "hold": "HOLD 30 s", "back": "LOWER"}[name]
    f.text("Hamstring stretch (strap)", "Gentle pull. If it lights up the nerve, do the nerve glide instead", ph, HOLD if name == "hold" else INK, "Hold 30 s each side · strap or towel")
    return f.out(), L


JOBS = {"prone-press-up": prone_press_up, "pelvic-tilt": pelvic_tilt, "nerve-glide": nerve_glide, "dead-bug": dead_bug,
        "bird-dog": bird_dog, "side-plank-knees": side_plank_knees, "cat-cow": cat_cow, "childs-pose": childs_pose,
        "figure-four": figure_four, "hip-flexor-stretch": hip_flexor, "hamstring-strap": hamstring_strap}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    only = [a for a in sys.argv[2:] if a != "stills"]
    for name, fn in JOBS.items():
        if only and name not in only: continue
        if "stills" in sys.argv:
            _, dur = fn(0)
            for j, tt in enumerate([0.1, dur * 0.3]): fn(tt)[0].save(f"{out}/{name}-{j}.png")
        else:
            render(fn, f"{out}/{name}.mp4")
