"""Vidéo TikTok pixel art : défi d'apnée, « tiens jusqu'au dauphin ».

Le spectateur retient sa respiration pendant que la vidéo plonge dans l'océan :
un palier (et une créature) toutes les 5 secondes, jusqu'au dauphin à 45 s.
Durée courte et tenable : on veut qu'il arrive au bout et en soit fier.
Pas de musique (ajoutée au montage), seulement de légers bruitages.

    python3 make_video.py                 # produit apnee_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import random
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 90
TOP = 48

# voix d'Hugo (audio/intro.mp3) : « Grande inspiration… » puis « trois, deux, un ! »
COUNT = [4.91, 5.68, 6.57]   # moments où il dit trois, deux, un
INTRO = 7.2          # inspiration + 3, 2, 1
HOLD = 45.0          # durée de l'apnée
OUTRO = 7.5
DUR = INTRO + HOLD + OUTRO


def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def put(img, spr, cx, cy, scale=3, flip=False):
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    if flip:
        s = s.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


# ---------------------------------------------------------------- créatures
K = INK
TADPOLE = art(["...gggg.", "..ggggkg", "gggggggg", "..gggggg", "...gggg."],
              {'g': (60, 120, 60), 'k': K})
CIG = art(["wwwwwwwwwwoor", "wwwwwwwwwwoor"], {'w': WHITE, 'o': ORANGE, 'r': RED})
GOLDFISH = art(["....ooo....", "o..oooooo..", "oooooookoo.", "o..oooooooo", "....ooo...."],
               {'o': ORANGE, 'k': K})
CRAB = art(["r.......r", "rr.k.k.rr", ".rrrrrrr.", "rrrrrrrrr", "r.r.r.r.r"], {'r': RED, 'k': K})
SWIMMER = art(["...ss.....", "s.sss....s", "sbbbbbbbbs", "...ss.ss..", "..s.....s."],
              {'s': PEACH, 'b': BLUE})
TURTLE = art(["...gggg....", "..gdgdgg.hh", "ggddgddgghk", "..gggggg.hh", ".h.....h..."],
             {'g': (60, 140, 70), 'd': (30, 90, 50), 'h': (120, 170, 90), 'k': K})
OCTOPUS = art(["..pppp..", ".pppppp.", ".pkppkp.", ".pppppp.", "p.p.p.p.", "p..p.p.p"],
              {'p': PINK, 'k': K})
SEAL = art(["......ggg..", "....gggkgg.", "ggggggggggg", ".gggggggg..", "g.......g.."],
           {'g': LGREY, 'k': K})
DOLPHIN = art(["......b.......", ".....bb.......", "..bbbbbbbbb...", ".bbbbbbbbbkbb.",
               "bb.wwwwwwwbbbb", "b.....wwww....", "......b......."],
              {'b': (90, 150, 220), 'w': WHITE, 'k': K})

# (seconde d'apnée, nom du niveau, sprite, échelle)
LEVELS = [
    (5, "TÊTARD", TADPOLE, 4),
    (10, "POUMONS DE FUMEUR", CIG, 3),
    (15, "POISSON ROUGE", GOLDFISH, 4),
    (20, "CRABE", CRAB, 4),
    (25, "NAGEUR DU DIMANCHE", SWIMMER, 4),
    (30, "TORTUE DE MER", TURTLE, 4),
    (35, "PIEUVRE", OCTOPUS, 4),
    (40, "PHOQUE", SEAL, 4),
    (45, "DAUPHIN", DOLPHIN, 4),
]

# ---------------------------------------------------------------- l'océan
SURFACE = np.array([70, 170, 230])
DEEP = np.array([8, 14, 48])
_yy, _xx = np.mgrid[0:H, 0:W]
_bayer = BAYER[_yy % 4, _xx % 4]
_bg_cache = {}


def ocean(depth):
    """Fond tramé : plus on descend (depth 0..1), plus l'eau s'assombrit."""
    key = round(depth, 2)
    if key not in _bg_cache:
        v = np.clip(depth * 0.8 + _yy / H * 0.35, 0, 1)
        levels = 5
        q = np.floor(v * (levels - 1) + _bayer).clip(0, levels - 1) / (levels - 1)
        a = SURFACE[None, None, :] * (1 - q[..., None]) + DEEP[None, None, :] * q[..., None]
        _bg_cache[key] = Image.fromarray(a.astype(np.uint8), 'RGB')
    return _bg_cache[key].copy()


_r = random.Random(3)
BUBBLES = [(_r.randrange(W), _r.random() * 400, 8 + _r.random() * 14, _r.choice((1, 1, 2))) for _ in range(28)]
FISH = [(_r.random() * 300, 70 + _r.random() * 150, 10 + _r.random() * 14, _r.random() < 0.5)
        for _ in range(14)]
WEEDS = [(_r.randrange(4, W - 4), _r.randrange(20, 46)) for _ in range(14)]


def decor(img, t, depth):
    d = ImageDraw.Draw(img)
    # rayons de lumière près de la surface
    if depth < 0.6:
        alpha = int(40 * (1 - depth / 0.6))
        for k in range(4):
            x = int((k * 55 + t * 6) % (W + 60)) - 30
            col = tuple(min(255, c + alpha) for c in (60, 150, 210))
            d.polygon([(x, 0), (x + 10, 0), (x + 50, H), (x + 34, H)], fill=None, outline=col)
    # bulles qui remontent
    for x, y0, sp, r in BUBBLES:
        y = (y0 - t * sp) % 380 - 40
        xx = x + math.sin(t * 2 + y0) * 2
        d.ellipse([xx - r, y - r, xx + r, y + r], outline=(190, 230, 255))
    # petits poissons en banc
    for x0, y, sp, left in FISH:
        x = (x0 + t * sp) % (W + 40) - 20
        if left:
            x = W - x
        img.paste((150, 200, 230), (int(x), int(y), int(x) + 4, int(y) + 2))
        img.paste((150, 200, 230), (int(x) + (4 if not left else -2), int(y) - 1, int(x) + (6 if not left else 0), int(y) + 3))
    # algues au fond, qui remontent dans le champ en fin de plongée
    if depth > 0.75:
        base = H - int((depth - 0.75) / 0.25 * 26)
        img.paste((30, 40, 60), (0, base, W, H))
        for x, h in WEEDS:
            for k in range(h):
                xx = x + int(math.sin(t * 2 + k * 0.3 + x) * 2)
                img.paste((40, 120, 80), (xx, base - k, xx + 2, base - k + 1))


# ---------------------------------------------------------------- interface
def gauge(img, sec):
    """Jauge des poumons à gauche, avec un cran par niveau."""
    x0, x1, y0, y1 = 12, 22, 74, 214
    img.paste(SHADOW, (x0 - 2, y0 - 2, x1 + 2, y1 + 2))
    img.paste((20, 30, 70), (x0, y0, x1, y1))
    p = clamp(sec / HOLD)
    h = int((y1 - y0) * p)
    col = GREEN if p < 0.5 else (YELLOW if p < 0.85 else ORANGE)
    img.paste(col, (x0, y1 - h, x1, y1))
    for s, _, _, _ in LEVELS:
        y = int(y1 - (y1 - y0) * s / HOLD)
        img.paste(WHITE if sec >= s else LGREY, (x1, y, x1 + 4, y + 1))


def chrono(img, sec):
    s = int(sec)
    draw_text(img, f"{s // 60:02d}:{s % 60:02d}", CX, TOP - 2, WHITE, scale=3, shadow=SHADOW)


def safety(img):
    img.paste(SHADOW, (20, 221, 160, 246))
    draw_text(img, "ASSIS, JAMAIS DANS L'EAU", CX, 222, LGREY, maxw=150, shadow=None)
    draw_text(img, "STOP AU MOINDRE VERTIGE", CX, 234, LGREY, maxw=150, shadow=None)


def lungs(img, cx, cy, fill):
    """Deux poumons pixel qui se remplissent."""
    for side in (-1, 1):
        x = cx + side * 14
        d = ImageDraw.Draw(img)
        d.ellipse([x - 11, cy - 18, x + 11, cy + 18], fill=(80, 40, 70))
        h = int(36 * fill)
        if h:
            m = Image.new('L', (W, H), 0)
            ImageDraw.Draw(m).ellipse([x - 11, cy - 18, x + 11, cy + 18], fill=255)
            layer = Image.new('RGB', (W, H), PINK)
            band = Image.new('L', (W, H), 0)
            band.paste(255, (0, cy + 18 - h, W, cy + 19))
            img.paste(layer, (0, 0), Image.fromarray(np.minimum(np.array(m), np.array(band))))
    img.paste((230, 200, 210), (cx - 2, cy - 30, cx + 2, cy - 8))


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
for k, tc in enumerate(COUNT):
    SFX.append((tc, 'place', 20 - k * 4))
SFX.append((INTRO, 'impact', None))
SHAKES.append((INTRO, 2))
for s, _, _, _ in LEVELS[:-1]:
    SFX.append((INTRO + s, 'coin', None))
SFX.append((INTRO + HOLD, 'sparkle', None))


@scene(0.0, INTRO)
def s_intro(img, t):
    draw_text(img, "RETIENS TA", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "RESPIRATION", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE)
    draw_text(img, "JUSQU'AU DAUPHIN", CX, TOP + 44, WHITE)
    put(img, DOLPHIN, CX, TOP + 62 + math.sin(t * 3) * 2, 2)
    if t < COUNT[0]:
        lungs(img, CX, 152, clamp(t / 4.4))
        draw_text(img, "INSPIRE À FOND..." if t < 2.17 else "ET BLOQUE !", CX, 184, WHITE, scale=1)
    else:
        lungs(img, CX, 152, 1)
        k = sum(1 for tc in COUNT if t >= tc)
        p = ease_out_back((t - COUNT[k - 1]) / 0.3)
        draw_text(img, str(4 - k), CX, int(176 + (1 - p) * 6), YELLOW, scale=3, shadow=PURPLE)
    safety(img)


def creature_track(img, t, sec):
    """Chaque créature arrive à son niveau, nage au centre, puis repart."""
    for s, name, spr, sc in LEVELS:
        lt = sec - s
        if -0.1 < lt < 6.0:
            x = 200 - 110 * ease_out_back(lt / 0.8) if lt < 4.8 else 90 - (lt - 4.8) * 120
            y = 164 + math.sin(t * 2.5 + s) * 5
            put(img, spr, x, y, sc + 1)


@scene(INTRO, INTRO + HOLD)
def s_dive(img, t):
    sec = t - INTRO
    depth = sec / HOLD
    bg = ocean(depth)
    img.paste(bg)
    decor(img, t, depth)
    creature_track(img, t, sec)
    gauge(img, sec)
    chrono(img, sec)
    reached = [lv for lv in LEVELS if sec >= lv[0]]
    if reached:
        s, name, _, _ = reached[-1]
        draw_text(img, "NIVEAU", CX, TOP + 34, LGREY)
        p = ease_out_back((sec - s) / 0.35)
        draw_text(img, name, CX, int(TOP + 46 + (1 - p) * 6), YELLOW, scale=2, shadow=PURPLE, maxw=150)
    else:
        draw_text(img, "BLOQUE !", CX, TOP + 40, WHITE, scale=2, shadow=PURPLE)
    nxt = [lv for lv in LEVELS if sec < lv[0]]
    if nxt and sec > 0.5:
        draw_text(img, f"PROCHAIN : {nxt[0][1]}", 96, 196, WHITE, maxw=136)
    safety(img)


@scene(INTRO + HOLD, DUR)
def s_win(img, t):
    lt = t - INTRO - HOLD
    img.paste(ocean(1.0))
    decor(img, t, 1.0)
    put(img, DOLPHIN, CX, 152 + math.sin(t * 3) * 4, 4)
    draw_text(img, "RESPIRE !", CX, TOP - 2, WHITE, scale=3, shadow=PURPLE)
    if lt > 0.6:
        p = ease_out_back((lt - 0.6) / 0.4)
        draw_text(img, "45 SECONDES", CX, int(TOP + 34 + (1 - p) * 6), YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "NIVEAU DAUPHIN", CX, TOP + 56, WHITE, scale=2, maxw=176, wave_t=t, rainbow=True,
                  shadow=PURPLE)
        px = img.load()
        for i in range(40):
            a = i * 0.157 + lt * 0.4
            dd = 40 + lt * 30 + (i % 4) * 6
            x, y = CX + math.cos(a) * dd, 130 + math.sin(a) * dd * 0.7
            if 0 <= x < W and 0 <= y < H and (int(lt * 10) + i) % 3:
                px[int(x), int(y)] = RAINBOW[i % 6]
    if lt > FIN_START + 4.2:
        img.paste(SHADOW, (14, 182, 156, 216))
        draw_text(img, "T'AS TENU JUSQU'OÙ ?", CX, 186, WHITE, maxw=150)
        draw_text(img, "DIS-LE EN COMMENTAIRE", CX, 200, YELLOW, maxw=150)
    safety(img)


FIN_START = 0.1    # la fin d'Hugo démarre 0,1 s après la fin de l'apnée


def voice():
    """Assemble intro + fin dans une seule piste, à leur place dans la vidéo."""
    import subprocess
    import wave

    def load(name):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'audio', name), '-f', 's16le',
                              '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.int16).astype(float) / 32768

    out = np.zeros(int(DUR * SR))
    add(out, 0.0, load('intro.mp3'), 1.0)
    add(out, INTRO + HOLD + FIN_START, load('fin.mp3'), 1.0)
    path = os.path.join(HERE, 'audio', 'voix.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return Narration(path, {}, [], DUR)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'apnee_tiktok.mp4'), DUR, voice(), loop=False,
                 music=lambda n, dur: np.zeros(n))
