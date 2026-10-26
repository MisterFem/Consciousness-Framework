"""Vidéo TikTok pixel art : défi d'apnée, niveau 2, « jusqu'à la baleine » (60 s).

Suite de l'apnée 1 (45 s, jusqu'au dauphin), qui a lancé la chaîne. Leçons
appliquées : l'océan et le chrono sont visibles dès la première image, le
départ se fait en 3 s au lieu de 7, et le record de l'épisode 1 (le dauphin,
45 s) est un palier à battre. On plonge plus profond : les abysses s'allument
de lumières bioluminescentes vers la fin. Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit apnee2_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle

Voix facultative : audio/intro.mp3 (calée sur INTRO) et audio/fin.mp3.
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

# voix d'Hugo (audio/intro.mp3) : « Niveau deux. Jusqu'à la baleine. Trois, deux, un ! »
COUNT = [2.33, 3.02, 3.77]   # 3, 2, 1
INTRO = 4.25
HOLD = 60.0
OUTRO = 7.5
DUR = INTRO + HOLD + OUTRO
EP1_RECORD = 45


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
SHRIMP = art(["..o.o.....", "...o.oooo.", "..ooooooko", ".oooooooo.", "o.o.o.o..."],
             {'o': (255, 140, 120), 'k': K})
JELLY = art(["..pppp..", ".pppppp.", "pppppppp", "pwpwpwpp", ".p.p.p..", "p..p..p.", ".p..p..p"],
            {'p': (220, 150, 255), 'w': WHITE})
CLOWN = art(["....oww...", "o.oowwooo.", "oooowwookw", "o.oowwooo.", "....oww..."],
            {'o': ORANGE, 'w': WHITE, 'k': K})
SEAHORSE = art([".yyy.", "yyky.", ".yy..", ".yyy.", "..yy.", ".yyy.", "..yy.", ".yy..", "y...."],
               {'y': YELLOW, 'k': K})
TURTLE = art(["...gggg....", "..gdgdgg.hh", "ggddgddgghk", "..gggggg.hh", ".h.....h..."],
             {'g': (60, 140, 70), 'd': (30, 90, 50), 'h': (120, 170, 90), 'k': K})
SHARK = art(["......g.........", ".....gg.........", "g..gggggggggg...", "gggggggggggggkg.",
             "g..gwwwwwwwwggg.", "........g......."], {'g': (120, 130, 150), 'w': WHITE, 'k': K})
DOLPHIN = art(["......b.......", ".....bb.......", "..bbbbbbbbb...", ".bbbbbbbbbkbb.",
               "bb.wwwwwwwbbbb", "b.....wwww....", "......b......."],
              {'b': (90, 150, 220), 'w': WHITE, 'k': K})
ORCA = art([".....k..........", "....kk..........", "k.kkkkkkkkkkkk..", "kkkkkkkkkkwkkkk.",
            "k.kwwwwwwwwkkkkk", "....www..wwww...", "......k........."], {'k': (20, 20, 30), 'w': WHITE})
WHALE = art(["b...............b....", "bb..bbbbbbbbbbbbbb...", ".bbbbbbbbbbbbbbbbbbb.",
             "bbbbbbbbbbbbbbbbbkbbb", "bb.lllllllllllllllbbb", "b....lllllllllllll...", "........l....l......."],
            {'b': (60, 90, 150), 'l': (150, 180, 220), 'k': K})

# (seconde d'apnée, nom du niveau, sprite, échelle)
LEVELS = [
    (6, "CREVETTE", SHRIMP, 4),
    (12, "MÉDUSE", JELLY, 4),
    (18, "POISSON-CLOWN", CLOWN, 4),
    (24, "HIPPOCAMPE", SEAHORSE, 4),
    (30, "TORTUE DE MER", TURTLE, 4),
    (36, "REQUIN", SHARK, 3),
    (EP1_RECORD, "DAUPHIN", DOLPHIN, 4),
    (52, "ORQUE", ORCA, 3),
    (60, "BALEINE", WHALE, 3),
]

# ---------------------------------------------------------------- l'océan
SURFACE = np.array([40, 120, 200])
DEEP = np.array([4, 6, 24])
_yy, _xx = np.mgrid[0:H, 0:W]
_bayer = BAYER[_yy % 4, _xx % 4]
_bg_cache = {}


def ocean(depth):
    """Fond tramé : on part déjà sous l'eau, on finit dans les abysses."""
    key = round(depth, 2)
    if key not in _bg_cache:
        v = np.clip(0.15 + depth * 0.85 + _yy / H * 0.3, 0, 1)
        levels = 6
        q = np.floor(v * (levels - 1) + _bayer).clip(0, levels - 1) / (levels - 1)
        a = SURFACE[None, None, :] * (1 - q[..., None]) + DEEP[None, None, :] * q[..., None]
        _bg_cache[key] = Image.fromarray(a.astype(np.uint8), 'RGB')
    return _bg_cache[key].copy()


