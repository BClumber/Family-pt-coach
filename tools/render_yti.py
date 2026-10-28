"""Demo clips for prone Y, T and I raises (rotator cuff / lower trap), drawn from above.
Usage: python3 render_yti.py OUT_DIR [stills]"""
import math, os, sys, importlib.util
spec = importlib.util.spec_from_file_location("rd", os.path.join(os.path.dirname(__file__), "render-demos.py"))
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
SS = rd.SS
SHADOW = (196, 210, 216); MATC = rd.MAT


def seg(d, a, b, col, w):
    d.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=col, width=int(w * SS))
    for p in (a, b):
        r = w * SS / 2; d.ellipse([p[0] * SS - r, p[1] * SS - r, p[0] * SS + r, p[1] * SS + r], fill=col)


def dot(d, c, r, col):
    d.ellipse([(c[0] - r) * SS, (c[1] - r) * SS, (c[0] + r) * SS, (c[1] + r) * SS], fill=col)


def make(letter, angle, title, cue):
    """angle = arm angle above horizontal, in degrees (screen up is positive)."""
    def fn(t):
        name, k, left, rep, L = None, 0, 0, 0, 0
        segs = [("rest", .7), ("go", 1.0), ("hold", 2.0), ("back", 1.0), ("rest", .3)]
        L = sum(x for _, x in segs); rep = int(t // L)
        name, u, left = rd.timeline(segs, t % L)
        k = {"rest": 0, "go": rd.ease(u), "hold": 1, "back": 1 - rd.ease(u)}[name]
        f = rd.Frame(); d = f.d
        # mat seen from above
        d.rounded_rectangle([300 * SS, 120 * SS, 660 * SS, 468 * SS], radius=18 * SS, fill=MATC)
        cx, shy = 480, 270
        # legs, torso, head (face down, forehead on a small towel)
        for x in (462, 498): seg(d, (x, 430), (x + (x - 480) * .15, 462), rd.FAR, 30)
        seg(d, (cx, shy), (cx, 420), rd.NEAR, 74)
        d.rounded_rectangle([(cx - 34) * SS, (shy - 92) * SS, (cx + 34) * SS, (shy - 58) * SS], radius=8 * SS, fill=(230, 236, 239))
        dot(d, (cx, shy - 44), 30, rd.NEAR)
        L_ARM = 150
        lift = 9 * k
        for side in (-1, 1):
            sh = (cx + side * 40, shy + 4)
            a = math.radians(angle)
            hand = (sh[0] + side * L_ARM * math.cos(a), sh[1] - L_ARM * math.sin(a))
            seg(d, sh, hand, SHADOW, 22)  # arm resting / shadow on the mat
            off = (side * -lift * .2, -lift)
            s2 = (sh[0] + off[0], sh[1] + off[1]); h2 = (hand[0] + off[0], hand[1] + off[1])
            seg(d, s2, h2, rd.NEAR if k > .02 else rd.FAR, 22 + 4 * k)
            # thumb pointing up (toward the ceiling) drawn as a small dot on the top edge of the hand
            th = (h2[0] - side * 9 * math.sin(a) * 0 + (0 if angle == 90 else 0), h2[1] - 2)
            dot(d, (h2[0] + (8 if side < 0 else -8) * (1 if angle < 80 else 0), h2[1] - (0 if angle < 80 else 10)), 7, rd.ARROW)
        # shoulder-blade squeeze arrows
        if k > .2:
            for side in (-1, 1):
                a0 = (cx + side * 62, shy + 46); a1 = (cx + side * 22, shy + 64)
                d.line([(a0[0] * SS, a0[1] * SS), (a1[0] * SS, a1[1] * SS)], fill=rd.ARROW, width=5 * SS)
                ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
                for da in (2.6, -2.6):
                    e = (a1[0] + 14 * math.cos(ang + da), a1[1] + 14 * math.sin(ang + da))
                    d.line([(a1[0] * SS, a1[1] * SS), (e[0] * SS, e[1] * SS)], fill=rd.ARROW, width=5 * SS)
        # big letter
        d.text((760 * SS, 230 * SS), letter, font=rd.ImageFont.truetype(rd.F + "DejaVuSans-Bold.ttf", 150 * SS), fill=(210, 222, 228))
        ph = {"rest": "", "go": "LIFT", "hold": f"HOLD {math.ceil(left)}", "back": "LOWER"}[name]
        f.text(title, cue, ph, rd.HOLD if name == "hold" else rd.INK, f"Rep {rep + 1} · seen from above · orange = thumbs up")
        return f.out(), L * 2
    return fn


JOBS = {
    "prone-y": make("Y", 45, "Prone Y raise", "Arms in a Y, thumbs up. Squeeze shoulder blades down and back"),
    "prone-t": make("T", 0, "Prone T raise", "Arms straight out, thumbs up. Pinch shoulder blades together"),
    "prone-i": make("I", 90, "Prone I raise", "Arms overhead by your ears, thumbs up. Lift a few inches"),
}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for name, fn in JOBS.items():
        if "stills" in sys.argv:
            _, dur = fn(0)
            for j, tt in enumerate([0.2, 2.5]): fn(tt)[0].save(f"{out}/{name}-{j}.png")
        else:
            rd.render(fn, f"{out}/{name}.mp4")
