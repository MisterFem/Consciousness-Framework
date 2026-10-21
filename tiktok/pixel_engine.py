"""Moteur commun des vidéos TikTok pixel art (police bitmap, textes machine à
écrire, fond étoilé, transitions, musique chiptune, narration, encodage).

Rendu interne 180x320, agrandi x6 -> 1080x1920. Un script de vidéo importe ce
module, déclare ses scènes avec @scene(t0, t1) puis appelle render_video().
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

W, H, S, FPS = 180, 320, 6, 30
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



# ================================================================ NARRATION
class Narration:
    """Cale la vidéo sur une voix off.

    `phrases` donne (début, fin) de chaque phrase dans le fichier audio. On
    insère des pauses (`gaps` = [(t_voix, durée)]) pour laisser lire ; V()
    convertit un temps de la voix en temps vidéo.
    """

    def __init__(self, path, phrases, gaps, end):
        self.path, self.P, self.gaps, self.end = path, phrases, gaps, end

    def V(self, tv):
        return tv + sum(g for c, g in self.gaps if c <= tv)

    def B(self, c):
        """Frontière de scène : au milieu de la pause insérée à c."""
        return self.V(c) - dict(self.gaps)[c] / 2

    def start(self, pid):
        return self.V(self.P[pid][0])

    def stop(self, pid):
        return self.V(self.P[pid][1])

    def text(self, text, pid, y, until=None, **kw):
        """Texte tapé pendant que la voix dit la phrase `pid` (jusqu'à `until`)."""
        t0 = self.start(pid)
        cps = clamp(len(text) / max(0.3, self.stop(until or pid) - t0), 12, 45)
        return T(text, t0, y, cps=cps, **kw)

    def load(self, n):
        out = np.zeros(n)
        if not self.path or not os.path.exists(self.path):
            return out
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', self.path, '-f', 's16le', '-ac', '1',
                              '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        src = np.frombuffer(raw, np.int16).astype(float) / 32768
        src /= np.abs(src).max()
        cuts = [0.0] + [c for c, _ in self.gaps] + [len(src) / SR]
        for a, b in zip(cuts, cuts[1:]):
            add(out, self.V(a), src[int(a * SR):int(b * SR)], 0.5)
        return out


# ================================================================ RENDU
def wipe(img, t, bounds):
    for b in bounds:
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


def render_frame(f, dur, loop=False):
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
    wipe(img, t, [s[0] for s in SCENES[1:]] + ([] if loop else [dur + 0.15]))
    if t > dur - 0.6 and not loop:
        k = clamp((dur - t) / 0.6)
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


# Musique par défaut : La mineur, Am F C G, 120 BPM
MUSIC = dict(bpm=120,
             chords=[[69, 72, 76, 81], [65, 69, 72, 77], [67, 72, 76, 79], [67, 71, 74, 79]],
             roots=[45, 41, 48, 43], climax=None)


def make_music(n, dur, nr, bpm, chords, roots, climax):
    music = np.zeros(n)
    step = 60 / bpm / 4  # double-croche
    pattern = [0, 1, 2, 3, 2, 1, 0, 1, 0, 2, 3, 2, 1, 2, 3, 2]
    for s in range(int(dur / step)):
        t = s * step
        bar = (s // 16) % len(chords)
        st = s % 16
        tone = chords[bar][pattern[st]]
        intro = t < 1.0
        if not intro:
            add(music, t, sq(midi(tone), step, 0.25) * env(int(step * SR), 14), 0.10)
            if climax is not None and t > climax:
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
    return music


def make_sfx(n, nr):
    sfx = np.zeros(n)
    for t, kind, p in SFX:
        if kind == 'blip':
            f = 900 + nr.randint(0, 5) * 80
            ln = int(0.035 * SR)
            add(sfx, t, sq(f, 0.035) * env(ln, 60), 0.035)
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
        elif kind == 'melody':
            # p = [(midi, durée en temps)], tempo fixe 0.3 s par temps
            tt = t
            for m, d in p:
                ln = d * 0.3
                add(sfx, tt, sq(midi(m), ln * 0.9, 0.5) * env(int(ln * 0.9 * SR), 3), 0.06)
                tt += ln
    return sfx


def make_audio(dur, narration=None, music=None, loop=False):
    n = int(dur * SR)
    nr = np.random.RandomState(1)
    mus = make_music(n, dur, nr, **{**MUSIC, **(music or {})})
    sfx = make_sfx(n, nr)
    voice = narration.load(n) if narration else np.zeros(n)
    if np.abs(voice).max() > 0:
        # ducking : la musique baisse quand la voix parle
        k = int(0.25 * SR)
        lvl = np.convolve(np.abs(voice), np.ones(k) / k, mode='same')
        duck = 1 - 0.6 * np.clip(lvl / (lvl.max() * 0.15 + 1e-9), 0, 1)
        gain = 0.55
    else:
        duck, gain = 1.0, 1.0
    fade = np.ones(n)
    fl = int((0.25 if loop else 1.5) * SR)
    fade[-fl:] = np.linspace(1, 0, fl)
    mix = mus * duck * fade * gain + sfx * 0.7 + voice * 1.9
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    return (mix * 32767).astype(np.int16)


def write_wav(path, data):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ================================================================ MAIN
def render_video(out, dur, narration=None, music=None, loop=False):
    """`python3 script.py` -> mp4 ; `python3 script.py preview 3 12.5` -> PNG.

    loop=True : pas de fondu final, pour que la vidéo s'enchaîne sur son début.
    """
    here = os.path.dirname(os.path.abspath(out))
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            render_frame(int(float(ts) * FPS), dur, loop).resize((W * 3, H * 3), Image.NEAREST).save(
                os.path.join(here, f'_preview_{ts}.png'))
        return
    for t0, _, _ in SCENES[1:]:
        SFX.append((t0 - 0.15, 'whoosh', None))
    wav = os.path.join(here, '_audio.wav')
    write_wav(wav, make_audio(dur, narration, music, loop))
    nframes = int(dur * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * S}x{H * S}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '44100',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        img = render_frame(f, dur, loop).resize((W * S, H * S), Image.NEAREST)
        proc.stdin.write(img.tobytes())
        if f % 300 == 0:
            print(f'frame {f}/{nframes}', flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print('->', out)