_r = random.Random(7)
BUBBLES = [(_r.randrange(W), _r.random() * 400, 8 + _r.random() * 14, _r.choice((1, 1, 2))) for _ in range(28)]
FISH = [(_r.random() * 300, 70 + _r.random() * 150, 10 + _r.random() * 14, _r.random() < 0.5)
        for _ in range(14)]
GLOW = [(_r.randrange(W), _r.randrange(60, 250), _r.random() * 6.28, _r.choice([(90, 255, 220), (140, 200, 255),
         (220, 140, 255)])) for _ in range(46)]


def decor(img, t, depth):
    d = ImageDraw.Draw(img)
    if depth < 0.4:
        alpha = int(40 * (1 - depth / 0.4))
        for k in range(4):
            x = int((k * 55 + t * 6) % (W + 60)) - 30
            col = tuple(min(255, c + alpha) for c in (40, 120, 190))
            d.polygon([(x, 0), (x + 10, 0), (x + 50, H), (x + 34, H)], fill=None, outline=col)
    for x, y0, sp, r in BUBBLES:
        y = (y0 - t * sp) % 380 - 40
        xx = x + math.sin(t * 2 + y0) * 2
        d.ellipse([xx - r, y - r, xx + r, y + r], outline=(150, 200, 240) if depth < 0.7 else (70, 100, 150))
    if depth < 0.75:
        for x0, y, sp, left in FISH:
            x = (x0 + t * sp) % (W + 40) - 20
            if left:
                x = W - x
            img.paste((150, 200, 230), (int(x), int(y), int(x) + 4, int(y) + 2))
    # abysses : lumières bioluminescentes qui s'allument
    if depth > 0.55:
        k = clamp((depth - 0.55) / 0.3)
        px = img.load()
        for i, (x, y, ph, col) in enumerate(GLOW):
            if i / len(GLOW) > k:
                continue
            b = 0.5 + 0.5 * math.sin(t * 2.5 + ph)
            if b > 0.3:
                yy = int(y + math.sin(t + ph) * 3)
                px[x, yy] = col
                if b > 0.8 and 0 < x < W - 1:
                    px[x + 1, yy] = col
                    px[x - 1, yy] = col


# ---------------------------------------------------------------- interface
def gauge(img, sec):
    x0, x1, y0, y1 = 12, 22, 74, 214
    img.paste(SHADOW, (x0 - 2, y0 - 2, x1 + 2, y1 + 2))
    img.paste((20, 30, 70), (x0, y0, x1, y1))
    p = clamp(sec / HOLD)
    h = int((y1 - y0) * p)
    col = GREEN if p < 0.5 else (YELLOW if p < 0.8 else (ORANGE if p < 0.93 else RED))
    img.paste(col, (x0, y1 - h, x1, y1))
    for s, _, _, _ in LEVELS:
        y = int(y1 - (y1 - y0) * s / HOLD)
        img.paste(WHITE if sec >= s else LGREY, (x1, y, x1 + 4, y + 1))
    # repère du record de l'épisode 1
    y = int(y1 - (y1 - y0) * EP1_RECORD / HOLD)
    img.paste(PINK, (x0 - 2, y, x1 + 6, y + 1))


def chrono(img, sec):
    s = int(sec)
    draw_text(img, f"{s // 60:02d}:{s % 60:02d}", CX, TOP - 2, WHITE, scale=3, shadow=SHADOW)


def safety(img):
    img.paste(SHADOW, (20, 221, 160, 246))
    draw_text(img, "ASSIS, JAMAIS DANS L'EAU", CX, 222, LGREY, maxw=150, shadow=None)
    draw_text(img, "STOP AU MOINDRE VERTIGE", CX, 234, LGREY, maxw=150, shadow=None)


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
for k, tc in enumerate(COUNT):
    SFX.append((tc, 'place', 20 - k * 4))
