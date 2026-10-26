"""Render looping mannequin demo clips for the Family PT Coach app."""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 960, 540, 2, 30
BG = (238, 243, 245); MAT = (214, 228, 233); FLOOR = (160, 178, 186)
NEAR = (10, 106, 134); FAR = (122, 172, 190); HEAD = (10, 106, 134)
INK = (19, 34, 42); MUTED = (86, 103, 111); ARROW = (192, 86, 47); HOLD = (44, 122, 76)
F = "/usr/share/fonts/truetype/dejavu/"
fT = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 34 * SS)
fS = ImageFont.truetype(F + "DejaVuSans.ttf", 22 * SS)
fP = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 40 * SS)
FLOOR_Y = 430  # screen y of floor

THIGH, SHIN, FOOT, TORSO, UARM, FARM = 112, 106, 34, 150, 78, 72


def ease(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def lerp(a, b, t): return a + (b - a) * t


VIEW = {"sc": 1.0, "ox": 0.0}


def P(x, y):  # world (y up from floor) -> supersampled screen
    sc, ox = VIEW["sc"], VIEW["ox"]
    return ((ox + x * sc) * SS, (FLOOR_Y - y * sc) * SS)


def view(sc, cx):  # scale about world x=cx placed at screen centre
    VIEW["sc"] = sc; VIEW["ox"] = W / 2 - cx * sc


def ik(a, c, l1, l2, bend=1):
    """two-bone IK from root a to end c; bend=+1 joint to the left of a->c direction (y-up)."""
    dx, dy = c[0] - a[0], c[1] - a[1]
    d = math.hypot(dx, dy); d = min(d, l1 + l2 - 1e-6); d = max(d, abs(l1 - l2) + 1e-6)
    base = math.atan2(dy, dx)
    ang = math.acos((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))
    t = base + bend * ang
    return (a[0] + l1 * math.cos(t), a[1] + l1 * math.sin(t))


def pol(o, l, deg):
    r = math.radians(deg); return (o[0] + l * math.cos(r), o[1] + l * math.sin(r))


class Frame:
    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), BG)
        self.d = ImageDraw.Draw(self.im)

    def limb(self, pts, col, w=22):
        w = w * VIEW["sc"]
        for a, b in zip(pts, pts[1:]):
            self.d.line([P(*a), P(*b)], fill=col, width=int(w * SS))
        for p in pts:
            x, y = P(*p); r = w * SS / 2
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def head(self, c, r=30, col=HEAD):
        x, y = P(*c); r *= SS * VIEW["sc"]
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def mat(self, x0, x1):
        x0 = P(x0, 0)[0] / SS; x1 = P(x1, 0)[0] / SS
        self.d.rounded_rectangle([x0 * SS, (FLOOR_Y) * SS, x1 * SS, (FLOOR_Y + 14) * SS], radius=6 * SS, fill=MAT)
        self.d.line([0, (FLOOR_Y + 14) * SS, W * SS, (FLOOR_Y + 14) * SS], fill=FLOOR, width=3 * SS)

    def arrow(self, a, b, col=ARROW, w=6):
        self.d.line([P(*a), P(*b)], fill=col, width=w * SS)
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); h = 22
        p1 = pol(b, h, math.degrees(ang) + 150); p2 = pol(b, h, math.degrees(ang) - 150)
        self.d.polygon([P(*b), P(*p1), P(*p2)], fill=col)

    def text(self, title, cue, phase=None, phase_col=INK, rep=None):
        self.d.text((36 * SS, 28 * SS), title, font=fT, fill=INK)
        self.d.text((36 * SS, 72 * SS), cue, font=fS, fill=MUTED)
        if phase:
            bb = self.d.textbbox((0, 0), phase, font=fP)
            self.d.text(((W - 36) * SS - (bb[2] - bb[0]), 28 * SS), phase, font=fP, fill=phase_col)
        if rep:
            self.d.text((36 * SS, (H - 56) * SS), rep, font=fS, fill=MUTED)
        self.d.text(((W - 300) * SS, (H - 56) * SS), "Demo animation · check with your PT", font=ImageFont.truetype(F + "DejaVuSans.ttf", 15 * SS), fill=MUTED)

    def out(self):
        return self.im.resize((W, H), Image.LANCZOS)


def timeline(segs, t):
    """segs: list of (name, dur). returns (name, local_t 0..1, seconds_left_in_seg)."""
    for name, dur in segs:
        if t < dur: return name, t / dur, dur - t
        t -= dur
    name, dur = segs[-1]; return name, 1.0, 0


