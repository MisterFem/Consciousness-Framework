"""Série « Utopiste ? » : direction artistique et éléments communs aux 3 épisodes.

Même âme que le compte (pixel art, police maison, chiptune) avec un habillage
propre à la série : fond « plan d'ingénieur » (on parle de mécanismes), tampon
UTOPISTE ? qui devient MÉCANISME ✓, le Sceptique qui porte les objections, et
un bandeau ÉP. n/3.
"""
import math
import os
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 84          # centre des textes, décalé à gauche des boutons TikTok
TOP = 48         # sous la barre de recherche TikTok
MAXW = 144       # TikTok rogne les côtés sur les écrans allongés

PAPER = (16, 34, 74)
GRID = (28, 54, 104)
GRID2 = (40, 72, 130)
CYAN = (120, 200, 255)
STAMP_RED = (230, 40, 60)


# ---------------------------------------------------------------- fond
def make_blueprint():
    yy, xx = np.mgrid[0:H, 0:W]
    a = np.zeros((H, W, 3), np.uint8)
    a[:] = PAPER
    # vignette tramée vers les bords
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    dark = d + BAYER[yy % 4, xx % 4] * 0.25 > 1.05
    a[dark] = (10, 22, 52)
    a[(yy % 10 == 0) | (xx % 10 == 0)] = GRID
    a[(yy % 50 == 0) | (xx % 50 == 0)] = GRID2
    return Image.fromarray(a, 'RGB')


def blueprint_anim(img, t):
    # une ligne de balayage lente, comme un écran de contrôle
    y = int((t * 40) % (H + 40)) - 20
    for k in range(3):
        if 0 <= y + k < H:
            row = img.crop((0, y + k, W, y + k + 1))
            img.paste(Image.eval(row, lambda v: min(255, v + 18 - k * 6)), (0, y + k))


set_backdrop(make_blueprint(), blueprint_anim)


# ---------------------------------------------------------------- narration
class Episode:
    """Calage d'un épisode sur sa voix off (ou sur une durée estimée)."""

    def __init__(self, lines, scene_starts, inner_gaps, measured, audio, rate=17.0, tail=1.2):
        self.lines, self.txt = lines, dict(lines)
        self.ids = [pid for pid, _ in lines]
        ph = measured or self._estimate(rate)
        self.ph = ph
        self.cut, gaps = {}, []
        for pid, g in {**scene_starts, **inner_gaps}.items():
            prev = self.ids[self.ids.index(pid) - 1]
            self.cut[pid] = (ph[prev][1] + ph[pid][0]) / 2
            gaps.append((self.cut[pid], g))
        gaps.sort()
        end = ph[self.ids[-1]][1] + 0.1
        self.N = Narration(audio, ph, gaps, end)
        self.dur = self.N.V(end) + tail

    def _estimate(self, rate, pause=0.3):
        out, t = {}, 0.05
        for pid, txt in self.lines:
            d = len(txt) / rate
            out[pid] = (t, t + d)
            t += d + pause
        return out

    def sb(self, pid):
        """Début de la scène qui s'ouvre sur la phrase pid."""
        return self.N.B(self.cut[pid])

    def start(self, pid):
        return self.N.start(pid)

    def stop(self, pid):
        return self.N.stop(pid)

    def at(self, pid, words):
        """Moment (vidéo) où la voix prononce `words` dans la phrase pid."""
        a, b = self.ph[pid]
        i = self.txt[pid].index(words)
        return self.N.V(a + (b - a) * i / len(self.txt[pid]))

    def write_text(self, path):
        with open(path, 'w') as f:
            f.write('\n\n'.join(t for _, t in self.lines) + '\n')


# ---------------------------------------------------------------- outils
def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def big_sprite(img, spr, cx, cy, scale, flip=False):
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    if flip:
        s = s.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


def pop(t, t0, dur=0.35):
    return ease_out_back((t - t0) / dur)


def box(img, y0, y1, x0=14, x1=156):
    img.paste(SHADOW, (x0, y0, x1, y1))


def text_w(txt, maxw=140):
    return max(w for _, w in layout(txt, maxw))


def caption(img, t, tx, y=206):
    """Sous-titre dans un cartouche sombre."""
    if t >= tx.t0:
        box(img, y - 3, y + 33)
        tx.draw(img, t, CX)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def burst(img, t, t0, cx, cy, n=24):
    lt = t - t0
    if lt < 0 or lt > 1.5:
        return
    px = img.load()
    for i in range(n):
        a = i * 6.283 / n
        d = 10 + lt * 50
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6
        if 0 <= x < W and 0 <= y < H:
            px[int(x), int(y)] = RAINBOW[i % 6]