SFX.append((INTRO, 'impact', None))
SHAKES.append((INTRO, 2))
for s, _, _, _ in LEVELS[:-1]:
    SFX.append((INTRO + s, 'sparkle' if s == EP1_RECORD else 'coin', None))
SFX.append((INTRO + HOLD, 'sparkle', None))


@scene(0.0, INTRO)
def s_intro(img, t):
    img.paste(ocean(0.0))
    decor(img, t, 0.0)
    draw_text(img, "APNÉE · NIVEAU 2", CX, TOP - 6, YELLOW, maxw=150)
    draw_text(img, "JUSQU'À LA", CX, TOP + 8, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "BALEINE", CX, TOP + 30, YELLOW, scale=3, shadow=PURPLE)
    put(img, WHALE, CX, 132 + math.sin(t * 2) * 2, 4)
    draw_text(img, "60 SECONDES · T'AS BATTU LE DAUPHIN ?", CX, 162, WHITE, maxw=150)
    if t < COUNT[0]:
        draw_text(img, "INSPIRE...", CX, 190, WHITE, scale=2)
    else:
        k = sum(1 for tc in COUNT if t >= tc)
        p = ease_out_back((t - COUNT[k - 1]) / 0.3)
        draw_text(img, str(4 - k), CX, int(186 + (1 - p) * 6), YELLOW, scale=3, shadow=PURPLE)
    safety(img)


def creature_track(img, t, sec):
    for s, name, spr, sc in LEVELS[:-1]:
        lt = sec - s
        if -0.1 < lt < 6.0:
            x = 210 - 120 * ease_out_back(lt / 0.8) if lt < 4.8 else 90 - (lt - 4.8) * 130
            y = 164 + math.sin(t * 2.5 + s) * 5
            put(img, spr, x, y, sc + 1)
    # la baleine se devine dans le noir avant d'arriver
    if sec > 54:
        p = clamp((sec - 54) / 6)
        put(img, WHALE, 260 - 170 * p, 170, 4)


@scene(INTRO, INTRO + HOLD)
def s_dive(img, t):
    sec = t - INTRO
    depth = sec / HOLD
    img.paste(ocean(depth))
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
        if EP1_RECORD <= sec < EP1_RECORD + 4:
            draw_text(img, "RECORD DU NIVEAU 1 ÉGALÉ !", CX, TOP + 70, PINK, maxw=150)
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
    put(img, WHALE, CX, 150 + math.sin(t * 2) * 3, 4)
    draw_text(img, "RESPIRE !", CX, TOP - 2, WHITE, scale=3, shadow=PURPLE)
    if lt > 0.6:
        p = ease_out_back((lt - 0.6) / 0.4)
        draw_text(img, "60 SECONDES", CX, int(TOP + 34 + (1 - p) * 6), YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "NIVEAU BALEINE", CX, TOP + 56, WHITE, scale=2, maxw=176, wave_t=t, rainbow=True,
                  shadow=PURPLE)
        px = img.load()
        for i in range(40):
            a = i * 0.157 + lt * 0.4
            dd = 40 + lt * 30 + (i % 4) * 6
            x, y = CX + math.cos(a) * dd, 130 + math.sin(a) * dd * 0.7
            if 0 <= x < W and 0 <= y < H and (int(lt * 10) + i) % 3:
                px[int(x), int(y)] = RAINBOW[i % 6]
    if lt > 2.5:
        img.paste(SHADOW, (14, 178, 156, 216))
        draw_text(img, "T'AS LÂCHÉ À QUEL ANIMAL ?", CX, 182, WHITE, maxw=150)
        draw_text(img, "DÉFIE UN POTE !", CX, 198, YELLOW, maxw=150)
    safety(img)


def voice():
    """Voix facultative : intro au début, fin au « RESPIRE ! »."""
    import subprocess
    import wave
    files = [(0.0, 'intro.mp3'), (INTRO + HOLD + 0.1, 'fin.mp3')]
    if not all(os.path.exists(os.path.join(HERE, 'audio', f)) for _, f in files):
        return None

    def load(name):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'audio', name), '-f', 's16le',
                              '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.int16).astype(float) / 32768

    out = np.zeros(int(DUR * SR))
    for t0, f in files:
        add(out, t0, load(f), 1.0)
    path = os.path.join(HERE, 'audio', 'voix.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return Narration(path, {}, [], DUR)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'apnee2_tiktok.mp4'), DUR, voice(), loop=False,
                 music=lambda n, dur: np.zeros(n))