# ---------------- exercises ----------------
def glute_bridge(t):
    rep_len = 0.7 + 1.2 + 3.0 + 1.2 + 0.5
    rep = int(t // rep_len); name, u, left = timeline([("rest", .7), ("lift", 1.2), ("hold", 3.0), ("lower", 1.2), ("rest2", .5)], t % rep_len)
    k = {"rest": 0, "lift": ease(u), "hold": 1, "lower": 1 - ease(u), "rest2": 0}[name]
    view(1.35, 420); f = Frame(); f.mat(170, 700)
    sh = (290, 22); hip_ang = lerp(0, 24, k)
    hip = pol(sh, TORSO, hip_ang)
    ank = (hip[0] if k == 0 else None, None)
    ank = (290 + TORSO + 128, 17)
    for col, dx in ((FAR, 10), (NEAR, 0)):
        h2 = (hip[0] + dx, hip[1]); a2 = (ank[0] + dx, ank[1])
        kn = ik(h2, a2, THIGH, SHIN, bend=1)
        f.limb([h2, kn, a2, (a2[0] + FOOT, 9)], col)
    f.limb([sh, hip], NEAR, 40)
    f.limb([sh, (sh[0] + UARM, 12), (sh[0] + UARM + FARM, 10)], NEAR, 18)
    f.head((sh[0] - 52, 30))
    if name == "lift": f.arrow((hip[0] + 0, hip[1] + 60), (hip[0], hip[1] + 120))
    if name == "lower": f.arrow((hip[0], hip[1] + 110), (hip[0], hip[1] + 50))
    phase = {"rest": "", "lift": "LIFT", "hold": f"HOLD {math.ceil(left)}", "lower": "LOWER", "rest2": ""}[name]
    f.text("Glute bridge", "Feet flat, squeeze glutes, lift hips to a straight line", phase, HOLD if name == "hold" else INK, f"Rep {rep + 1}")
    return f.out(), rep_len * 2


def clamshell(t):
    rep_len = .5 + 1.0 + .5 + 1.2
    rep = int(t // rep_len); name, u, left = timeline([("rest", .5), ("open", 1.0), ("pause", .5), ("close", 1.2)], t % rep_len)
    k = {"rest": 0, "open": ease(u), "pause": 1, "close": 1 - ease(u)}[name]
    view(1.35, 470); f = Frame(); f.mat(220, 720)
    hip = (520, 45); sh = (hip[0] - TORSO, 45)
    f.limb([sh, (sh[0] - 30, 16), (sh[0] - 85, 30)], FAR, 18)  # bottom arm pillowing head
    f.head((sh[0] - 62, 64))
    f.limb([(hip[0], 24), (hip[0] + 62, 14), (hip[0] + 178, 14)], FAR)  # bottom leg
    f.limb([sh, hip], NEAR, 52)
    tk = (hip[0] + 62 - 6 * k, 36 + 96 * k)
    f.limb([(hip[0], 64), tk, (hip[0] + 178, 36)], NEAR)  # top leg, feet stay together
    f.limb([(sh[0] + 20, 50), (sh[0] + 80, 22), (sh[0] + 140, 14)], NEAR, 18)  # top arm in front
    if name == "open": f.arrow((tk[0] + 30, tk[1] - 10), (tk[0] + 30, tk[1] + 50))
    if name == "close": f.arrow((tk[0] + 30, tk[1] + 40), (tk[0] + 30, tk[1] - 20))
    phase = {"rest": "", "open": "OPEN", "pause": "", "close": "CLOSE"}[name]
    f.text("Clamshell", "Side-lying, feet together — lift top knee, keep pelvis still", phase, INK, f"Rep {rep + 1}  ·  view from the front")
    return f.out(), rep_len * 3


def heel_slide(t):
    rep_len = .5 + 1.6 + .5 + 1.6
    rep = int(t // rep_len); name, u, left = timeline([("rest", .5), ("in", 1.6), ("pause", .5), ("out", 1.6)], t % rep_len)
    k = {"rest": 0, "in": ease(u), "pause": 1, "out": 1 - ease(u)}[name]
    view(1.3, 450); f = Frame(); f.mat(200, 740)
    sh = (300, 22); hip = (sh[0] + TORSO, 22)
    # far leg straight
    f.limb([(hip[0] + 8, hip[1]), (hip[0] + 8 + THIGH, 18), (hip[0] + 8 + THIGH + SHIN, 16), (hip[0] + 8 + THIGH + SHIN + 8, 46)], FAR)
    f.limb([sh, hip], NEAR, 40)
    ax = lerp(hip[0] + THIGH + SHIN - 4, hip[0] + 92, k); ank = (ax, 16)
    kn = ik(hip, ank, THIGH, SHIN, bend=1)
    toe = (ank[0] + 8, 46) if k < .5 else (ank[0] + FOOT * lerp(.3, 1, (k - .5) * 2), lerp(46, 10, (k - .5) * 2))
    f.limb([hip, kn, ank, toe], NEAR)
    f.limb([sh, (sh[0] + UARM, 12), (sh[0] + UARM + FARM, 10)], NEAR, 18)
    f.head((sh[0] - 52, 30))
    if name == "in": f.arrow((ank[0] + 70, 70), (ank[0] + 10, 70))
    if name == "out": f.arrow((ank[0] - 10, 70), (ank[0] + 50, 70))
    phase = {"rest": "", "in": "SLIDE IN", "pause": "", "out": "SLIDE OUT"}[name]
    f.text("Heel slide", "Lying on your back — slide heel toward you, then back out", phase, INK, f"Rep {rep + 1}")
    return f.out(), rep_len * 2


def calf_stretch(t):
    name, u, left = timeline([("rest", .8), ("lean", 1.6), ("hold", 4.0), ("back", 1.6), ("rest2", .6)], t)
    k = {"rest": 0, "lean": ease(u), "hold": 1, "back": 1 - ease(u), "rest2": 0}[name]
    view(0.78, 520); f = Frame()
    f.d.line([0, (FLOOR_Y + 2) * SS, W * SS, (FLOOR_Y + 2) * SS], fill=FLOOR, width=3 * SS)
    wall_x = 700
    wx = P(wall_x, 0)[0]; wt = P(0, 470)[1]
    f.d.rectangle([wx, wt, wx + 26 * SS, (FLOOR_Y + 2) * SS], fill=MAT)
    back_ank = (330, 10); front_ank = (520, 10)
    phi = lerp(10, 27, k)  # back leg lean from vertical, degrees
    leg = THIGH + SHIN
    hip = (back_ank[0] + leg * math.sin(math.radians(phi)), back_ank[1] + leg * math.cos(math.radians(phi)))
    sh = (hip[0] + TORSO * math.sin(math.radians(phi + 2)), hip[1] + TORSO * math.cos(math.radians(phi + 2)))
    hand = (wall_x - 6, sh[1] + 4)
    # front leg (far color, bent)
    fk = ik(hip, front_ank, THIGH, SHIN, bend=-1)
    f.limb([hip, fk, front_ank, (front_ank[0] + FOOT, 4)], FAR)
    f.limb([back_ank, hip], NEAR)
    f.limb([(back_ank[0] - 6, 4), (back_ank[0] + FOOT - 4, 4)], NEAR)
    f.limb([hip, sh], NEAR, 40)
    el = ik(sh, hand, UARM, FARM, bend=-1)
    f.limb([sh, el, hand], NEAR, 18)
    f.head(pol(sh, 50, 90 - phi * .8))
    if name == "lean": f.arrow((hip[0] - 30, hip[1] + 40), (hip[0] + 40, hip[1] + 40))
    if name == "back": f.arrow((hip[0] + 40, hip[1] + 40), (hip[0] - 30, hip[1] + 40))
    phase = {"rest": "", "lean": "LEAN IN", "hold": "HOLD 30 s", "back": "EASE BACK", "rest2": ""}[name]
    f.text("Calf stretch", "Back knee straight, back heel stays down", phase, HOLD if name == "hold" else INK, "Hold the stretch for the time your PT set")
    return f.out(), 8.6


def render(fn, path):
    _, dur = fn(0)
    n = int(dur * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    for i in range(n):
        im, _ = fn(i / FPS); proc.stdin.write(im.tobytes())
    proc.stdin.close(); proc.wait()


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    jobs = {"glute-bridge": glute_bridge, "clamshell": clamshell, "heel-slide": heel_slide, "calf-stretch": calf_stretch}
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        for k, fn in jobs.items():
            _, dur = fn(0)
            for j, t in enumerate([0.2, dur * 0.25]):
                fn(t)[0].save(f"{out}/{k}-{j}.png")
    else:
        for k, fn in jobs.items():
            render(fn, f"{out}/{k}.mp4")