def checklist(img, t, items, y0, dy=26):
    """Mesures qui se cochent : [(temps, texte)]."""
    for k, (ti, txt) in enumerate(items):
        if t < ti:
            continue
        y = y0 + k * dy
        p = clamp((t - ti) / 0.25)
        x = 18 + int((1 - p) * -20)
        img.paste(WHITE, (x, y + 2, x + 9, y + 11))
        img.paste(INK, (x + 1, y + 3, x + 8, y + 10))
        if t >= ti + 0.15:
            stamp(img, FONT['✓'], x + 2, y + 3, GREEN)
        draw_text(img, txt, x + 13 + text_w(txt, 126) // 2, y + 1, WHITE, maxw=126)


# ---------------------------------------------------------------- habillage
def episode_tag(img, num, t):
    """Bandeau ÉP. n/3 + segments de progression de la série."""
    draw_text(img, f"UTOPISTE ? · ÉP. {num}/3", CX, TOP - 10, CYAN, maxw=MAXW)
    for k in range(3):
        col = YELLOW if k + 1 == num else (GRID2 if k + 1 > num else CYAN)
        img.paste(col, (CX - 33 + k * 23, TOP + 2, CX - 13 + k * 23, TOP + 4))


def rubber_stamp(img, text, cx, cy, t, t0, col=STAMP_RED, scale=2, angle=-8):
    """Tampon qui s'écrase sur l'écran."""
    if t < t0:
        return
    p = clamp((t - t0) / 0.18)
    sc = scale if p >= 1 else scale + 1
    w = text_w(text, 300) * sc + 10 * sc // 2
    h = 12 * sc + 6
    layer = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([2, 2, w + 5, h + 5], outline=col + (255,), width=2)
    tmp = Image.new('RGB', (w + 8, h + 8), (0, 0, 0))
    draw_text(tmp, text, (w + 8) // 2, 5, (255, 255, 255), scale=sc, maxw=600, shadow=None)
    mask = tmp.convert('L').point(lambda v: 255 if v > 128 else 0)
    layer.paste(col + (255,), (0, 0), mask)
    # usure du tampon : quelques pixels manquants
    px = layer.load()
    for i in range(0, layer.width * layer.height, 7):
        x, y = i % layer.width, (i * 13) // layer.width % layer.height
        if (x * 7 + y * 3) % 11 == 0:
            px[x, y] = (0, 0, 0, 0)
    layer = layer.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)


SCEPTIC = art([
    "...hhhh...",
    "..hhhhhh..",
    "..ssssss..",
    "..sksskss.",
    "..ssssss..",
    "..s.mm.s..",
    "...ssss...",
    ".cccccccc.",
    "cccccccccc",
    "csssssssc.",
    "cccccccccc",
    ".cccccccc.",
    ".cccccccc.",
    "..pp..pp..",
    "..pp..pp..",
    ".kkk..kkk.",
], {'h': (90, 60, 30), 's': PEACH, 'k': INK, 'm': (150, 60, 60), 'c': (120, 120, 140),
    'p': (50, 50, 80)})


def sceptic(img, t, t0, text, y=150, side='right'):
    """Le Sceptique, bras croisés, et sa bulle d'objection."""
    if t < t0:
        return
    p = pop(t, t0, 0.3)
    x = 138 if side == 'right' else 30
    yy = int(y + (1 - p) * 30 + math.sin(t * 3) * 1)
    big_sprite(img, SCEPTIC, x, yy, 3, flip=side == 'left')
    bw = min(MAXW, text_w(text, 120) + 12)
    bx = CX - bw // 2 - (12 if side == 'right' else -12)
    lines = len(layout(text.upper(), 120))
    bh = lines * 12 + 8
    by = yy - 24 - bh - 10
    img.paste(SHADOW, (bx + 2, by + 2, bx + bw + 2, by + bh + 2))
    img.paste(WHITE, (bx, by, bx + bw, by + bh))
    tail_x = x - 14 if side == 'right' else x + 14
    for k in range(6):
        img.paste(WHITE, (tail_x - k // 2, by + bh + k, tail_x + 3 - k // 2, by + bh + k + 1))
    draw_text(img, text, bx + bw // 2, by + 4, INK, maxw=120, shadow=None, hl_color=STAMP_RED)
    draw_text(img, "LE SCEPTIQUE", x, yy + 26, LGREY)


def quote_card(img, t, t0, text, author, source, y=70):
    """Citation réelle : guillemets pixel, texte, auteur et source. Renvoie le bas de la carte."""
    if t < t0:
        return y
    p = pop(t, t0, 0.4)
    yy = int(y + (1 - p) * 12)
    nq, na, ns = (len(layout(s_.upper(), 128)) for s_ in (text, "— " + author, source))
    h = 14 + nq * 12 + 6 + (na + ns) * 12 + 4
    img.paste(SHADOW, (16, yy + 3, 159, yy + h + 3))
    img.paste((235, 228, 210), (14, yy, 156, yy + h))
    img.paste(STAMP_RED, (14, yy, 18, yy + h))
    draw_text(img, "«", 26, yy, STAMP_RED, shadow=None)
    draw_text(img, text, CX + 2, yy + 12, INK, maxw=128, shadow=None, hl_color=STAMP_RED)
    ya = yy + 14 + nq * 12 + 4
    draw_text(img, "— " + author, CX + 2, ya, (60, 60, 90), maxw=128, shadow=None)
    draw_text(img, source, CX + 2, ya + na * 12, (110, 110, 130), maxw=128, shadow=None)
    return yy + h


def verdict(img, t, t_stamp, t_fix):
    """Fin d'épisode : UTOPISTE ? tamponné, puis barré et remplacé par MÉCANISME ✓."""
    rubber_stamp(img, "UTOPISTE ?", CX, 110, t, t_stamp)
    if t >= t_fix:
        p = clamp((t - t_fix) / 0.3)
        d = ImageDraw.Draw(img)
        d.line([(30, 124), (30 + 110 * p, 96)], fill=WHITE, width=3)
        if p >= 1:
            rubber_stamp(img, "MÉCANISME ✓", CX, 150, t, t_fix + 0.35, col=GREEN, angle=5)


def render(ep, name, music):
    render_video(os.path.join(HERE, name), ep.dur, ep.N, loop=False, music=music)


MUSIC_SERIE = dict(bpm=104,
                   chords=[[62, 65, 69, 74], [58, 62, 65, 70], [60, 64, 67, 72], [57, 61, 64, 69]],
                   roots=[38, 34, 36, 33], climax=None)
