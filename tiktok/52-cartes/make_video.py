"""Vidéo TikTok pixel art : pourquoi un paquet de 52 cartes n'est (quasi) jamais
mélangé deux fois dans le même ordre.

Tout est généré procéduralement (images + musique chiptune + bruitages),
aucune ressource externe. Rendu interne 180x320, agrandi x6 -> 1080x1920.

    python3 make_video.py            # produit 52_cartes_tiktok.mp4
"""
import math
import os
import random
import subprocess
import wave

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, S, FPS = 180, 320, 6, 30
DUR = 0.0  # calculé plus bas (scène 8)
SR = 44100

# ---------------------------------------------------------------- palette
BLACK = (0, 0, 0)
NAVY = (29, 43, 83)
PURPLE = (126, 37, 83)
DGREEN = (0, 135, 81)
BROWN = (171, 82, 54)
DGREY = (95, 87, 79)
LGREY = (194, 195, 199)
WHITE = (255, 241, 232)
RED = (255, 0, 77)
ORANGE = (255, 163, 0)
YELLOW = (255, 236, 39)
GREEN = (0, 228, 54)
BLUE = (41, 173, 255)
LAVENDER = (131, 118, 156)
PINK = (255, 119, 168)
PEACH = (255, 204, 170)
INK = (22, 23, 48)
SHADOW = (12, 10, 30)
RAINBOW = [RED, ORANGE, YELLOW, GREEN, BLUE, PINK]

