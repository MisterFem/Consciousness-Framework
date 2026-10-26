"""Vidéo TikTok pixel art : défi d'apnée, épisode FINAL, « jusqu'au Mégalodon » (75 s).

Clôture de la série (niveau 1 : dauphin 45 s, niveau 2 : baleine 60 s). On
plonge dans les abysses préhistoriques : un monstre disparu à chaque palier,
les records des épisodes précédents en repères sur la jauge, et le Mégalodon
en boss final. Intro un peu plus longue (voix d'Hugo), fin en « clap de fin »
avec le récapitulatif des trois boss. Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit apnee3_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle

Voix facultative : audio/intro.mp3 et audio/fin.mp3 (voir texte_voix.txt).
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

# voix d'Hugo (audio/intro.mp3) — temps estimés, à recaler sur l'enregistrement
# intro resserrée (~7 s, voix à vitesse normale) : pauses raccourcies, « le dauphin… la baleine… »
# retirés de la voix (les icônes restent à l'écran)
DOLPH_T, WHALE_T, MEGA_T = 0.5, 1.0, 3.29     # icônes du dauphin, de la baleine ; « le Mégalodon »
INSPIRE_T = 4.33              # « Grande inspiration… »
COUNT = [5.60, 6.12, 6.61]    # trois, deux, un
INTRO = 7.1
HOLD = 75.0
OUTRO = 12.0
DUR = INTRO + HOLD + OUTRO
RECORDS = [(45, "DAUPHIN", PINK), (60, "BALEINE", (120, 200, 255))]


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


# ---------------------------------------------------------------- monstres
K = INK
AMMONITE = art([".ssss.", "sbbbbs", "sbsssb", "sbsbsb", "sbbsbs", ".ssss."],
               {'s': (210, 170, 120), 'b': (150, 100, 60)})
COELA = art(["...bbb.......", "b.bbbbbbbb...", "bbbwbwbwbbkb.", "b.bbbbbbbbbb.", "...b..b......"],
            {'b': (60, 80, 140), 'w': (200, 200, 230), 'k': K})
ARCHELON = art(["....ggggg.....", "...gdgdgdg..hh", ".ggdgdgdgdghkh", "...ggggggg..hh", "..h......h...."],
               {'g': (90, 110, 80), 'd': (50, 70, 50), 'h': (140, 150, 110), 'k': K})
DUNKLE = art(["..aaaa.........", ".aaaaaaggggg...", "aakaaaggggggg..", "awwwaggggggggg.", "aaaaagggggg....",
              ".aa.....g......"], {'a': (150, 140, 120), 'g': (90, 90, 110), 'w': WHITE, 'k': K})
ICHTHYO = art(["......b........", ".....bb........", "..bbbbbbbbbb...", "bbbbbbbbbbbkbbb", "b..lllllllll...",
               ".....b..b......"], {'b': (110, 120, 150), 'l': (190, 190, 210), 'k': K})
PLESIO = art(["..............gg", ".............gkg", "............gg..", "...........gg...", "....gggggggg....",
              "..gggggggggg....", "gggggggggg......", "..g...g.........", ], {'g': (80, 130, 110), 'k': K})
MOSA = art(["................rr", "..rrrrrrrrrrrrrrkr", "rrrrrrrrrrrrrrrrrr", "r.rllllllllllwwwww", "...r....r.........",
            ], {'r': (90, 110, 90), 'l': (170, 180, 150), 'w': WHITE, 'k': K})
MEGALODON = art(["..........g.............", ".........ggg............", "g......gggggggggggg.....",
                 "gg...ggggggggggggggggg..", "ggggggggggggggggggggkggg", "gg..gllllllllllllwwwwwww",
                 "g......llllllllllwwwwww.", ".........g......g.......", ],
                {'g': (80, 90, 110), 'l': (170, 175, 190), 'w': WHITE, 'k': (200, 30, 40)})
DOLPHIN = art(["......b.......", ".....bb.......", "..bbbbbbbbb...", ".bbbbbbbbbkbb.",
               "bb.wwwwwwwbbbb", "b.....wwww....", "......b......."],
              {'b': (90, 150, 220), 'w': WHITE, 'k': K})
WHALE = art(["b...............b....", "bb..bbbbbbbbbbbbbb...", ".bbbbbbbbbbbbbbbbbbb.",
             "bbbbbbbbbbbbbbbbbkbbb", "bb.lllllllllllllllbbb", "b....lllllllllllll...", "........l....l......."],
            {'b': (60, 90, 150), 'l': (150, 180, 220), 'k': K})

# (seconde d'apnée, nom, sprite, échelle)
LEVELS = [
    (8, "AMMONITE", AMMONITE, 5),
    (16, "CŒLACANTHE", COELA, 4),
    (24, "ARCHELON", ARCHELON, 4),
    (32, "DUNKLEOSTEUS", DUNKLE, 4),
    (40, "ICHTHYOSAURE", ICHTHYO, 4),
    (50, "PLÉSIOSAURE", PLESIO, 4),
    (65, "MOSASAURE", MOSA, 3),
    (75, "MÉGALODON", MEGALODON, 3),
]

# ---------------------------------------------------------------- les abysses
TOP_COL = np.array([20, 70, 120])
DEEP = np.array([2, 4, 14])
_yy, _xx = np.mgrid[0:H, 0:W]
_bayer = BAYER[_yy % 4, _xx % 4]
_bg_cache = {}


def ocean(depth):
    key = round(depth, 2)
    if key not in _bg_cache:
        v = np.clip(0.3 + depth * 0.7 + _yy / H * 0.3, 0, 1)
        levels = 6
        q = np.floor(v * (levels - 1) + _bayer).clip(0, levels - 1) / (levels - 1)
        a = TOP_COL[None, None, :] * (1 - q[..., None]) + DEEP[None, None, :] * q[..., None]
        _bg_cache[key] = Image.fromarray(a.astype(np.uint8), 'RGB')
    return _bg_cache[key].copy()


_r = random.Random(11)
BUBBLES = [(_r.randrange(W), _r.random() * 400, 8 + _r.random() * 14, _r.choice((1, 1, 2))) for _ in range(24)]
GLOW = [(_r.randrange(W), _r.randrange(60, 250), _r.random() * 6.28, _r.choice([(90, 255, 220), (140, 200, 255),
         (220, 140, 255), (255, 120, 120)])) for _ in range(60)]
ROCKS = [(_r.randrange(0, W), _r.randrange(8, 30)) for _ in range(12)]


def decor(img, t, depth):
    d = ImageDraw.Draw(img)
    for x, y0, sp, r in BUBBLES:
        y = (y0 - t * sp) % 380 - 40
        xx = x + math.sin(t * 2 + y0) * 2
        d.ellipse([xx - r, y - r, xx + r, y + r], outline=(60, 100, 140) if depth < 0.5 else (40, 60, 90))
    k = clamp(0.2 + depth)
    px = img.load()
    for i, (x, y, ph, col) in enumerate(GLOW):
        if i / len(GLOW) > k:
            continue
        b = 0.5 + 0.5 * math.sin(t * 2.5 + ph)
        if b > 0.3:
            yy = int(y + math.sin(t + ph) * 3)
            px[x, yy] = col
    # fond rocheux qui remonte
    base = H - int(10 + depth * 30)
    img.paste((14, 14, 22), (0, base, W, H))
    for x, h in ROCKS:
        img.paste((22, 22, 34), (x - 6, base - h // 3, x + 6, base))


# ---------------------------------------------------------------- interface
def gauge(img, sec):
    x0, x1, y0, y1 = 12, 22, 74, 214
    img.paste(SHADOW, (x0 - 2, y0 - 2, x1 + 2, y1 + 2))
    img.paste((20, 30, 70), (x0, y0, x1, y1))
    p = clamp(sec / HOLD)
    h = int((y1 - y0) * p)
    col = GREEN if p < 0.5 else (YELLOW if p < 0.75 else (ORANGE if p < 0.9 else RED))
    img.paste(col, (x0, y1 - h, x1, y1))
    for s, _, _, _ in LEVELS:
        y = int(y1 - (y1 - y0) * s / HOLD)
        img.paste(WHITE if sec >= s else LGREY, (x1, y, x1 + 4, y + 1))
    for s, _, c in RECORDS:
        y = int(y1 - (y1 - y0) * s / HOLD)
        img.paste(c, (x0 - 2, y, x1 + 6, y + 1))


def chrono(img, sec):
    s = int(sec)
    draw_text(img, f"{s // 60:02d}:{s % 60:02d}", CX, TOP - 2, WHITE, scale=3, shadow=SHADOW)


def safety(img):
    img.paste(SHADOW, (20, 221, 160, 246))
    draw_text(img, "ASSIS, JAMAIS DANS L'EAU", CX, 222, LGREY, maxw=150, shadow=None)
    draw_text(img, "STOP AU MOINDRE VERTIGE", CX, 234, LGREY, maxw=150, shadow=None)


def silhouette(spr, col=(10, 12, 22)):
    a = np.array(spr)
    a[a[..., 3] > 0, :3] = col
    return Image.fromarray(a, 'RGBA')


MEGA_SIL = silhouette(MEGALODON)

# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
SHAKES.append((MEGA_T, 3))
SFX.append((MEGA_T, 'impact', None))
for k, tc in enumerate(COUNT):
    SFX.append((tc, 'place', 20 - k * 4))
SFX.append((INTRO, 'impact', None))
SHAKES.append((INTRO, 3))
for s, _, _, _ in LEVELS[:-1]:
    SFX.append((INTRO + s, 'coin', None))
for s, _, _ in RECORDS:
    SFX.append((INTRO + s, 'sparkle', None))
SFX.append((INTRO + HOLD, 'impact', None))
SHAKES.append((INTRO + HOLD, 4))


@scene(0.0, INTRO)
def s_intro(img, t):
    img.paste(ocean(0.15))
    decor(img, t, 0.15)
    # le Mégalodon passe dans le noir derrière le titre
    put(img, MEGA_SIL, 240 - (t * 30) % 360, 200, 5)
    draw_text(img, "APNÉE · ÉPISODE FINAL", CX, TOP - 6, RED, maxw=160)
    draw_text(img, "JUSQU'AU", CX, TOP + 10, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "MÉGALODON", CX, TOP + 32, YELLOW, scale=3, shadow=PURPLE, maxw=176)
    # rappel des boss précédents
    if t > DOLPH_T:
        for k, (spr, lab, sc) in enumerate(((DOLPHIN, "45 S", 2), (WHALE, "60 S", 1))):
            if t < (DOLPH_T, WHALE_T)[k]:
                continue
            x = 56 + k * 68
            put(img, spr, x, 128, sc)
            draw_text(img, lab, x, 140, LGREY)
            ImageDraw.Draw(img).line([(x - 16, 126), (x + 16, 132)], fill=GREEN, width=1)
        if t > 1.5:
            draw_text(img, "DÉJÀ BATTUS ?", CX, 152, WHITE, maxw=150)
    if t < COUNT[0]:
        if t >= INSPIRE_T:
            draw_text(img, "INSPIRE...", CX, 184, WHITE, scale=2)
        else:
            draw_text(img, "75 SECONDES", CX, 184, YELLOW, scale=2, shadow=PURPLE)
    else:
        k = sum(1 for tc in COUNT if t >= tc)
        p = ease_out_back((t - COUNT[k - 1]) / 0.3)
        draw_text(img, str(4 - k), CX, int(180 + (1 - p) * 6), YELLOW, scale=3, shadow=PURPLE)
    safety(img)


def creature_track(img, t, sec):
    for s, name, spr, sc in LEVELS[:-1]:
        lt = sec - s
        if -0.1 < lt < 7.0:
            x = 220 - 130 * ease_out_back(lt / 0.8) if lt < 5.6 else 90 - (lt - 5.6) * 140
            y = 166 + math.sin(t * 2.5 + s) * 5
            put(img, spr, x, y, sc + (1 if sc < 5 else 0))
    # le Mégalodon rôde en silhouette, puis surgit
    if sec > 66:
        p = clamp((sec - 66) / 9)
        put(img, MEGA_SIL if sec < 74 else MEGALODON, 300 - 210 * p, 168, 4)


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
    else:
        draw_text(img, "BLOQUE !", CX, TOP + 40, WHITE, scale=2, shadow=PURPLE)
    for s, name, c in RECORDS:
        if s <= sec < s + 4:
            draw_text(img, f"RECORD {name} BATTU !", CX, TOP + 70, c, maxw=150)
    nxt = [lv for lv in LEVELS if sec < lv[0]]
    if nxt and sec > 0.5:
        draw_text(img, f"PROCHAIN : {nxt[0][1]}", 96, 196, WHITE, maxw=136)
    safety(img)


FIN = INTRO + HOLD


@scene(FIN, DUR)
def s_win(img, t):
    lt = t - FIN
    img.paste(ocean(1.0))
    decor(img, t, 1.0)
    if lt < 5.0:
        put(img, MEGALODON, CX, 162 + math.sin(t * 2) * 3, 4)
        draw_text(img, "RESPIRE !", CX, TOP - 2, WHITE, scale=3, shadow=PURPLE)
        if lt > 0.6:
            p = ease_out_back((lt - 0.6) / 0.4)
            draw_text(img, "75 SECONDES", CX, int(TOP + 34 + (1 - p) * 6), YELLOW, scale=2, shadow=PURPLE)
            draw_text(img, "NIVEAU", CX, TOP + 56, WHITE, scale=2, shadow=PURPLE)
            draw_text(img, "MÉGALODON", CX, TOP + 78, WHITE, scale=2, maxw=176, wave_t=t,
                      rainbow=True, shadow=PURPLE)
            px = img.load()
            for i in range(50):
                a = i * 0.126 + lt * 0.4
                dd = 40 + lt * 30 + (i % 4) * 6
                x, y = CX + math.cos(a) * dd, 130 + math.sin(a) * dd * 0.7
                if 0 <= x < W and 0 <= y < H and (int(lt * 10) + i) % 3:
                    px[int(x), int(y)] = RAINBOW[i % 6]
    else:
        # clap de fin : les trois boss de la série
        p = clamp((lt - 5.0) / 0.6)
        draw_text(img, "FIN DE LA SÉRIE", CX, TOP - 4, YELLOW, scale=2, shadow=PURPLE, maxw=176)
        for k, (spr, lab, sc, y) in enumerate(((DOLPHIN, "NIVEAU 1 · 45 S", 2, 92),
                                                (WHALE, "NIVEAU 2 · 60 S", 2, 124),
                                                (MEGALODON, "NIVEAU 3 · 75 S", 2, 160))):
            if lt > 5.0 + k * 0.5:
                put(img, spr, 54, y, sc)
                draw_text(img, lab, 124, y - 6, WHITE, maxw=100)
        if lt > 7.0:
            img.paste(SHADOW, (14, 182, 156, 216))
            draw_text(img, "TON RECORD FINAL ?", CX, 186, WHITE, maxw=150)
            draw_text(img, "DIS-LE EN COMMENTAIRE", CX, 200, YELLOW, maxw=150)
        if lt > DUR - FIN - 1.0:
            k = clamp((DUR - t) / 1.0)
            img.paste(Image.eval(img, lambda v: int(v * k)))
    safety(img)


def voice():
    import subprocess
    import wave
    files = [(0.0, 'intro.mp3'), (FIN + 0.1, 'fin.mp3')]
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
    render_video(os.path.join(HERE, 'apnee3_tiktok.mp4'), DUR, voice(), loop=False,
                 music=lambda n, dur: np.zeros(n))