# ---------------------------------------------------------------- polices
FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '.': [".", ".", ".", ".", ".", ".", "#"],
    ',': ["..", "..", "..", "..", "..", "..", ".#", "#."],
    '!': ["#", "#", "#", "#", "#", ".", "#"],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ':': [".", ".", "#", ".", ".", "#", "."],
    "'": ["#", "#", ".", ".", ".", ".", "."],
    '-': ["....", "....", "....", "####", "....", "....", "...."],
    '×': [".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."],
    '≈': [".....", ".##.#", "#.##.", ".....", ".##.#", "#.##.", "....."],
    '~': [".....", ".....", ".##.#", "#.##.", ".....", ".....", "....."],
    '=': [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    '+': [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    '%': ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    '/': ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    '(': ["..#", ".#.", "#..", "#..", "#..", ".#.", "..#"],
    ')': ["#..", ".#.", "..#", "..#", "..#", ".#.", "#.."],
    '°': [".#.", "#.#", ".#.", "...", "...", "...", "..."],
}
ACC = {
    'acute': ["...#.", "..#.."], 'grave': [".#...", "..#.."],
    'circ': ["..#..", ".#.#."], 'trema': [".#.#.", "....."],
}
ACCENTED = {
    'É': ('E', 'acute'), 'È': ('E', 'grave'), 'Ê': ('E', 'circ'), 'Ë': ('E', 'trema'),
    'À': ('A', 'grave'), 'Â': ('A', 'circ'), 'Ù': ('U', 'grave'), 'Û': ('U', 'circ'),
    'Î': ('I', 'circ'), 'Ï': ('I', 'trema'), 'Ô': ('O', 'circ'), 'Ç': ('C', None),
}
FONT3 = {
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#.", "##.", ".#.", ".#.", "###"],
    '2': ["###", "..#", "###", "#..", "###"], '3': ["###", "..#", "###", "..#", "###"],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "###", "..#", "###"],
    '6': ["###", "#..", "###", "#.#", "###"], '7': ["###", "..#", "..#", "..#", "..#"],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "###"],
    'A': [".#.", "#.#", "###", "#.#", "#.#"], 'J': ["..#", "..#", "..#", "#.#", ".#."],
    'Q': [".#.", "#.#", "#.#", "##.", ".##"], 'K': ["#.#", "#.#", "##.", "#.#", "#.#"],
    'T': ["#.###", "#.#.#", "#.#.#", "#.#.#", "#.###"],  # "10" compact
    'X': ["...", "#.#", ".#.", "#.#", "..."],
}
SUIT5 = {
    'H': ["##.##", "#####", "#####", ".###.", "..#.."],
    'D': ["..#..", ".###.", "#####", ".###.", "..#.."],
    'S': ["..#..", ".###.", "#####", "#####", "..#.."],
    'C': [".###.", ".###.", "#####", "#####", "..#.."],
}
SUIT7 = {
    'H': [".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."],
    'D': ["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
    'S': ["...#...", "..###..", ".#####.", "#######", "#######", "...#...", "..###.."],
    'C': ["..###..", "..###..", "##.#.##", "#######", "##.#.##", "...#...", "..###.."],
}
SUIT_COL = {'H': RED, 'D': RED, 'S': INK, 'C': INK}


def rows_to_mask(rows):
    return np.array([[c == '#' for c in r] for r in rows], dtype=bool)


def mask_img(m, scale=1):
    im = Image.fromarray((m * 255).astype(np.uint8), 'L')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return im


_mask_cache = {}


def glyph(key, scale):
    """key = ('g', ch) glyphe normal 5x7 ou ('s', ch) chiffre en exposant."""
    ck = (key, scale)
    if ck in _mask_cache:
        return _mask_cache[ck]
    kind, ch = key
    if kind == 's':
        m = np.zeros((12, 3), bool)
        m[1:6, :] = rows_to_mask(FONT3[ch])
    else:
        base, acc = ACCENTED.get(ch, (ch, None))
        rows = FONT[base]
        w = len(rows[0])
        m = np.zeros((12, w), bool)
        for r, row in enumerate(rows):
            rr = 2 + r if r < 7 else 9 + (r - 7)
            m[rr, :] = [c == '#' for c in row]
        if acc:
            m[0:2, :] = rows_to_mask(ACC[acc])[:, :w]
        if ch == 'Ç':
            m[9, 2] = m[10, 1] = m[10, 2] = True
    im = mask_img(m, scale)
    _mask_cache[ck] = im
    return im


def advance(key):
    return 4 if key[0] == 's' else glyph(key, 1).width + 1


def layout(text, maxw):
    """Retourne [(lignes, largeur)], chaque ligne = [(idx, key, x, hl)]."""
    words, cur = [], []
    sup = hl = False
    for i, ch in enumerate(text.upper()):
        if ch == ' ' or ch == '\n':
            words.append(cur)
            cur = []
            if ch == '\n':
                words.append('\n')
            sup = False
            continue
        if ch == '*':
            hl = not hl
            continue
        if ch == '^':
            sup = True
            continue
        if sup and not ch.isdigit():
            sup = False
        cur.append((i, ('s' if sup else 'g', ch), hl))
    words.append(cur)

    lines, line, lw = [], [], 0
    for wd in words:
        if wd == '\n':
            lines.append((line, lw))
            line, lw = [], 0
            continue
        if not wd:
            continue
        ww = sum(advance(k) for _, k, _ in wd)
        gap = 3 if line else 0
        if line and lw + gap + ww - 1 > maxw:
            lines.append((line, lw))
            line, lw, gap = [], 0, 0
        x = lw + gap
        for i, k, h in wd:
            line.append((i, k, x, h))
            x += advance(k)
        lw = x - 1
    lines.append((line, lw))
    return lines


_layout_cache = {}


def draw_text(img, text, cx, y, color=WHITE, scale=1, maxw=150, reveal=10 ** 9,
              hl_color=YELLOW, shadow=SHADOW, wave_t=None, rainbow=False, lh=12):
    key = (text, maxw // scale)
    if key not in _layout_cache:
        _layout_cache[key] = layout(text, maxw // scale)
    lines = _layout_cache[key]
    for li, (line, lw) in enumerate(lines):
        x0 = cx - (lw * scale) // 2
        yy = y + li * lh * scale
        for i, k, x, h in line:
            if i >= reveal:
                continue
            m = glyph(k, scale)
            col = hl_color if h else color
            if rainbow:
                col = RAINBOW[(i + int((wave_t or 0) * 8)) % len(RAINBOW)]
            dy = 0
            if wave_t is not None:
                dy = int(round(math.sin(wave_t * 7 - i * 0.7) * 2 * scale / 2))
            px, py = x0 + x * scale, yy + dy
            if shadow:
                img.paste(shadow, (px + scale, py + scale), m)
            img.paste(col, (px, py), m)
    return len(lines) * lh * scale


# ---------------------------------------------------------------- audio events
SFX = []  # (temps, type, param)


class T:
    """Texte en machine à écrire, avec ses 'blips' enregistrés pour l'audio."""

    def __init__(self, text, t0, y, cps=22, blip=True, **kw):
        self.text, self.t0, self.y, self.cps, self.kw = text, t0, y, cps, kw
        if blip:
            n = 0
            for i, ch in enumerate(text):
                if ch not in ' *^\n':
                    if n % 2 == 0:
                        SFX.append((t0 + i / cps, 'blip', None))
                    n += 1

    def end(self):
        return self.t0 + len(self.text) / self.cps

    def draw(self, img, t, cx=90):
        if t >= self.t0:
            draw_text(img, self.text, cx, self.y,
                      reveal=int((t - self.t0) * self.cps) + 1, **self.kw)


# ---------------------------------------------------------------- sprites
def stamp(img, rows, x, y, col):
    img.paste(col, (int(x), int(y)), mask_img(rows_to_mask(rows)))


def make_card(rank, suit):
    im = Image.new('RGBA', (22, 30), (0, 0, 0, 0))
    a = np.zeros((30, 22, 4), np.uint8)
    a[1:29, 0:22] = (*WHITE, 255)
    a[0:30, 1:21] = (*WHITE, 255)
    a[0, 1:21] = a[29, 1:21] = (*DGREY, 255)
    a[1:29, 0] = a[1:29, 21] = (*DGREY, 255)
    a[28, 1:21] = (*LGREY, 255)
    im = Image.fromarray(a, 'RGBA')
    col = SUIT_COL[suit]
    stamp(im, FONT3[rank], 2, 2, col)
    stamp(im, SUIT5[suit], 2, 8, col)
    stamp(im, SUIT7[suit], 8, 12, col)
    corner = im.crop((2, 2, 7, 13)).rotate(180)
    im.paste(corner, (15, 16), corner)
    return im


def make_back():
    a = np.zeros((30, 22, 4), np.uint8)
    a[1:29, 0:22] = (*WHITE, 255)
    a[0:30, 1:21] = (*WHITE, 255)
    a[0, 1:21] = a[29, 1:21] = (*DGREY, 255)
    a[1:29, 0] = a[1:29, 21] = (*DGREY, 255)
    for yy in range(3, 27):
        for xx in range(3, 19):
            a[yy, xx] = (*RED, 255) if (xx + yy) % 4 else (*PURPLE, 255)
            if (xx - yy) % 4 == 0:
                a[yy, xx] = (*PINK, 255)
    return Image.fromarray(a, 'RGBA')


def make_mini(rank, suit):
    a = np.zeros((13, 10, 4), np.uint8)
    a[1:12, 0:10] = (*WHITE, 255)
    a[0:13, 1:9] = (*WHITE, 255)
    a[12, 1:9] = (*LGREY, 255)
    im = Image.fromarray(a, 'RGBA')
    col = SUIT_COL[suit]
    stamp(im, FONT3[rank], 1, 1, col)
    stamp(im, SUIT5[suit], 3, 7, col)
    return im


RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
SUITS = ['S', 'H', 'D', 'C']
DECK = [(r, s) for s in SUITS for r in RANKS]
CARDS = {c: make_card(*c) for c in DECK}
MINIS = {c: make_mini(*c) for c in DECK}
BACK = make_back()


def paste_sprite(img, spr, cx, cy, angle=0.0):
    if angle:
        spr = spr.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(spr, (int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))), spr)


# ---------------------------------------------------------------- fond
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BG_COLS = np.array([(9, 9, 26), (16, 18, 46), (24, 30, 66), (38, 34, 82), (60, 38, 92)])


def make_bg():
    yy, xx = np.mgrid[0:H, 0:W]
    v = yy / (H - 1) * (len(BG_COLS) - 1)
    idx = np.floor(v + BAYER[yy % 4, xx % 4] - 0.5).clip(0, len(BG_COLS) - 1).astype(int)
    return Image.fromarray(BG_COLS[idx].astype(np.uint8), 'RGB')


BG = make_bg()
rng = random.Random(52)
STARS = [(rng.randrange(W), rng.randrange(H - 60), rng.random() * 6.28, 1 + rng.random() * 3)
         for _ in range(70)]


def draw_stars(img, t):
    px = img.load()
    for x, y, ph, sp in STARS:
        b = 0.5 + 0.5 * math.sin(t * sp + ph)
        if b > 0.85:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    px[x + dx, y + dy] = WHITE if (dx, dy) == (0, 0) else LAVENDER
        elif b > 0.35:
            px[x, y] = LGREY
        else:
            px[x, y] = LAVENDER if b > 0.15 else (50, 50, 90)


# ---------------------------------------------------------------- utilitaires
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_out_back(p):
    p = clamp(p)
    c1 = 1.70158
    return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2


def ease_out_bounce(p):
    p = clamp(p)
    n, d = 7.5625, 2.75
    if p < 1 / d:
        return n * p * p
    if p < 2 / d:
        p -= 1.5 / d
        return n * p * p + 0.75
    if p < 2.5 / d:
        p -= 2.25 / d
        return n * p * p + 0.9375
    p -= 2.625 / d
    return n * p * p + 0.984375


SHAKES = []  # (t0, amplitude)


def impact(t, amp=3):
    SHAKES.append((t, amp))
    SFX.append((t, 'impact', None))


def title(img, text, t, t0, y=26, color=YELLOW, scale=2):
    p = ease_out_bounce((t - t0) / 0.7)
    yy = int(-30 + (y + 30) * p)
    if t >= t0:
        draw_text(img, text, 90, yy, color, scale=scale, maxw=170, shadow=PURPLE)


# ================================================================ SCÈNES
SCENES = []


def scene(t0, t1):
    def deco(fn):
        SCENES.append((t0, t1, fn))
        return fn
    return deco


def read(tx):
    """Temps laissé pour finir de lire un texte une fois tapé."""
    t_ = tx.text if isinstance(tx, T) else tx
    return 1.0 + sum(c not in " *^" for c in t_) / 30


def after(tx, extra=0.0):
    return tx.end() + read(tx) + extra


# 1 ─ accroche ------------------------------------------------------------
FAN = [('A', 'S'), ('K', 'H'), ('Q', 'D'), ('J', 'C'), ('T', 'H'), ('7', 'S'), ('2', 'D')]
S1_T = T("QUAND TU MÉLANGES BIEN UN PAQUET DE *52 CARTES*...", 1.7, 205, scale=1)
S2 = after(S1_T)
SFX.append((0.0, 'crash', None))
SFX.append((1.0, 'whoosh', None))


@scene(0.0, S2)
def s1(img, t):
    title(img, "LE SAVAIS-TU ?", t, 0.1, y=40)
    open_ = ease_out_back((t - 0.9) / 0.6)
    bob = math.sin(t * 3) * 2
    for i, c in enumerate(FAN):
        a = (i - 3) * 13 * open_
        r = 26
        cx = 90 + math.sin(math.radians(a)) * r
        cy = 150 + bob - math.cos(math.radians(a)) * r + 10
        paste_sprite(img, CARDS[c], cx, cy, -a)
    S1_T.draw(img, t)


# 2 ─ tornade de cartes --------------------------------------------------
S2_T = T("... TU OBTIENS PRESQUE À COUP SÛR UN ORDRE QUE *PERSONNE* N'A JAMAIS VU DANS TOUTE L'HISTOIRE !",
         S2 + 0.6, 190)
S3_START = after(S2_T)
ORBIT = random.Random(7).sample(DECK, 12)
for k in range(6):
    SFX.append((S2 + 0.1 + k * 0.45, 'whoosh', None))


@scene(S2, S3_START)
def s2(img, t):
    lt = t - S2
    theta = 2.0 * lt + 0.9 * min(lt, 3) ** 2 + 5.4 * max(lt - 3, 0)
    items = []
    for i, c in enumerate(ORBIT):
        th = theta + i * 2 * math.pi / len(ORBIT)
        x = 90 + 64 * math.cos(th)
        y = 115 + 30 * math.sin(th) + math.sin(lt * 4 + i) * 4
        items.append((math.sin(th), x, y, c, math.cos(th) * 20))
    for depth, x, y, c, ang in sorted(items):
        paste_sprite(img, CARDS[c] if depth > -0.2 else BACK, x, y, ang)
    S2_T.draw(img, t)


# 3 ─ pourquoi ? 52 x 51 x ... ------------------------------------------
GRID_ORDER = random.Random(2024).sample(DECK, 52)
PLACE_T = []
tt = S3_START + 0.9
for k in range(52):
    PLACE_T.append(tt)
    tt += 1.6 if k < 3 else max(0.03, 0.14 - (k - 3) * 0.004)
for k, pt in enumerate(PLACE_T):
    SFX.append((pt, 'place', k))
S3_F = T("52 × 51 × 50 × ... × 1", PLACE_T[-1] + 0.4, 160, cps=24)
S3_EQ_T = S3_F.end() + 0.35
impact(S3_EQ_T, 2)
S3_N = T("(ON APPELLE ÇA *FACTORIELLE 52*)", S3_EQ_T + 1.2, 222, color=LGREY)
S4 = after(S3_N, 0.5)


@scene(S3_START, S4)
def s3(img, t):
    title(img, "POURQUOI ?", t, S3_START + 0.05, y=22)
    x0, y0 = 13, 58
    for k, c in enumerate(GRID_ORDER):
        if t < PLACE_T[k]:
            x, y = x0 + (k % 13) * 12, y0 + (k // 13) * 15
            img.paste((40, 40, 80), (x + 1, y + 1, x + 9, y + 12))
    for k, c in enumerate(GRID_ORDER):
        if t >= PLACE_T[k]:
            p = clamp((t - PLACE_T[k]) / 0.15)
            x, y = x0 + (k % 13) * 12, y0 + (k // 13) * 15 - int(6 * (1 - p))
            img.paste(MINIS[c], (x, y), MINIS[c])
    placed = sum(1 for pt in PLACE_T if t >= pt)
    if 0 < placed and t < S3_F.t0:
        n = placed
        label = "1RE CARTE" if n == 1 else ("DERNIÈRE" if n == 52 else f"{n}E CARTE")
        draw_text(img, f"{label} : *{53 - n} CHOIX*", 90, 130)
        if t < S3_F.t0:
            draw_text(img, "PEU IMPORTE LES CARTES DÉJÀ POSÉES, IL EN RESTE UNE DE MOINS",
                      90, 160, LGREY, maxw=140)
    S3_F.draw(img, t)
    if t >= S3_EQ_T:
        p = ease_out_back((t - S3_EQ_T) / 0.4)
        draw_text(img, "= 52 !", 90, int(178 + (1 - p) * 20), YELLOW, scale=3, shadow=PURPLE)
    S3_N.draw(img, t)


# 4 ─ le nombre ----------------------------------------------------------
FACT = str(math.factorial(52))
S4_D0 = S4 + 1.0
S4_CPS = 40
for i in range(0, len(FACT), 2):
    SFX.append((S4_D0 + i / S4_CPS, 'blip', None))
S4_APPROX = S4_D0 + len(FACT) / S4_CPS + 0.5
impact(S4_APPROX, 4)
SFX.append((S4_APPROX + 0.05, 'coin', None))
S4_T1 = T("UN NOMBRE À *68 CHIFFRES* !", S4_APPROX + 1.4, 176)
S4_T2 = T("BEAUCOUP TROP GRAND POUR QUE NOTRE CERVEAU PUISSE L'IMAGINER...",
          after(S4_T1), 204, color=LGREY)


S5 = after(S4_T2)


@scene(S4, S5)
def s4(img, t):
    title(img, "52 ! =", t, S4 + 0.05, y=24)
    n = int((t - S4_D0) * S4_CPS) + 1 if t >= S4_D0 else 0
    for i, d in enumerate(FACT[:n]):
        x = 22 + (i % 17) * 8
        y = 60 + (i // 17) * 14
        m = mask_img(rows_to_mask(FONT3[d]), 2)
        img.paste(SHADOW, (x + 1, y + 1), m)
        img.paste(WHITE if i >= n - 3 else LGREY, (x, y), m)
    if t >= S4_APPROX:
        draw_text(img, "≈ 8 × 10^67", 90, 122, YELLOW, scale=3, shadow=PURPLE,
                  wave_t=t if t > S4_APPROX + 0.5 else None)
    S4_T1.draw(img, t)
    S4_T2.draw(img, t)


# 5 ─ la Terre -----------------------------------------------------------
_er = np.random.RandomState(3)
_land = _er.rand(16, 32)
_land = np.kron(_land, np.ones((4, 4)))
for _ in range(6):
    _land = (_land + np.roll(_land, 1, 0) + np.roll(_land, -1, 0) +
             np.roll(_land, 1, 1) + np.roll(_land, -1, 1)) / 5
LAND = _land > np.percentile(_land, 62)
ER = 30
_ey, _ex = np.mgrid[-ER:ER + 1, -ER:ER + 1]
_inside = _ex ** 2 + _ey ** 2 <= ER ** 2
_z = np.sqrt(np.clip(1 - (_ex / ER) ** 2 - (_ey / ER) ** 2, 0, 1))
_lon0 = np.arctan2(_ex / ER, _z)
_lat = np.arcsin(np.clip(_ey / ER, -1, 1))
_light = (_ex * -0.5 + _ey * -0.4) / ER + _z * 0.8


def earth(t):
    lon = (_lon0 + t * 0.6) % (2 * math.pi)
    li = ((_lat / math.pi + 0.5) * (LAND.shape[0] - 1)).astype(int)
    lj = (lon / (2 * math.pi) * (LAND.shape[1] - 1)).astype(int)
    land = LAND[li, lj]
    th = _light + BAYER[(_ey + ER) % 4, (_ex + ER) % 4] * 0.35
    bright = th > 0.55
    out = np.zeros(_ex.shape + (4,), np.uint8)
    ocean = np.where(bright[..., None], np.array(BLUE), np.array(NAVY))
    ground = np.where(bright[..., None], np.array(GREEN), np.array(DGREEN))
    polar = np.abs(_lat) > 1.2
    col = np.where(land[..., None], ground, ocean)
    col = np.where(polar[..., None], np.array(WHITE if True else LGREY), col)
    out[..., :3] = col
    out[..., 3] = _inside * 255
    ring = (_ex ** 2 + _ey ** 2 > (ER - 1) ** 2) & _inside
    out[ring] = (*BLUE, 255)
    return Image.fromarray(out, 'RGBA')


S5_T1 = T("C'EST PLUS QUE LE NOMBRE D'*ATOMES* QUI COMPOSENT LA TERRE ENTIÈRE ! (~10^50)",
          S5 + 0.8, 150)
S5_T2 = T("52 ! EST *600 MILLIONS DE MILLIARDS DE FOIS* PLUS GRAND.", after(S5_T1), 202)
S6 = after(S5_T2)
SFX.append((S5 + 0.1, 'whoosh', None))
SFX.append((S5_T2.t0, 'coin', None))
ATOMS = [(random.Random(i).random() * 6.28, 36 + i % 5 * 3, 0.8 + (i % 7) * 0.25) for i in range(28)]


@scene(S5, S6)
def s5(img, t):
    lt = t - S5
    cy = 82 + int(math.sin(lt * 2) * 2)
    p = ease_out_back(lt / 0.6)
    for i, (ph, r, sp) in enumerate(ATOMS):
        a = ph + lt * sp
        x, y = 90 + math.cos(a) * r * p, cy + math.sin(a) * r * 0.45 * p
        if math.sin(a) < 0:
            img.putpixel((int(x), int(y)), PINK if i % 2 else YELLOW)
    e = earth(lt)
    if p > 0.05:
        if p < 0.999:
            e = e.resize((max(1, int(e.width * p)), max(1, int(e.height * p))), Image.NEAREST)
        img.paste(e, (90 - e.width // 2, cy - e.height // 2), e)
    for i, (ph, r, sp) in enumerate(ATOMS):
        a = ph + lt * sp
        x, y = 90 + math.cos(a) * r * p, cy + math.sin(a) * r * 0.45 * p
        if math.sin(a) >= 0:
            img.putpixel((int(x), int(y)), PINK if i % 2 else YELLOW)
    S5_T1.draw(img, t)
    S5_T2.draw(img, t)


# 6 ─ depuis le big bang -------------------------------------------------
BB_T = S6 + 0.4
impact(BB_T, 3)
S6_T1 = T("IMAGINE : *8 MILLIARDS* D'HUMAINS QUI MÉLANGENT 1 PAQUET CHAQUE SECONDE DEPUIS LE *BIG BANG*...",
          BB_T + 1.6, 132)
S6_T2 = T("... ILS N'AURAIENT MÊME PAS TESTÉ *1 ORDRE SUR 10^40* !", after(S6_T1), 198)
SFX.append((S6_T2.t0, 'whoosh', None))
S7 = after(S6_T2, 0.5)
_pr = random.Random(11)
PARTS = [(_pr.random() * 6.28, 20 + _pr.random() * 40, _pr.choice([YELLOW, ORANGE, RED, WHITE, PINK]))
         for _ in range(90)]
PEOPLE = [(_pr.choice([PEACH, BROWN, (120, 70, 40), (230, 170, 120)]),
           _pr.choice([RED, BLUE, GREEN, ORANGE, PINK, LAVENDER, YELLOW]), _pr.random() * 6)
          for _ in range(3 * 22)]


@scene(S6, S7)
def s6(img, t):
    lt = t - BB_T
    if lt >= 0:
        px = img.load()
        for a, sp, col in PARTS:
            d = sp * (1 - math.exp(-lt * 1.5))
            x = 90 + math.cos(a) * d * 1.3
            y = 50 + math.sin(a) * d * 0.6
            if 0 <= x < W and 0 <= y < H:
                px[int(x), int(y)] = col
        r = int(10 * math.exp(-lt * 2))
        if r > 0:
            img.paste(WHITE, (90 - r, 50 - r, 90 + r, 50 + r))
        if lt > 0.5:
            draw_text(img, "BIG BANG", 90, 20, ORANGE, maxw=170)
            draw_text(img, "IL Y A 13,8 MILLIARDS D'ANNÉES", 90, 72, LGREY, maxw=170)
    # foule de petits humains qui mélangent
    if t > S6_T1.t0:
        n = min(len(PEOPLE), int((t - S6_T1.t0) * 40))
        for i, (skin, shirt, ph) in enumerate(PEOPLE[:n]):
            row, col = divmod(i, 22)
            x = 14 + col * 7 + (row % 2) * 3
            y = 92 + row * 11
            img.paste(skin, (x + 1, y, x + 3, y + 2))
            img.paste(shirt, (x, y + 2, x + 4, y + 6))
            img.paste(INK, (x + 1, y + 6, x + 3, y + 8))
            flick = int(t * 12 + ph) % 2
            img.paste(WHITE if flick else RED, (x + 4, y + 2 - flick, x + 6, y + 5 - flick))
    S6_T1.draw(img, t)
    S6_T2.draw(img, t)


# 7 ─ bonus 7 mélanges + UNIQUE ------------------------------------------
S7_T1 = T("BONUS : IL SUFFIT DE *7 MÉLANGES À L'AMÉRICAINE* POUR BIEN MÉLANGER UN PAQUET.", S7 + 0.3, 28)
RIFFLE0 = S7_T1.end() + 1.0
RIFFLE_DT = 0.5
for k in range(7):
    SFX.append((RIFFLE0 + k * RIFFLE_DT, 'riffle', k))
S7_T2 = T("DONC TON MÉLANGE EST SÛREMENT...", max(after(S7_T1), RIFFLE0 + 7 * RIFFLE_DT + 0.6), 186)
UNIQUE_T = S7_T2.end() + 0.7
impact(UNIQUE_T, 4)
SFX.append((UNIQUE_T + 0.05, 'sparkle', None))


S7_END = UNIQUE_T + 3.0


@scene(S7, S7_END)
def s7(img, t):
    S7_T1.draw(img, t)
    if t >= S7_T1.t0:
        k = int((t - RIFFLE0) / RIFFLE_DT) if t >= RIFFLE0 else -1
        ph = ((t - RIFFLE0) / RIFFLE_DT) % 1 if 0 <= k < 7 else 0
        merge = math.sin(ph * math.pi)
        for side in (-1, 1):
            for j in range(6):
                x = 90 + side * (30 - 22 * merge)
                y = 125 - j * 1.5 + (j % 2) * merge * 3 * side
                paste_sprite(img, BACK, x, y, side * 8 * merge)
        if k >= 0:
            kk = min(k + 1, 7)
            draw_text(img, f"× {kk}", 90, 150, GREEN if kk == 7 else WHITE, scale=2)
    S7_T2.draw(img, t)
    if t >= UNIQUE_T:
        p = ease_out_back((t - UNIQUE_T) / 0.35)
        sc = 3 if p > 0.6 else 2
        draw_text(img, "UNIQUE !", 90, 218 + (3 - sc) * 6, scale=sc, wave_t=t, rainbow=True,
                  shadow=PURPLE)
        lt = t - UNIQUE_T
        px = img.load()
        for i in range(24):
            a = i * 0.785 + lt * 0.5
            d = 40 + lt * 30 + (i % 3) * 8
            x, y = 90 + math.cos(a) * d, 236 + math.sin(a) * d * 0.5
            if 0 <= x < W and 0 <= y < H and (int(lt * 10) + i) % 3:
                px[int(x), int(y)] = RAINBOW[i % 6]


# 8 ─ appel à l'action ---------------------------------------------------
HEART = SUIT7['H']
S8 = S7_END
DUR = S8 + 5.5
SFX.append((S8 + 0.1, 'coin', None))
S8_T = T("ABONNE-TOI POUR PLUS D'ANECDOTES DE MATHS !", S8 + 0.5, 168, cps=30)
RAIN = [(random.Random(i).randrange(-10, W + 10), random.Random(i + 99).random() * 400,
         20 + (i % 5) * 12, DECK[(i * 17) % 52]) for i in range(14)]


@scene(S8, DUR)
def s8(img, t):
    lt = t - S8
    for x, y0, sp, c in RAIN:
        y = (y0 + lt * sp) % 380 - 30
        paste_sprite(img, CARDS[c], x, y, (x % 40) - 20)
    beat = 1 + 0.25 * max(0, math.cos(lt * math.pi * 4)) ** 8
    sc = int(round(6 * beat * ease_out_back(lt / 0.5)))
    if sc > 0:
        m = mask_img(rows_to_mask(HEART), sc)
        img.paste(SHADOW, (90 - m.width // 2 + 2, 110 - m.height // 2 + 2), m)
        img.paste(RED, (90 - m.width // 2, 110 - m.height // 2), m)
    if t >= S8_T.t0:
        img.paste(SHADOW, (8, 162, 172, 196))
    S8_T.draw(img, t)
    if t > S8 + 1.5:
        img.paste(RED, (52, 205, 128, 222))
        img.paste(PINK, (52, 205, 128, 207))
        draw_text(img, "+ SUIVRE", 90, 205, WHITE, shadow=PURPLE)


# ---------------------------------------------------------------- transitions
BOUNDS = [s[0] for s in SCENES[1:]]
for b in BOUNDS:
    SFX.append((b - 0.15, 'whoosh', None))


def wipe(img, t):
    for b in BOUNDS + [DUR + 0.15]:
        d = t - b
        if -0.15 <= d <= 0.15:
            p = 1 - abs(d) / 0.15
            for by in range(16):
                for bx in range(9):
                    if (bx + by) / 23 < p * 1.05 - (0.05 if d > 0 else 0):
                        img.paste(SHADOW, (bx * 20, by * 20, bx * 20 + 20, by * 20 + 20))


def shake_offset(t, f):
    amp = 0
    for t0, a in SHAKES:
        if 0 <= t - t0 < 0.4:
            amp = max(amp, a * (1 - (t - t0) / 0.4))
    if amp < 0.5:
        return 0, 0
    r = random.Random(f)
    a = int(round(amp))
    return r.randint(-a, a), r.randint(-a, a)


def render_frame(f):
    t = f / FPS
    img = BG.copy()
    draw_stars(img, t)
    for t0, t1, fn in SCENES:
        if t0 <= t < t1:
            fn(img, t)
            break
    dx, dy = shake_offset(t, f)
    if dx or dy:
        moved = BG.copy()
        moved.paste(img, (dx, dy))
        img = moved
    wipe(img, t)
    if t > DUR - 0.6:
        k = clamp((DUR - t) / 0.6)
        img = Image.eval(img, lambda v: int(v * k))
    return img


# ================================================================ AUDIO
def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, decay):
    return np.exp(-np.arange(n) / SR * decay)


def sq(freq, dur, duty=0.5):
    tt = np.arange(int(dur * SR)) / SR
    return np.where((tt * freq) % 1 < duty, 1.0, -1.0)


def tri(freq, dur):
    tt = np.arange(int(dur * SR)) / SR
    return 2 * np.abs(2 * ((tt * freq) % 1) - 1) - 1


def add(buf, t, sig, vol):
    i = int(t * SR)
    if i >= len(buf) or i < 0:
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * vol


def make_audio():
    n = int(DUR * SR)
    music = np.zeros(n)
    sfx = np.zeros(n)
    nr = np.random.RandomState(1)
    step = 0.125  # double-croche à 120 BPM
    chords = [[69, 72, 76, 81], [65, 69, 72, 77], [67, 72, 76, 79], [67, 71, 74, 79]]
    roots = [45, 41, 48, 43]
    pattern = [0, 1, 2, 3, 2, 1, 0, 1, 0, 2, 3, 2, 1, 2, 3, 2]
    nsteps = int(DUR / step)
    for s in range(nsteps):
        t = s * step
        bar = (s // 16) % 4
        st = s % 16
        tone = chords[bar][pattern[st]]
        intro = t < 1.0
        if not intro:
            add(music, t, sq(midi(tone), step, 0.25) * env(int(step * SR), 14), 0.10)
            if t > S7:
                add(music, t, sq(midi(tone + 12), step, 0.125) * env(int(step * SR), 20), 0.05)
        if st % 2 == 0:
            r = roots[bar] + (12 if st % 4 == 2 else 0)
            add(music, t, tri(midi(r), step * 2) * env(int(step * 2 * SR), 4), 0.32)
        if st in (0, 8, 10) and not intro:
            ln = int(0.18 * SR)
            ph = np.cumsum(np.linspace(140, 40, ln)) / SR
            add(music, t, np.sin(2 * np.pi * ph) * env(ln, 18), 0.55)
        if st in (4, 12) and not intro:
            ln = int(0.15 * SR)
            add(music, t, nr.uniform(-1, 1, ln) * env(ln, 22), 0.16)
        if st % 2 == 0 and not intro:
            ln = int(0.04 * SR)
            no = nr.uniform(-1, 1, ln)
            add(music, t, np.diff(no, prepend=0) * env(ln, 70), 0.05)

    for t, kind, p in SFX:
        if kind == 'blip':
            f = 900 + nr.randint(0, 5) * 80
            ln = int(0.035 * SR)
            add(sfx, t, sq(f, 0.035) * env(ln, 60), 0.13)
        elif kind == 'place':
            f = 330 * 2 ** (p / 26)
            ln = int(0.05 * SR)
            add(sfx, t, sq(f, 0.05, 0.25) * env(ln, 45), 0.14)
        elif kind == 'impact':
            ln = int(0.4 * SR)
            ph = np.cumsum(np.linspace(180, 35, ln)) / SR
            add(sfx, t, np.sin(2 * np.pi * ph) * env(ln, 7), 0.7)
            add(sfx, t, nr.uniform(-1, 1, ln) * env(ln, 14), 0.22)
        elif kind == 'crash':
            ln = int(1.0 * SR)
            no = nr.uniform(-1, 1, ln)
            add(sfx, t, np.diff(no, prepend=0) * env(ln, 4), 0.15)
        elif kind == 'whoosh':
            ln = int(0.3 * SR)
            no = nr.uniform(-1, 1, ln)
            k = 30
            no = np.convolve(no, np.ones(k) / k, mode='same') * 4
            e = np.sin(np.linspace(0, np.pi, ln)) ** 2
            add(sfx, t, no * e, 0.22)
        elif kind == 'coin':
            add(sfx, t, sq(988, 0.07) * env(int(0.07 * SR), 10), 0.12)
            add(sfx, t + 0.07, sq(1319, 0.3) * env(int(0.3 * SR), 9), 0.12)
        elif kind == 'riffle':
            ln = int(0.25 * SR)
            no = nr.uniform(-1, 1, ln)
            clicks = (np.arange(ln) % int(SR / 90) < 40).astype(float)
            add(sfx, t, no * clicks * env(ln, 6), 0.25)
            add(sfx, t + 0.2, sq(523 * 2 ** (p / 12), 0.06) * env(int(0.06 * SR), 30), 0.1)
        elif kind == 'sparkle':
            for j, m in enumerate([81, 84, 88, 93, 96, 100]):
                add(sfx, t + j * 0.05, sq(midi(m), 0.12, 0.25) * env(int(0.12 * SR), 25), 0.08)

    fade = np.ones(n)
    fl = int(1.5 * SR)
    fade[-fl:] = np.linspace(1, 0, fl)
    mix = music * fade + sfx
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    return (mix * 32767).astype(np.int16)


def write_wav(path, data):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ================================================================ MAIN
def main():
    out = os.path.join(HERE, '52_cartes_tiktok.mp4')
    wav = os.path.join(HERE, '_audio.wav')
    write_wav(wav, make_audio())
    nframes = int(DUR * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * S}x{H * S}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest',
           '-movflags', '+faststart', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        img = render_frame(f).resize((W * S, H * S), Image.NEAREST)
        proc.stdin.write(img.tobytes())
        if f % 150 == 0:
            print(f'frame {f}/{nframes}', flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print('->', out)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        # python3 make_video.py preview 3.0 12.5 ... -> PNG de contrôle
        for ts in sys.argv[2:]:
            render_frame(int(float(ts) * FPS)).resize((W * 3, H * 3), Image.NEAREST).save(
                os.path.join(HERE, f'_preview_{ts}.png'))
    else:
        main()
