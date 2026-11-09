"""« La Plume et le Crayon » — fable en court-métrage (DA « livre illustré » 360x640, x3).

Découpage en ~40 plans (macro, contre-plongée, plan large, champ / contrechamp,
vue subjective à travers le monocle...), 10 décors, éclairage par moment de la
journée (soir, nuit + lampe, lune, aube), profondeur de champ, raccords
« tache d'encre ». Bruitages synthétisés ici ; voix : audio/narration.wav
(assemblée par build_voice.py à partir de narrateur / plume / crayon).

    python3 make_video.py preview 1.5 12 30   -> _preview_*.png
    python3 make_video.py                     -> plume_crayon_tiktok.mp4
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pixel_engine import draw_text, layout  # noqa: E402

W, H, S, FPS, SR = 360, 640, 3, 30, 44100
CX = W // 2
TOP = 100
SS = 2  # sur-échantillonnage des personnages

# ================================================================ texte & temps
BLOCKS = [ln.split('|', 1) for ln in open(os.path.join(HERE, 'script.txt'), encoding='utf-8').read().strip().split('\n')]
TXT = dict(BLOCKS)
IDS = [b[0] for b in BLOCKS]
_mj = os.path.join(HERE, 'measured.json')
MEASURED = {k: tuple(v) for k, v in __import__('json').load(open(_mj)).items()} if os.path.exists(_mj) else None


def estimate():
    ph, t = {}, 0.15
    for pid in IDS:
        rate = 15.5 if pid[0] == 'N' else 13.5
        d = len(TXT[pid]) / rate
        ph[pid] = (round(t, 2), round(t + d, 2))
        t += d + (0.55 if pid[0] != 'N' or pid == 'N1' else 0.45)
    return ph


PH = MEASURED or estimate()
DUR = PH[IDS[-1]][1] + 1.6


def at(pid, words=None, off=0.0):
    a, b = PH[pid]
    if words is None:
        return a + off
    i = TXT[pid].index(words)
    return a + (b - a) * i / len(TXT[pid]) + off


def end(pid, off=0.0):
    return PH[pid][1] + off


# ================================================================ utilitaires
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def eout(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def eback(u):
    u = clamp(u)
    c = 1.9
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def mixc(a, b, u):
    return tuple(int(a[k] + (b[k] - a[k]) * u) for k in range(3))


def arr(img):
    return np.asarray(img, dtype=np.float32)


def toimg(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB')


_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    pos = [p for p, _ in stops]
    out = np.zeros((h, w, 3), np.float32)
    for k in range(3):
        out[..., k] = np.interp(ys, pos, [c[k] for _, c in stops])[:, None]
    return out


def radial(w, h, cx, cy, rx, ry=None, power=2.0):
    ry = ry or rx
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip(1 - r, 0, 1) ** power


def poly_mask(w, h, pts, blur=0):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255


def capsule(d, p0, p1, r, fill):
    d.line([p0, p1], fill=fill, width=int(r * 2))
    for p in (p0, p1):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def blur(img, r):
    return img.filter(ImageFilter.GaussianBlur(r))


# ================================================================ personnages
# boîte locale 120 x 270 unités, pointe en (60, 266)
BW, BH, TIP = 120, 270, (60, 266)
MOODS = {
    #            paupière, sourcils (angle, hauteur), bouche
    'neutral': (0.12, 0, 0, 'flat'),
    'proud': (0.48, -6, 3, 'smirk'),
    'grumpy': (0.38, 12, -1, 'frown'),
    'suspicious': (0.58, 4, -2, 'side'),
    'smug': (0.5, -4, 2, 'smirk'),
    'happy': (0.0, -6, 3, 'smile_open'),
    'joy': (0.0, -8, 4, 'smile_open'),
    'shock': (0.0, -10, 6, 'o'),
    'sad': (0.28, -12, 1, 'frown_small'),
    'tender': (0.32, -9, 1, 'smile'),
    'ashamed': (0.3, -12, 0, 'wobble'),
    'worried': (0.12, -12, 3, 'wobble'),
    'resolved': (0.3, 6, 0, 'flat'),
}


def face(d, U, cx, cy, sep, rx, ry, mood='neutral', look=(0, 0), blink=False, talk=0.0, t=0.0, mono=False,
         brow_col=(70, 60, 70), blush=None):
    lid, bang, bh, mouth = MOODS[mood]
    lx, ly = look
    for side in (-1, 1):
        ex = cx + side * sep / 2
        if blink:
            d.line([U(ex - rx), U(cy + 1), U(ex + rx), U(cy + 1)], fill=(30, 25, 40), width=U(1.6))
        elif mood in ('happy', 'joy') and mood == 'happy':
            d.arc([U(ex - rx), U(cy - ry * 0.6), U(ex + rx), U(cy + ry * 1.1)], 200, 340, fill=(30, 25, 40),
                  width=U(2))
        else:
            d.ellipse([U(ex - rx), U(cy - ry), U(ex + rx), U(cy + ry)], fill=(255, 252, 245),
                      outline=(40, 30, 45), width=U(0.8))
            pr = rx * (0.42 if mood != 'shock' else 0.3)
            px, py = ex + lx * rx * 0.45, cy + ly * ry * 0.4 + (1.5 if lid > 0.3 else 0)
            d.ellipse([U(px - pr), U(py - pr * 1.1), U(px + pr), U(py + pr * 1.1)], fill=(35, 28, 45))
            d.ellipse([U(px - pr * 0.15 - pr * 0.4), U(py - pr * 0.8), U(px - pr * 0.15), U(py - pr * 0.4)],
                      fill=(255, 255, 255))
            if mood == 'joy':
                d.ellipse([U(px + pr * 0.2), U(py + pr * 0.2), U(px + pr * 0.5), U(py + pr * 0.5)], fill=(255, 255, 255))
        # sourcils
        a = math.radians(bang) * side
        by = cy - ry - 4.5 - bh
        if mood == 'proud' and side == 1:
            by -= 3
        x0, x1 = ex - rx * 0.9, ex + rx * 0.9
        y0 = by + math.sin(a) * rx * -0.9 * -1
        y1 = by - math.sin(a) * rx * 0.9 * -1
        if side == -1:
            y0, y1 = by - math.sin(-a) * rx * 0.9, by + math.sin(-a) * rx * 0.9
        d.line([U(x0), U(y0), U(x1), U(y1)], fill=brow_col, width=U(2.2))
    if mono:
        ex = cx + sep / 2
        d.ellipse([U(ex - rx - 3), U(cy - ry - 3), U(ex + rx + 3), U(cy + ry + 3)], outline=(235, 190, 80),
                  width=U(1.8))
        d.arc([U(ex - rx - 1), U(cy - ry - 1), U(ex + rx + 1), U(cy + ry + 1)], 200, 260, fill=(255, 245, 200),
              width=U(1.2))
    if blush:
        for side in (-1, 1):
            ex = cx + side * (sep / 2 + rx * 0.6)
            d.ellipse([U(ex - 4), U(cy + ry + 2), U(ex + 4), U(cy + ry + 6)], fill=blush)
    # bouche
    my = cy + ry + 13
    w = 6
    op = talk * (0.5 + 0.5 * abs(math.sin(t * 17))) if talk else 0
    col = (60, 25, 35)
    if op > 0.15:
        d.ellipse([U(cx - w * 0.8), U(my - 2), U(cx + w * 0.8), U(my - 1 + 7 * op)], fill=col)
        d.ellipse([U(cx - w * 0.4), U(my + 2 * op), U(cx + w * 0.4), U(my - 1 + 6 * op)], fill=(230, 110, 120))
    elif mouth == 'flat':
        d.line([U(cx - 4), U(my), U(cx + 4), U(my)], fill=col, width=U(1.6))
    elif mouth == 'side':
        d.line([U(cx - 2), U(my), U(cx + 6), U(my - 1)], fill=col, width=U(1.6))
    elif mouth == 'smirk':
        d.arc([U(cx - 6), U(my - 6), U(cx + 6), U(my + 2)], 20, 110, fill=col, width=U(1.8))
        d.line([U(cx - 5), U(my), U(cx + 1), U(my + 2)], fill=col, width=U(1.6))
    elif mouth == 'frown':
        d.arc([U(cx - 6), U(my), U(cx + 6), U(my + 8)], 200, 340, fill=col, width=U(1.8))
    elif mouth == 'frown_small':
        d.arc([U(cx - 4), U(my + 1), U(cx + 4), U(my + 6)], 200, 340, fill=col, width=U(1.6))
    elif mouth == 'smile':
        d.arc([U(cx - 6), U(my - 6), U(cx + 6), U(my + 3)], 20, 160, fill=col, width=U(1.8))
    elif mouth == 'smile_open':
        d.chord([U(cx - 7), U(my - 5), U(cx + 7), U(my + 7)], 0, 180, fill=col)
        d.chord([U(cx - 4), U(my + 1), U(cx + 4), U(my + 7)], 0, 180, fill=(230, 110, 120))
    elif mouth == 'o':
        d.ellipse([U(cx - 3.5), U(my - 3), U(cx + 3.5), U(my + 6)], fill=col)
    elif mouth == 'wobble':
        pts = [(U(cx - 6 + i * 2), U(my + 1 + (1.2 if i % 2 else -0.6))) for i in range(7)]
        d.line(pts, fill=col, width=U(1.5))


def lids(d, U, cx, cy, sep, rx, ry, mood, skin, blink):
    """Paupières supérieures (couleur de la peau du personnage)."""
    lid = MOODS[mood][0]
    if blink or lid <= 0 or mood in ('happy',):
        return
    for side in (-1, 1):
        ex = cx + side * sep / 2
        h = ry * 2 * lid
        d.chord([U(ex - rx - 0.8), U(cy - ry - 0.8), U(ex + rx + 0.8), U(cy - ry + h * 2)], 180, 360, fill=skin)
        d.arc([U(ex - rx - 0.8), U(cy - ry - 0.8), U(ex + rx + 0.8), U(cy - ry + h * 2)], 180, 360,
              fill=(40, 30, 45), width=U(0.9))


def plume_layer(s, mood='neutral', look=(0, 0), blink=False, talk=0.0, t=0.0, stain=0.0, mono=True, sweat=0.0):
    k = s * SS
    lay = Image.new('RGBA', (int(BW * k), int(BH * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    def U(v):
        return int(round(v * k))

    navy, hi, sh = (30, 40, 98), (66, 90, 170), (16, 20, 56)
    gold, goldh, golds = (232, 182, 70), (255, 230, 140), (170, 120, 40)
    d.ellipse([U(51), U(1), U(69), U(15)], fill=gold)
    d.rounded_rectangle([U(42), U(8), U(78), U(104)], radius=U(10), fill=navy)
    d.rectangle([U(46), U(16), U(51), U(98)], fill=hi)
    d.rectangle([U(70), U(16), U(76), U(98)], fill=sh)
    d.rectangle([U(70), U(16), U(83), U(24)], fill=gold)
    d.rectangle([U(77), U(18), U(83), U(84)], fill=gold)
    d.rectangle([U(77), U(18), U(79), U(84)], fill=goldh)
    d.ellipse([U(75), U(80), U(85), U(92)], fill=gold)
    d.rectangle([U(40), U(98), U(80), U(109)], fill=gold)
    d.rectangle([U(40), U(98), U(80), U(100)], fill=goldh)
    d.line([U(40), U(105), U(80), U(105)], fill=golds, width=U(1))
    d.rectangle([U(43), U(109), U(77), U(206)], fill=navy)
    d.rectangle([U(46), U(112), U(51), U(203)], fill=hi)
    d.rectangle([U(70), U(112), U(76), U(203)], fill=sh)
    d.rectangle([U(43), U(196), U(77), U(201)], fill=gold)
    d.polygon([(U(44), U(206)), (U(76), U(206)), (U(71), U(228)), (U(49), U(228))], fill=(22, 22, 30))
    d.polygon([(U(47), U(208)), (U(52), U(208)), (U(52), U(226)), (U(50), U(226))], fill=(60, 60, 75))
    d.polygon([(U(49), U(228)), (U(71), U(228)), (U(65), U(250)), (U(60), U(266)), (U(55), U(250))], fill=gold)
    d.polygon([(U(51), U(229)), (U(57), U(229)), (U(58), U(258)), (U(55), U(250))], fill=goldh)
    d.line([U(60), U(238), U(60), U(264)], fill=(90, 60, 20), width=U(1))
    d.ellipse([U(58), U(233), U(62), U(237)], fill=(90, 60, 20))
    # visage
    cx, cy = 60, 132
    face(d, U, cx, cy, 17, 6, 7, mood, look, blink, 0, t, mono=False, brow_col=(200, 200, 215))
    lids(d, U, cx, cy, 17, 6, 7, mood, navy, blink)
    # moustache
    for side in (-1, 1):
        pts = [(60, 147), (60 + side * 7, 145), (60 + side * 13, 148), (60 + side * 15, 144), (60 + side * 14, 151),
               (60 + side * 8, 151.5), (60, 150)]
        d.polygon([(U(x), U(y)) for x, y in pts], fill=(225, 225, 235))
    # bouche (sous la moustache)
    my = 155
    op = talk * (0.5 + 0.5 * abs(math.sin(t * 15))) if talk else 0
    m = MOODS[mood][3]
    col = (180, 70, 90)
    if op > 0.15:
        d.ellipse([U(56), U(my - 1), U(64), U(my + 6 * op + 1)], fill=(20, 10, 25))
    elif m in ('frown', 'frown_small', 'wobble'):
        d.arc([U(55), U(my), U(65), U(my + 6)], 200, 340, fill=col, width=U(1.5))
    elif m == 'o':
        d.ellipse([U(57), U(my - 1), U(63), U(my + 6)], fill=(20, 10, 25))
    elif m in ('smile', 'smile_open', 'smirk'):
        d.arc([U(55), U(my - 4), U(65), U(my + 2)], 20, 160, fill=col, width=U(1.5))
    if mono:
        ex, ey = cx + 8.5, cy
        d.ellipse([U(ex - 9), U(ey - 10), U(ex + 9), U(ey + 10)], outline=gold, width=U(1.8))
        d.arc([U(ex - 7), U(ey - 8), U(ex + 7), U(ey + 8)], 200, 250, fill=(255, 250, 220), width=U(1.2))
        d.line([U(ex + 8), U(ey + 5), U(82), U(150), U(80), U(91)], fill=golds, width=U(0.8))
    if stain > 0:
        r = 7 * stain
        d.ellipse([U(46 - r), U(140 - r * 0.8), U(46 + r), U(140 + r * 0.8)], fill=(8, 8, 18))
        for (dx, dy, rr) in ((-9, -6, 2), (-4, 8, 1.5), (8, -3, 1.2)):
            d.ellipse([U(46 + dx * stain - rr), U(140 + dy * stain - rr), U(46 + dx * stain + rr),
                       U(140 + dy * stain + rr)], fill=(8, 8, 18))
    if sweat > 0:
        d.polygon([(U(78), U(118)), (U(75), U(126)), (U(81), U(126))], fill=(170, 220, 255))
        d.ellipse([U(75), U(123), U(81), U(129)], fill=(170, 220, 255))
    return lay.resize((int(BW * s), int(BH * s)), Image.LANCZOS)


def crayon_layer(s, mood='neutral', look=(0, 0), blink=False, talk=0.0, t=0.0, eraser=1.0, upside=False,
                 sweat=0.0, sparkle=0.0):
    k = s * SS
    lay = Image.new('RGBA', (int(BW * k), int(BH * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    def U(v):
        return int(round(v * k))

    def Y(v):
        return U(BH - v) if upside else U(v)

    def R(x0, y0, x1, y1, **kw):
        ya, yb = sorted((Y(y0), Y(y1)))
        d.rectangle([U(x0), ya, U(x1), yb], **kw)

    def P(pts, **kw):
        d.polygon([(U(x), Y(y)) for x, y in pts], **kw)

    eh = 34 * eraser
    if eraser > 0.02:
        ya, yb = sorted((Y(48 - eh), Y(50)))
        d.rounded_rectangle([U(44), ya, U(76), yb], radius=U(min(8, eh / 2)), fill=(245, 138, 165))
        R(48, 50 - eh + 3, 53, 48, fill=(255, 188, 205))
        R(69, 50 - eh + 3, 74, 48, fill=(215, 100, 130))
    R(43, 46, 77, 72, fill=(192, 198, 212))
    R(46, 47, 50, 71, fill=(235, 238, 245))
    R(70, 47, 75, 71, fill=(140, 146, 162))
    for yy in (52, 57, 62, 67):
        R(43, yy, 77, yy + 1, fill=(150, 156, 172))
    R(44, 72, 54, 214, fill=(255, 218, 95))
    R(54, 72, 66, 214, fill=(250, 192, 45))
    R(66, 72, 76, 214, fill=(222, 155, 28))
    R(53.5, 72, 54.5, 214, fill=(235, 175, 40))
    R(65.5, 72, 66.5, 214, fill=(205, 140, 25))
    P([(44, 214), (76, 214), (60, 258)], fill=(238, 200, 155))
    P([(62, 214), (76, 214), (61, 256)], fill=(212, 168, 122))
    for i in range(4):
        P([(44 + i * 8, 214), (52 + i * 8, 214), (48 + i * 8, 219)], fill=(222, 155, 28) if i > 1 else (250, 192, 45))
    P([(54.5, 244), (65.5, 244), (60, 264)], fill=(58, 58, 70))
    P([(54.5, 244), (59, 244), (59.5, 262)], fill=(95, 95, 110))
    # visage (toujours à l'endroit)
    cx = 60
    cy = (BH - 120) if upside else 120
    U2 = U
    face(d, U2, cx, cy, 19, 7.5, 8.5, mood, look, blink, talk, t, brow_col=(120, 70, 30), blush=(255, 140, 120))
    lids(d, U2, cx, cy, 19, 7.5, 8.5, mood, (250, 192, 45), blink)
    for fx, fy in ((47, cy + 13), (50, cy + 15), (73, cy + 13), (70, cy + 15)):
        d.ellipse([U(fx - 0.7), U(fy - 0.7), U(fx + 0.7), U(fy + 0.7)], fill=(200, 120, 40))
    if sweat > 0:
        d.polygon([(U(77), U(cy - 8)), (U(74), U(cy)), (U(80), U(cy))], fill=(170, 220, 255))
        d.ellipse([U(74), U(cy - 3), U(80), U(cy + 3)], fill=(170, 220, 255))
    out = lay.resize((int(BW * s), int(BH * s)), Image.LANCZOS)
    return out


def hand_layer(s, sleeve=(196, 72, 64)):
    """Main de Lou qui tient l'outil (repère local : pointe en (0,0), outil vertical)."""
    k = s * SS
    C = 230
    lay = Image.new('RGBA', (int(2 * C * k), int(2 * C * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    def P(x, y):
        return (int((C + x) * k), int((C + y) * k))

    skin, skin2, skin3 = (246, 196, 168), (228, 168, 140), (205, 140, 115)
    d.polygon([P(70, -40), P(230, 10), P(215, 90), P(52, 10)], fill=sleeve)
    d.polygon([P(70, -40), P(90, -32), P(70, 20), P(52, 10)], fill=mixc(sleeve, (255, 255, 255), 0.25))
    d.polygon([P(36, -64), P(96, -36), P(76, 18), P(18, -16)], fill=skin2)
    d.ellipse([*P(4, -78), *P(62, -12)], fill=skin)
    capsule(d, P(14, -38), P(-2, -60), 9 * k, skin2)
    capsule(d, P(30, -66), P(2, -52), 8.5 * k, skin)
    capsule(d, P(24, -22), P(4, -36), 8 * k, skin)
    capsule(d, P(30, -10), P(14, -22), 7 * k, skin3)
    d.ellipse([*P(-6, -60), *P(4, -50)], fill=(255, 220, 205))
    d.line([P(16, -46), P(26, -50)], fill=skin3, width=int(1.2 * k))
    return lay.resize((int(2 * C * s), int(2 * C * s)), Image.LANCZOS), C * s


def put(img, lay, x, y, tilt=0.0, anchor=None, alpha=1.0):
    """Colle `lay` avec son point d'ancrage (par défaut la pointe) en (x, y), rotation autour de ce point."""
    ax, ay = anchor if anchor else (TIP[0] * lay.width / BW, TIP[1] * lay.height / BH)
    if tilt:
        R = int(math.hypot(max(ax, lay.width - ax), max(ay, lay.height - ay))) + 2
        pad = Image.new('RGBA', (2 * R, 2 * R), (0, 0, 0, 0))
        pad.paste(lay, (int(R - ax), int(R - ay)))
        lay = pad.rotate(tilt, resample=Image.BICUBIC)
        ax = ay = R
    if alpha < 1:
        lay = lay.copy()
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * alpha)))
    img.paste(lay, (int(round(x - ax)), int(round(y - ay))), lay)


def put_hand(img, s, x, y, tilt):
    lay, c = hand_layer(s)
    put(img, lay, x, y, tilt, anchor=(c, c))


def shadow_under(img, x, y, rx, ry, a=90):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([x - rx, y - ry, x + rx, y + ry], fill=(20, 10, 10, a))
    img.paste(blur(lay, max(1, ry / 2)), (0, 0), blur(lay, max(1, ry / 2)))


def rim(lay, dx, dy, col, amt=0.9):
    """Liseré de lumière sur le bord d'un calque (contre-jour)."""
    a = np.asarray(lay.getchannel('A'), np.float32) / 255
    sh = np.roll(np.roll(a, dy, 0), dx, 1)
    edge = np.clip(a - sh, 0, 1) * amt
    rgb = np.asarray(lay.convert('RGB'), np.float32)
    rgb = rgb * (1 - edge[..., None]) + np.array(col, np.float32) * edge[..., None]
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    out.putalpha(lay.getchannel('A'))
    return out


def tint(lay, col, amt):
    rgb = np.asarray(lay.convert('RGB'), np.float32)
    rgb = rgb * (1 - amt) + rgb * np.array(col, np.float32) / 255 * amt
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    out.putalpha(lay.getchannel('A'))
    return out


def blink(t, seed):
    return ((t + seed * 1.37) % 3.3) < 0.12


# ================================================================ éclairages
TOD = {
    #           ambiance            lumière lampe        lune / soleil
    'eve': dict(amb=(0.95, 0.82, 0.72), lamp=0.0, lampc=(1.0, 0.8, 0.5), win=(1.1, 0.75, 0.5), wina=0.5,
                sky=[(0, (255, 170, 120)), (0.6, (250, 120, 110)), (1, (120, 70, 120))]),
    'night': dict(amb=(0.28, 0.27, 0.45), lamp=1.15, lampc=(1.25, 0.95, 0.6), win=(0.5, 0.6, 1.0), wina=0.25,
                  sky=[(0, (14, 16, 48)), (0.7, (40, 34, 90)), (1, (70, 50, 110))]),
    'dark': dict(amb=(0.14, 0.14, 0.26), lamp=0.0, lampc=(1.2, 0.9, 0.6), win=(0.5, 0.6, 1.0), wina=0.35,
                 sky=[(0, (10, 12, 40)), (0.7, (34, 30, 80)), (1, (60, 44, 100))]),
    'moon': dict(amb=(0.22, 0.27, 0.5), lamp=0.0, lampc=(1, 1, 1), win=(0.7, 0.85, 1.25), wina=0.95,
                 sky=[(0, (10, 14, 46)), (0.7, (30, 40, 96)), (1, (52, 60, 120))]),
    'morning': dict(amb=(0.85, 0.78, 0.72), lamp=0.0, lampc=(1, 1, 1), win=(1.35, 1.05, 0.7), wina=0.9,
                    sky=[(0, (255, 214, 150)), (0.55, (255, 180, 150)), (1, (190, 160, 200))]),
}

# ================================================================ décor : le bureau (monde 600 x 640)
DW = 600
DESK_Y = 410
HOME = {'plume': (190, 560), 'crayon': (430, 560), 'pot': (505, 545), 'ink': (110, 520), 'lamp': (300, 470)}


def desk_wall(tod):
    def mk():
        c = TOD[tod]
        img = Image.fromarray(vgrad(DW, H, [(0, (120, 78, 70)), (0.6, (150, 98, 82)), (1, (120, 76, 64))]).astype(np.uint8))
        d = ImageDraw.Draw(img)
        for x in range(0, DW, 24):
            d.line([x, 0, x, DESK_Y], fill=(132, 86, 74), width=2)
        # fenêtre
        wx0, wy0, wx1, wy1 = 360, 50, 560, 330
        sky = Image.fromarray(vgrad(wx1 - wx0, wy1 - wy0, c['sky']).astype(np.uint8))
        sd = ImageDraw.Draw(sky)
        r = random.Random(4)
        if tod in ('night', 'moon', 'dark'):
            for _ in range(40):
                x, y = r.randint(0, wx1 - wx0), r.randint(0, 200)
                sd.point((x, y), fill=(255, 250, 220))
            sd.ellipse([120, 30, 168, 78], fill=(255, 248, 220))
            sd.ellipse([112, 26, 156, 70], fill=c['sky'][0][1])
        elif tod == 'morning':
            sd.ellipse([40, 150, 140, 250], fill=(255, 240, 190))
        else:
            sd.ellipse([60, 140, 150, 230], fill=(255, 220, 160))
        # silhouette de ville
        bx = 0
        while bx < wx1 - wx0:
            bw, bh = r.randint(16, 34), r.randint(30, 110)
            colb = (30, 26, 52) if tod in ('night', 'moon', 'dark') else (150, 90, 110)
            sd.rectangle([bx, wy1 - wy0 - bh, bx + bw, wy1 - wy0], fill=colb)
            if tod in ('night', 'dark', 'moon'):
                for wy in range(wy1 - wy0 - bh + 6, wy1 - wy0 - 4, 9):
                    for wxx in range(bx + 3, bx + bw - 3, 7):
                        if r.random() < 0.35:
                            sd.rectangle([wxx, wy, wxx + 2, wy + 3], fill=(255, 210, 120))
            bx += bw + r.randint(0, 4)
        img.paste(sky, (wx0, wy0))
        d.rectangle([wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8], outline=(235, 220, 200), width=8)
        d.line([(wx0 + wx1) // 2, wy0, (wx0 + wx1) // 2, wy1], fill=(235, 220, 200), width=6)
        d.line([wx0, (wy0 + wy1) // 2, wx1, (wy0 + wy1) // 2], fill=(235, 220, 200), width=6)
        d.rectangle([wx0 - 16, wy1 + 6, wx1 + 16, wy1 + 16], fill=(240, 228, 210))
        # rideaux
        for cx0, cx1 in ((wx0 - 40, wx0 + 10), (wx1 - 10, wx1 + 40)):
            d.rectangle([cx0, 30, cx1, 360], fill=(150, 50, 60))
            for xx in range(cx0 + 6, cx1, 10):
                d.line([xx, 30, xx, 360], fill=(120, 36, 48), width=3)
        d.rectangle([wx0 - 50, 22, wx1 + 50, 32], fill=(90, 60, 40))
        # bibliothèque
        d.rectangle([18, 40, 300, 380], fill=(86, 52, 36))
        for sy in (40, 150, 260, 370):
            d.rectangle([14, sy, 304, sy + 10], fill=(110, 70, 46))
        cols = [(150, 50, 50), (60, 90, 140), (200, 160, 70), (70, 120, 80), (120, 70, 130), (220, 210, 190),
                (170, 90, 50)]
        for sy in (50, 160, 270):
            x = 26
            while x < 290:
                bw = r.randint(9, 18)
                bh = r.randint(66, 98)
                cb = r.choice(cols)
                if r.random() < 0.12:
                    d.polygon([(x, sy + 100), (x + bw, sy + 100), (x + bw + 14, sy + 100 - bh), (x + 14, sy + 100 - bh)],
                              fill=cb)
                    x += bw + 16
                    continue
                d.rectangle([x, sy + 100 - bh, x + bw, sy + 100], fill=cb)
                d.rectangle([x + 2, sy + 100 - bh + 8, x + bw - 2, sy + 100 - bh + 11], fill=mixc(cb, (255, 230, 150), 0.5))
                x += bw + 1
        # cadre
        d.rectangle([316, 120, 348, 170], fill=(200, 160, 80))
        d.rectangle([320, 124, 344, 166], fill=(90, 140, 160))
        return arr(img)
    return cached(('wall', tod), mk)


def desk_surface():
    def mk():
        img = Image.new('RGBA', (DW, H), (0, 0, 0, 0))
        g = vgrad(DW, H - DESK_Y, [(0, (120, 72, 44)), (0.4, (150, 92, 54)), (1, (96, 56, 34))])
        top = Image.fromarray(g.astype(np.uint8))
        d = ImageDraw.Draw(top)
        r = random.Random(7)
        for i in range(0, H - DESK_Y, 26):
            d.line([0, i, DW, i], fill=(90, 52, 30), width=2)
            for _ in range(10):
                x = r.randint(0, DW)
                d.line([x, i + 6, x + r.randint(30, 90), i + 6 + r.randint(-2, 2)], fill=(132, 80, 46), width=1)
        img.paste(top, (0, DESK_Y))
        d2 = ImageDraw.Draw(img)
        d2.rectangle([0, DESK_Y - 6, DW, DESK_Y + 4], fill=(170, 110, 66))
        # encrier
        x, y = HOME['ink']
        d2.ellipse([x - 34, y - 8, x + 34, y + 12], fill=(30, 30, 50))
        d2.rounded_rectangle([x - 32, y - 52, x + 32, y + 2], radius=10, fill=(40, 48, 80))
        d2.rectangle([x - 12, y - 66, x + 12, y - 50], fill=(30, 30, 40))
        d2.rectangle([x - 26, y - 46, x - 18, y - 6], fill=(110, 130, 190))
        # pot à crayons
        x, y = HOME['pot']
        for i, (cc, dx, hh) in enumerate(((220, 60, 60), -22, 120), ) if False else []:
            pass
        pens = [((220, 70, 70), -24, 112, -8), ((70, 140, 220), -10, 128, -3), ((90, 180, 90), 4, 118, 4),
                ((240, 160, 50), 18, 106, 10), ((150, 80, 190), 28, 96, 15)]
        for col, dx, hh, ang in pens:
            lay = Image.new('RGBA', (20, hh + 20), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lay)
            dl.rectangle([4, 14, 16, hh + 20], fill=col)
            dl.rectangle([4, 14, 8, hh + 20], fill=mixc(col, (255, 255, 255), 0.35))
            dl.polygon([(4, 14), (16, 14), (10, 0)], fill=(238, 200, 155))
            dl.polygon([(8, 5), (12, 5), (10, 0)], fill=col)
            lay = lay.rotate(-ang, expand=True, resample=Image.BICUBIC)
            img.paste(lay, (x + dx - lay.width // 2, y - 60 - hh), lay)
        d2.rounded_rectangle([x - 40, y - 80, x + 40, y + 6], radius=8, fill=(70, 120, 120))
        d2.rectangle([x - 40, y - 60, x + 40, y - 52], fill=(240, 200, 90))
        d2.rectangle([x - 34, y - 76, x - 26, y + 2], fill=(110, 170, 165))
        # pile de livres
        for i, (col, w) in enumerate(((150, 60, 50), 120), ) if False else []:
            pass
        for i, (col, w) in enumerate((((150, 60, 50), 130), ((60, 80, 130), 116), ((200, 170, 90), 124))):
            y0 = 470 - i * 22
            d2.rectangle([-20, y0 - 22, -20 + w, y0], fill=col)
            d2.rectangle([-20, y0 - 18, -20 + w - 6, y0 - 14], fill=mixc(col, (255, 230, 160), 0.4))
        # lampe
        x, y = HOME['lamp']
        d2.ellipse([x - 44, y - 10, x + 44, y + 12], fill=(40, 90, 70))
        d2.ellipse([x - 44, y - 16, x + 44, y + 6], fill=(60, 130, 100))
        d2.line([x, y - 6, x - 30, y - 150], fill=(50, 110, 85), width=8)
        d2.line([x - 30, y - 150, x - 90, y - 230], fill=(50, 110, 85), width=7)
        d2.ellipse([x - 38, y - 158, x - 22, y - 142], fill=(200, 170, 80))
        d2.polygon([(x - 120, y - 262), (x - 56, y - 216), (x - 96, y - 160), (x - 160, y - 206)], fill=(40, 120, 90))
        d2.polygon([(x - 160, y - 206), (x - 96, y - 160), (x - 104, y - 150), (x - 170, y - 196)], fill=(250, 230, 160))
        return img
    return cached('surface', mk)


def lamp_mask():
    def mk():
        x, y = HOME['lamp']
        m = radial(DW, H, x - 60, 560, 340, 200, 1.4) * 1.0
        cone = poly_mask(DW, H, [(x - 165, y - 200), (x - 100, y - 155), (x + 200, 640), (x - 420, 640)], blur=30)
        m = np.maximum(m, cone * 0.55)
        m += radial(DW, H, x - 132, y - 184, 50, 50, 2.0) * 1.6
        return m
    return cached('lampmask', mk)


def window_mask(tod):
    def mk():
        m = poly_mask(DW, H, [(360, 50), (560, 50), (380, 640), (60, 640)], blur=26) * 0.75
        m += radial(DW, H, 460, 190, 130, 160, 1.5) * 0.8
        return m
    return cached(('winmask', tod), mk)


def light(a, tod, lamp_k=1.0, ox=0, w=W):
    c = TOD[tod]
    amb = np.array(c['amb'], np.float32)
    L = np.zeros(a.shape, np.float32) + amb
    if c['lamp'] * lamp_k > 0:
        L += lamp_mask()[:, ox:ox + w, None] * np.array(c['lampc'], np.float32) * c['lamp'] * lamp_k
    if c['wina'] > 0:
        L += window_mask(tod)[:, ox:ox + w, None] * np.array(c['win'], np.float32) * c['wina'] * 0.6
    return a * L


def paper_ball(seed, r):
    def mk():
        rr = random.Random(seed)
        k = 3
        lay = Image.new('RGBA', (int(r * 2 * k + 4), int(r * 2 * k + 4)), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        c = r * k + 2
        pts = []
        for i in range(14):
            a = i / 14 * 6.283
            rad = r * k * rr.uniform(0.78, 1.0)
            pts.append((c + math.cos(a) * rad, c + math.sin(a) * rad))
        d.polygon(pts, fill=(238, 234, 226))
        d.polygon([(c + (x - c) * 0.9 + r * k * 0.12, c + (y - c) * 0.9 + r * k * 0.12) for x, y in pts],
                  fill=(205, 200, 195))
        d.polygon([(c + (x - c) * 0.75 - r * k * 0.1, c + (y - c) * 0.75 - r * k * 0.1) for x, y in pts],
                  fill=(250, 248, 242))
        for _ in range(6):
            a, b2 = rr.uniform(0, 6.28), rr.uniform(0, 6.28)
            d.line([c + math.cos(a) * r * k * 0.7, c + math.sin(a) * r * k * 0.7, c + math.cos(b2) * r * k * 0.3,
                    c + math.sin(b2) * r * k * 0.3], fill=(180, 175, 170), width=k)
        return lay.resize((lay.width // k, lay.height // k), Image.LANCZOS)
    return cached(('ball', seed, r), mk)


def set_desk(t, u, p):
    """Plan large du bureau. p : tod, ox (fn u), actors [(kind, x, y, s, kwargs)], balls, lamp_k, fg."""
    tod = p.get('tod', 'eve')
    ox = int(p['ox'](u)) if callable(p.get('ox')) else int(p.get('ox', 120))
    ox = max(0, min(DW - W, ox))
    wall = desk_wall(tod)
    wox = int(ox * 0.75 + (DW - W) * 0.25 * 0.5)
    base = Image.fromarray(wall[:, wox:wox + W].astype(np.uint8)).convert('RGBA')
    world = Image.new('RGBA', (DW, H), (0, 0, 0, 0))
    world.paste(desk_surface(), (0, 0), desk_surface())
    for kind, x, y, s, kw in p.get('actors', []):
        kw = dict(kw)
        tilt = kw.pop('tilt', 0)
        if kind == 'plume':
            lay = plume_layer(s, t=t, blink=blink(t, 0), **kw)
        else:
            lay = crayon_layer(s, t=t, blink=blink(t, 1), **kw)
        shadow_under(world, x, y, 26 * s, 6 * s)
        put(world, lay, x, y, tilt)
    for (bx, by, tl, r, seed) in p.get('balls', []):
        dt = t - tl
        if dt < -0.6:
            continue
        if dt < 0:
            yy = by - (dt * dt) * 1400
        else:
            yy = by - abs(math.sin(dt * 9)) * 22 * math.exp(-dt * 5)
        ball = paper_ball(seed, r)
        shadow_under(world, bx, by + r * 0.8, r, r * 0.3, 70)
        world.paste(ball, (int(bx - ball.width / 2), int(yy - ball.height / 2)), ball)
    if p.get('letter'):
        lx, ly = p['letter']
        d = ImageDraw.Draw(world)
        d.polygon([(lx - 80, ly - 20), (lx + 80, ly - 26), (lx + 92, ly + 30), (lx - 92, ly + 36)], fill=(246, 240, 226))
    base.paste(world.crop((ox, 0, ox + W, H)), (0, 0), world.crop((ox, 0, ox + W, H)))
    a = arr(base.convert('RGB'))
    full = np.zeros((H, DW, 3), np.float32)
    a = light(a, tod, p.get('lamp_k', 1.0), ox, W) if True else a
    img = toimg(a)
    if p.get('fg'):
        fg = cached('fgbook', make_fg_book)
        fx = int(p['fg'](u))
        img.paste(fg, (fx, H - 130), fg)
    return img


def make_fg_book():
    lay = Image.new('RGBA', (220, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([20, 20, 200, 300], radius=14, fill=(60, 30, 26))
    d.rectangle([30, 30, 190, 60], fill=(140, 100, 50))
    return blur(lay, 7)


# ================================================================ décor : gros plan sur fond flou
def close_bg(tod, focus_x, zoom=1.9, lamp_k=1.0):
    def mk():
        wall = desk_wall(tod)
        world = Image.fromarray(wall.astype(np.uint8)).convert('RGBA')
        world.paste(desk_surface(), (0, 0), desk_surface())
        a = arr(world.convert('RGB'))
        L = np.zeros(a.shape, np.float32) + np.array(TOD[tod]['amb'], np.float32)
        c = TOD[tod]
        if c['lamp'] * lamp_k > 0:
            L += lamp_mask()[..., None] * np.array(c['lampc'], np.float32) * c['lamp'] * lamp_k
        if c['wina'] > 0:
            L += window_mask(tod)[..., None] * np.array(c['win'], np.float32) * c['wina'] * 0.6
        lit = toimg(a * L)
        w, h = W / zoom, H / zoom
        x0 = clamp(focus_x - w / 2, 0, DW - w)
        y0 = clamp(470 - h * 0.62, 0, H - h)
        crop = lit.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
        crop = blur(crop, 7)
        # bokeh
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        r = random.Random(int(focus_x) + len(tod))
        bc = {'eve': (255, 200, 140), 'night': (255, 200, 120), 'moon': (150, 180, 255), 'morning': (255, 230, 170),
              'dark': (120, 140, 220)}[tod]
        for _ in range(18):
            x, y, rr = r.randint(0, W), r.randint(0, 380), r.randint(8, 26)
            dl.ellipse([x - rr, y - rr, x + rr, y + rr], fill=bc + (r.randint(20, 60),),
                       outline=bc + (90,), width=2)
        lay = blur(lay, 1.5)
        crop.paste(lay, (0, 0), lay)
        return crop
    return cached(('closebg', tod, int(focus_x), zoom, lamp_k), mk)


RIMC = {'eve': (255, 210, 160), 'night': (255, 210, 140), 'moon': (170, 200, 255), 'morning': (255, 230, 180),
        'dark': (130, 150, 230)}


def set_close(t, u, p):
    """Gros plan : p = who, tod, s, x, y, kw, fg (autre perso flou au premier plan), dx (fn u)."""
    tod = p.get('tod', 'eve')
    img = close_bg(tod, p.get('focus', HOME[p['who']][0]), lamp_k=p.get('lamp_k', 1.0)).copy()
    s = p.get('s', 2.3)
    kw = dict(p.get('kw', {}))
    if callable(kw.get('mood')):
        kw['mood'] = kw['mood'](t)
    tilt = kw.pop('tilt', 0)
    bob = math.sin(t * 2.2) * 2
    if p['who'] == 'plume':
        lay = plume_layer(s, t=t, blink=blink(t, 0), **kw)
    else:
        lay = crayon_layer(s, t=t, blink=blink(t, 1), **kw)
    amb = TOD[tod]['amb']
    lay = tint(lay, tuple(int(255 * min(1, v * 1.15 + 0.12)) for v in amb), 0.85)
    lay = rim(lay, -4 if p.get('rim', 1) > 0 else 4, 0, RIMC[tod], 0.85)
    x = p.get('x', CX)
    if callable(x):
        x = x(u)
    y = p.get('y', 560)
    put(img, lay, x, y + bob, tilt)
    if p.get('fg'):
        who, fx, fs = p['fg']
        fl = plume_layer(fs, t=t, mood='neutral') if who == 'plume' else crayon_layer(fs, t=t, mood='neutral',
                                                                                          eraser=p.get('fg_er', 1.0))
        fl = tint(fl, (60, 50, 70), 0.75)
        fl = blur(fl, 5)
        put(img, fl, fx, 700)
    return img


# ================================================================ décor : la page (macro / vue de dessus)
PAGE_W, PAGE_H = 200, 280
LINES_Y = [44 + i * 24 for i in range(9)]


def build_letter():
    r = random.Random(11)
    items = []  # (type, data, length)
    items.append(('text', ("CHÈRE INÈS,", 18, 24), 11 * 6))
    for li in range(1, 7):
        y = LINES_Y[li]
        x = 18 if li > 1 else 30
        words = []
        while x < 176:
            wl = r.randint(14, 38)
            if x + wl > 182:
                break
            words.append((x, x + wl, r.uniform(0, 6)))
            x += wl + r.randint(6, 9)
        for (a, b, ph) in words:
            items.append(('word', (a, b, y, ph), b - a))
    items.append(('text', ("PARDON.", 18, LINES_Y[7] - 6), 7 * 6))
    items.append(('text', ("LOU", 138, LINES_Y[8] + 4), 3 * 6))
    total = sum(i[2] for i in items)
    return items, total


LETTER, LETTER_LEN = build_letter()


def word_pts(a, b, y, ph, upto=None):
    pts = []
    x = a
    end_x = b if upto is None else min(b, a + upto)
    while x <= end_x:
        hgt = 2.2 + 2.2 * math.sin(x * 1.25 + ph)
        asc = 5.5 * max(0, math.sin(x * 0.33 + ph * 2)) ** 10
        pts.append((x, y - hgt - asc))
        x += 0.7
    return pts


def paper_tex():
    def mk():
        rng = np.random.default_rng(3)
        n = rng.normal(0, 1, (PAGE_H * 2, PAGE_W * 2)).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(1.2)), np.float32) - 128
        base = np.zeros((PAGE_H * 2, PAGE_W * 2, 3), np.float32) + np.array([248, 241, 226], np.float32)
        base += n[..., None] * 0.35
        img = toimg(base)
        d = ImageDraw.Draw(img)
        for y in LINES_Y:
            d.line([0, y * 2, PAGE_W * 2, y * 2], fill=(200, 210, 230), width=1)
        d.line([12 * 2, 0, 12 * 2, PAGE_H * 2], fill=(235, 170, 170), width=1)
        return img
    return cached('papertex', mk)


def set_page(t, u, p):
    """Macro sur la feuille. p : cx, cy (page), k (px/unité), rot, bg, tod, pencil, ink, blot, scratch,
    mistake (0..1 effacement), ghost (fondu des mots crayon), tool=(kind, px, py, tilt, kw), hand, crumbs, text_rev."""
    get = lambda key, dflt=None: (p[key](u) if callable(p.get(key)) else p.get(key, dflt))  # noqa: E731
    k = get('k', 2.0)
    pcx, pcy = get('cx', 100), get('cy', 140)
    rot = get('rot', -4)
    tod = p.get('tod', 'night')
    bg = vgrad(W, H, [(0, (70, 40, 26)), (1, (40, 22, 16))])
    img = toimg(bg)
    # feuille texturée, transformée
    pw, ph = int(PAGE_W * k), int(PAGE_H * k)
    tex = paper_tex().resize((pw, ph), Image.BILINEAR).convert('RGBA')
    d = ImageDraw.Draw(tex)

    def P(x, y):
        return (x * k, y * k)

    pencil = get('pencil', 0.0) * LETTER_LEN
    ink = get('ink', 0.0) * LETTER_LEN
    ghost = get('ghost', 0.0)
    pc = mixc((120, 118, 130), (248, 241, 226), ghost)
    inkc = (24, 28, 72)
    acc = 0
    for typ, data, ln in LETTER:
        for layer_len, col, wdt in ((pencil, pc, 0.75), (ink, inkc, 1.05)):
            if layer_len <= acc:
                continue
            part = min(ln, layer_len - acc)
            if typ == 'word':
                a, b, y, phs = data
                pts = word_pts(a, b, y, phs, part)
                if len(pts) > 1:
                    d.line([P(*q) for q in pts], fill=col, width=max(1, int(wdt * k)), joint='curve')
            else:
                s_, x, y = data
                sc = max(1, int(round(k * 1.0)))
                draw_text(tex, s_, int((x + len(s_) * 3) * k), int(y * k), col, scale=sc, maxw=10 ** 4,
                          reveal=int(part / 6 + 0.999), shadow=None)
        acc += ln
    # brouillon raté (crayon) qu'on gomme
    if p.get('mistake') is not None:
        m = get('mistake')
        if m < 1:
            col = mixc((110, 108, 120), (248, 241, 226), m)
            y = LINES_Y[3]
            pts = [(60 + i * 2.4, y - 4 + (5 if i % 2 else -2)) for i in range(26)]
            d.line([P(*q) for q in pts], fill=col, width=max(1, int(0.9 * k)))
    if p.get('scratch') is not None:
        sv = get('scratch')
        if sv > 0:
            y = LINES_Y[1]
            n = int(30 * clamp(sv))
            pts = [(30 + i * 2.6, y - 2 + (6 if i % 2 else -3)) for i in range(n)]
            if len(pts) > 1:
                d.line([P(*q) for q in pts], fill=inkc, width=max(1, int(1.3 * k)))
    if p.get('blot') is not None:
        bv = get('blot')
        if bv > 0:
            bx, by = p.get('blot_at', (98, LINES_Y[1] - 2))
            rr = random.Random(5)
            R = 14 * eout(bv)
            pts = [(bx + math.cos(a) * R * (1 + 0.28 * math.sin(a * 5 + 1) + 0.12 * math.sin(a * 11)),
                    by + math.sin(a) * R * (1 + 0.28 * math.sin(a * 5 + 1) + 0.12 * math.sin(a * 11)))
                   for a in np.linspace(0, 6.283, 48)]
            d.polygon([P(*q) for q in pts], fill=(14, 14, 34))
            for _ in range(12):
                a, dist, sr = rr.uniform(0, 6.28), rr.uniform(1.1, 1.9), rr.uniform(0.6, 2.2)
                qx, qy = bx + math.cos(a) * R * dist, by + math.sin(a) * R * dist
                d.ellipse([*P(qx - sr * bv, qy - sr * bv), *P(qx + sr * bv, qy + sr * bv)], fill=(14, 14, 34))
    if p.get('final_words'):
        fw = get('final_words')
        draw_text(tex, "CE QUI RESTE", int(100 * k), int(120 * k), (120, 118, 130), scale=max(1, int(k * 1.6)),
                  maxw=10 ** 4, reveal=int(fw[0] * 12 + 0.99), shadow=None)
        draw_text(tex, "CE QUI RESTE", int(100 * k), int(120 * k), inkc, scale=max(1, int(k * 1.6)),
                  maxw=10 ** 4, reveal=int(fw[1] * 12 + 0.99), shadow=None)
    # ombre portée + rotation de la feuille
    ang = rot
    sh = Image.new('RGBA', (pw + 40, ph + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([20, 20, pw + 20, ph + 20], fill=(10, 5, 5, 140))
    sh = blur(sh, 10)
    tex2 = Image.new('RGBA', (pw + 40, ph + 40), (0, 0, 0, 0))
    tex2.paste(tex, (20, 20))
    shr = sh.rotate(ang, resample=Image.BICUBIC, center=(pcx * k + 20, pcy * k + 20))
    texr = tex2.rotate(ang, resample=Image.BICUBIC, center=(pcx * k + 20, pcy * k + 20))
    sy = get('sy', H * 0.5)
    ox, oy = int(CX - pcx * k - 20), int(sy - pcy * k - 20)
    img.paste(shr, (ox + 8, oy + 12), shr)
    img.paste(texr, (ox, oy), texr)

    def S(x, y):
        """page -> écran."""
        dx, dy = (x - pcx) * k, (y - pcy) * k
        a = math.radians(-ang)
        return CX + dx * math.cos(a) - dy * math.sin(a), sy + dx * math.sin(a) + dy * math.cos(a)

    # miettes de gomme
    if p.get('crumbs'):
        n, seed = get('crumbs')
        rr = random.Random(seed)
        dd = ImageDraw.Draw(img)
        for i in range(int(n)):
            x, y = S(rr.uniform(40, 170), rr.uniform(LINES_Y[2], LINES_Y[5]))
            sz = rr.uniform(0.8, 2.0) * k
            dd.ellipse([x - sz, y - sz * 0.7, x + sz, y + sz * 0.7], fill=(235, 130, 155))
    tool = p.get('tool')
    if tool:
        tool = tool(u, t) if callable(tool) else tool
        kind, tx, ty, tilt, kw = tool
        sx, sy2 = S(tx, ty)
        s = k * kw.pop('scale', 0.5)
        if kind == 'plume':
            lay = plume_layer(s, t=t, blink=blink(t, 0), **kw)
            anchor = None
        else:
            up = kw.get('upside', False)
            lay = crayon_layer(s, t=t, blink=blink(t, 1), **kw)
            anchor = (TIP[0] * s, (BH - 50 + 34 * kw.get('eraser', 1) * 0 - 4) * s) if up else None
            if up:
                er = kw.get('eraser', 1.0)
                anchor = (TIP[0] * s, (BH - 48 + 34 * er) * s)
        shadow_under(img, sx + 16 * s, sy2 + 6 * s, 18 * s, 5 * s, 80)
        put(img, lay, sx, sy2, tilt - ang, anchor=anchor)
        if p.get('hand'):
            put_hand(img, s, sx, sy2, tilt - ang)
    a = arr(img)
    c = TOD[tod]
    lc = get('lamp_xy', (CX - 80, 220))
    L = np.zeros(a.shape, np.float32) + np.array(c['amb'], np.float32) * 1.05
    if tod == 'night':
        L += cached(('pagelamp', lc), lambda: radial(W, H, lc[0], lc[1], 420, 460, 1.3))[..., None] * \
            np.array(c['lampc'], np.float32) * 0.72
    elif tod in ('moon', 'morning', 'eve'):
        L += cached(('pagewin', tod), lambda: poly_mask(W, H, [(80, -40), (300, -40), (420, 700), (-60, 700)], 40))[..., None] \
            * np.array(c['win'], np.float32) * (0.38 if tod == 'moon' else 0.18)
    return toimg(a * L)


# ================================================================ autres décors
def set_macro_nib(t, u, p):
    """Ouverture : plume géante qui calligraphie, goutte d'encre qui tremble."""
    img = toimg(vgrad(W, H, [(0, (14, 10, 28)), (0.6, (26, 16, 40)), (1, (40, 24, 40))]))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    r = random.Random(2)
    for _ in range(14):
        x, y, rr = r.randint(0, W), r.randint(0, 330), r.randint(10, 34)
        c = r.choice([(255, 190, 110), (200, 140, 255), (255, 220, 170)])
        dl.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c + (r.randint(18, 50),))
    img.paste(blur(lay, 3), (0, 0), blur(lay, 3))
    # papier en perspective
    paper = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(paper)
    dp.polygon([(-200, 470), (560, 470), (760, 640), (-400, 640)], fill=(244, 236, 220))
    prog = p.get('write', lambda u: 0)(u)
    # calligraphie dorée : boucles qui s'écrivent
    pts = []
    for i in range(int(160 * prog)):
        x = -40 + i * 2.6
        y = 540 + math.sin(i * 0.22) * 16 * math.exp(-((i - 80) / 70) ** 2) + math.sin(i * 0.6) * 4
        pts.append((x, y))
    if len(pts) > 1:
        dp.line(pts, fill=(20, 18, 50), width=4, joint='curve')
    img.paste(paper, (0, 0), paper)
    nx, ny = pts[-1] if pts else (-40, 540)
    if p.get('drop'):
        nx, ny = CX, 470
    s = p.get('s', 3.4)
    lay = plume_layer(s, mood=p.get('mood', 'proud'), t=t, blink=False, look=(0.6, 0.3))
    lay = rim(lay, -5, 0, (255, 210, 150), 0.9)
    put(img, lay, nx, ny, p.get('tilt', -24))
    if p.get('drop'):
        dv = p['drop'](u)
        dy = 6 + 10 * dv
        tremble = math.sin(t * 40) * (1 - dv) * 1.2
        d = ImageDraw.Draw(img)
        r0 = 6 + 4 * dv
        d.ellipse([nx - r0 + tremble, ny + dy - r0, nx + r0 + tremble, ny + dy + r0 * 1.4], fill=(12, 12, 40))
        d.polygon([(nx - 3, ny + 2), (nx + 3, ny + 2), (nx + tremble, ny + dy)], fill=(12, 12, 40))
        d.ellipse([nx - r0 * 0.5 + tremble, ny + dy - r0 * 0.6, nx - r0 * 0.1 + tremble, ny + dy - r0 * 0.1],
                  fill=(120, 120, 200))
    a = arr(img)
    a *= 0.7 + radial(W, H, nx, ny - 120, 300, 400, 1.2)[..., None] * 0.7
    return toimg(a)


def set_throne(t, u, p):
    """Contre-plongée : Monsieur Stylo-Plume sur son coussin de velours, rayons dorés. Monde 360 x 1100."""
    def mk_bg():
        bg = vgrad(W, 1100, [(0, (40, 16, 30)), (0.5, (90, 26, 40)), (1, (50, 12, 24))])
        img = toimg(bg)
        d = ImageDraw.Draw(img)
        for i in range(12):
            a0 = -math.pi / 2 + (i - 6) * 0.2
            pts = [(CX, 160), (CX + math.cos(a0 - 0.05) * 1400, 160 + math.sin(a0 - 0.05) * -1400 * -1),
                   (CX + math.cos(a0 + 0.05) * 1400, 160 + math.sin(a0 + 0.05) * -1400 * -1)]
        lay = Image.new('RGBA', (W, 1100), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        for i in range(14):
            a0 = math.pi / 2 + (i - 7) * 0.13
            dl.polygon([(CX, 80), (CX + math.cos(a0 - 0.035) * 1500, 80 + math.sin(a0 - 0.035) * 1500),
                        (CX + math.cos(a0 + 0.035) * 1500, 80 + math.sin(a0 + 0.035) * 1500)],
                       fill=(255, 210, 120, 38))
        img.paste(blur(lay, 4), (0, 0), blur(lay, 4))
        # coussin de velours
        d.ellipse([20, 960, 340, 1090], fill=(110, 20, 40))
        d.ellipse([30, 940, 330, 1050], fill=(170, 34, 60))
        d.ellipse([70, 950, 230, 1000], fill=(205, 70, 90))
        for x in (40, 320):
            d.line([x, 1000, x - 10 * (1 if x < 100 else -1), 1080], fill=(235, 190, 80), width=4)
        return img
    bg = cached('throne', mk_bg).copy()
    lay = plume_layer(2.9, mood=p.get('mood', 'proud'), t=t, blink=blink(t, 0), look=(0, -0.3))
    lay = rim(lay, -6, 0, (255, 220, 150), 1.0)
    lay = rim(lay, 6, 0, (255, 120, 140), 0.6)
    put(bg, lay, CX, 1000)
    # poussières dorées
    d = ImageDraw.Draw(bg)
    r = random.Random(9)
    for i in range(60):
        x = (r.uniform(0, W) + math.sin(t * 0.8 + i) * 12) % W
        y = (r.uniform(0, 1100) - t * r.uniform(8, 20)) % 1100
        if (i + int(t * 4)) % 3:
            d.point((x, y), fill=(255, 225, 150))
    cy = p['cy'](u)
    return bg.crop((0, int(cy), W, int(cy) + H))


def set_parchment(t, u, p):
    img = toimg(vgrad(W, H, [(0, (40, 18, 14)), (1, (20, 8, 8))]))
    d = ImageDraw.Draw(img)
    pts = [(40, 120), (330, 108), (342, 560), (28, 574)]
    d.polygon([(x + 6, y + 10) for x, y in pts], fill=(10, 4, 4))
    d.polygon(pts, fill=(226, 200, 150))
    d.polygon([(52, 132), (318, 122), (330, 548), (40, 560)], fill=(236, 214, 168))
    for i in range(7):
        y = 170 + i * 26
        d.line([70, y, 300, y - 3], fill=(170, 140, 100), width=2)
    prog = clamp(u / 0.62)
    pts = []
    for i in range(int(200 * prog)):
        a = i / 200
        x = 90 + a * 180 + math.sin(a * 18) * 16
        y = 430 + math.cos(a * 18) * 22 * (1 - a * 0.6) - a * 20
        pts.append((x, y))
    if len(pts) > 1:
        d.line(pts, fill=(25, 22, 60), width=3, joint='curve')
    nx, ny = pts[-1] if pts else (90, 452)
    if u < 0.66:
        lay = plume_layer(1.5, mood='proud', t=t, blink=False)
        lay = rim(lay, -4, 0, (255, 200, 140), 0.9)
        put(img, lay, nx, ny, -28)
    # sceau de cire
    sv = clamp((u - 0.68) / 0.08)
    if sv > 0:
        sc = 1 + (1 - eout(sv)) * 1.8
        r0 = 34 * sc
        sx, sy = 270, 470
        d.ellipse([sx - r0 * 1.15, sy - r0 * 1.1, sx + r0 * 1.15, sy + r0 * 1.2], fill=(140, 20, 30))
        d.ellipse([sx - r0, sy - r0, sx + r0, sy + r0], fill=(190, 30, 44))
        d.ellipse([sx - r0 * 0.7, sy - r0 * 0.7, sx + r0 * 0.7, sy + r0 * 0.7], outline=(130, 14, 26), width=3)
        draw_text(img, "SP", sx + 1, int(sy - 10 * sc), (130, 14, 26), scale=max(1, int(3 * sc)), shadow=None)
    a = arr(img) * (0.55 + radial(W, H, 190, 330, 330, 420, 1.0)[..., None] * 0.75)
    return toimg(a)


def set_monocle(t, u, p):
    """Vue subjective à travers le monocle de Monsieur Stylo-Plume."""
    tod = p.get('tod', 'eve')
    base = set_close(t, u, {'who': 'crayon', 'tod': tod, 's': p.get('s', 3.0), 'y': p.get('y', 900),
                            'kw': p.get('kw', {}), 'lamp_k': p.get('lamp_k', 1.0)})
    cx, cy, R = CX + math.sin(t * 1.3) * 6, 300 + math.cos(t * 1.1) * 5, 150
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    outside = Image.blend(blur(base, 8), Image.new('RGB', (W, H), (10, 6, 14)), 0.75)
    img = Image.composite(base, outside, mask)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10], outline=(150, 100, 30), width=14)
    d.ellipse([cx - R - 7, cy - R - 7, cx + R + 7, cy + R + 7], outline=(240, 195, 90), width=6)
    d.arc([cx - R - 7, cy - R - 7, cx + R + 7, cy + R + 7], 200, 250, fill=(255, 245, 210), width=4)
    # reflet qui balaie la lentille
    g = (u * 1.6) % 1.6 - 0.3
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(cx - R + g * 2 * R, cy - R), (cx - R + g * 2 * R + 40, cy - R),
                                 (cx - R + g * 2 * R - 60, cy + R), (cx - R + g * 2 * R - 100, cy + R)],
                                fill=(255, 255, 255, 40))
    lm = Image.new('L', (W, H), 0)
    ImageDraw.Draw(lm).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), lm))
    img.paste(lay, (0, 0), lay)
    return img


def set_glam(t, u, p):
    """La « magnifique gomme » : rayons tournants, paillettes."""
    img = toimg(vgrad(W, H, [(0, (255, 170, 190)), (1, (250, 120, 150))]))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    c0 = (CX, 300)
    rot = t * 0.6
    for i in range(16):
        a = rot + i * math.pi / 8
        dl.polygon([c0, (c0[0] + math.cos(a) * 900, c0[1] + math.sin(a) * 900),
                    (c0[0] + math.cos(a + 0.2) * 900, c0[1] + math.sin(a + 0.2) * 900)], fill=(255, 230, 160, 90))
    img.paste(lay, (0, 0), lay)
    pulse = 1.0 + 0.08 * math.sin(t * 10) + 0.25 * eback(u * 3)
    lay = crayon_layer(4.2, mood='joy', t=t, blink=False, eraser=pulse * 0.9, look=(0, -0.4))
    lay = rim(lay, -6, 0, (255, 255, 255), 0.8)
    put(img, lay, CX, 1010 + (1 - eout(u * 3)) * 80)
    d = ImageDraw.Draw(img)
    r = random.Random(3)
    for i in range(16):
        x, y = r.uniform(30, 330), r.uniform(120, 420)
        ph = (t * 3 + i * 0.7) % 2
        sz = 9 * max(0, 1 - abs(ph - 1)) + 1
        d.polygon([(x, y - sz), (x + sz * 0.25, y - sz * 0.25), (x + sz, y), (x + sz * 0.25, y + sz * 0.25), (x, y + sz),
                   (x - sz * 0.25, y + sz * 0.25), (x - sz, y), (x - sz * 0.25, y - sz * 0.25)], fill=(255, 255, 240))
    return img


def set_room(t, u, p):
    """Plan large de dos : la chambre de nuit, Lou s'installe, la lampe s'allume."""
    lamp = p.get('lamp', lambda u: 1)(u)
    img = toimg(vgrad(W, H, [(0, (24, 22, 50)), (1, (14, 12, 30))]))
    d = ImageDraw.Draw(img)
    wx0, wy0, wx1, wy1 = 50, 70, 310, 380
    sky = toimg(vgrad(wx1 - wx0, wy1 - wy0, TOD['night']['sky']))
    sd = ImageDraw.Draw(sky)
    r = random.Random(1)
    for i in range(60):
        x, y = r.randint(0, wx1 - wx0), r.randint(0, 220)
        if (i + int(t * 2)) % 7:
            sd.point((x, y), fill=(255, 250, 230))
    sd.ellipse([170, 30, 226, 86], fill=(255, 248, 225))
    sd.ellipse([160, 24, 212, 76], fill=TOD['night']['sky'][0][1])
    bx = 0
    while bx < wx1 - wx0:
        bw, bh = r.randint(16, 30), r.randint(40, 140)
        sd.rectangle([bx, wy1 - wy0 - bh, bx + bw, wy1 - wy0], fill=(26, 22, 48))
        for wy in range(wy1 - wy0 - bh + 6, wy1 - wy0 - 4, 10):
            for wxx in range(bx + 3, bx + bw - 3, 7):
                if r.random() < 0.3:
                    sd.rectangle([wxx, wy, wxx + 2, wy + 3], fill=(255, 205, 120))
        bx += bw + 2
    img.paste(sky, (wx0, wy0))
    d.rectangle([wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8], outline=(60, 56, 90), width=10)
    d.line([CX, wy0, CX, wy1], fill=(60, 56, 90), width=8)
    # bureau
    d.rectangle([0, 430, W, 470], fill=(50, 30, 30))
    d.rectangle([0, 470, W, H], fill=(30, 18, 22))
    # lampe
    d.polygon([(286, 330), (330, 300), (348, 336), (304, 364)], fill=(30, 70, 55))
    d.line([320, 340, 300, 430], fill=(30, 70, 55), width=6)
    # Lou de dos (silhouette)
    lx = CX - 30
    sil = (12, 8, 20)
    d.rounded_rectangle([lx - 70, 440, lx + 70, 560], radius=10, fill=(40, 24, 30))
    d.polygon([(lx - 66, 640), (lx - 58, 430), (lx - 30, 404), (lx + 30, 404), (lx + 58, 430), (lx + 66, 640)], fill=sil)
    d.ellipse([lx - 38, 320, lx + 38, 410], fill=sil)
    d.ellipse([lx - 16, 290, lx + 16, 330], fill=sil)
    a = arr(img)
    L = np.zeros(a.shape, np.float32) + np.array([0.75, 0.75, 1.0], np.float32)
    lm = cached('roomlamp', lambda: radial(W, H, 300, 420, 260, 240, 1.3))
    L += lm[..., None] * np.array([1.6, 1.15, 0.6], np.float32) * lamp
    out = a * L
    if lamp > 0:
        # liseré chaud sur la silhouette
        rm = cached('roomrim', lambda: poly_mask(W, H, [(lx + 30, 404), (lx + 58, 430), (lx + 66, 640), (lx + 60, 640),
                                                        (lx + 52, 432), (lx + 28, 410)], 1))
        out += rm[..., None] * np.array([255, 190, 110], np.float32) * lamp * 0.8
    return toimg(out)


def set_bin(t, u, p):
    img = toimg(vgrad(W, H, [(0, (150, 110, 90)), (0.55, (190, 140, 100)), (0.56, (140, 90, 56)), (1, (100, 60, 40))]))
    d = ImageDraw.Draw(img)
    d.polygon([(70, 300), (290, 300), (264, 600), (96, 600)], fill=(60, 60, 70))
    for i in range(12):
        x0 = 70 + i * 20
        d.line([x0, 300, 96 + i * 14.2, 600], fill=(110, 110, 125), width=3)
    for y in range(320, 600, 30):
        f = (y - 300) / 300
        d.line([70 + 26 * f, y, 290 - 26 * f, y], fill=(110, 110, 125), width=3)
    for i, (x, y, r, sd) in enumerate(((120, 300, 30, 1), (180, 286, 34, 2), (240, 302, 28, 3), (150, 270, 26, 4),
                                       (215, 262, 27, 5))):
        b = paper_ball(sd, r)
        img.paste(b, (x - b.width // 2, y - b.height // 2), b)
    d.ellipse([60, 288, 300, 316], outline=(130, 130, 145), width=5)
    a = arr(img)
    a *= 0.6 + cached('binlight', lambda: poly_mask(W, H, [(0, 0), (200, 0), (420, 640), (120, 640)], 40))[..., None] \
        * np.array([0.7, 0.55, 0.35], np.float32)
    return toimg(a)


def set_crumbs(t, u, p):
    img = toimg(vgrad(W, H, [(0, (40, 26, 30)), (1, (70, 40, 30))]))
    beam = cached('beam', lambda: poly_mask(W, H, [(150, -20), (260, -20), (330, 660), (90, 660)], 22))
    a = arr(img) + beam[..., None] * np.array([120, 90, 50], np.float32)
    img = toimg(a)
    d = ImageDraw.Draw(img)
    r = random.Random(8)
    for i in range(90):
        x = r.uniform(60, 320) + math.sin(t + i) * 8
        y = (r.uniform(0, H) - t * r.uniform(6, 18)) % H
        inb = beam[int(clamp(y, 0, H - 1)), int(clamp(x, 0, W - 1))]
        sz = r.uniform(1.0, 3.2)
        col = mixc((235, 130, 155), (255, 235, 170), inb)
        d.ellipse([x - sz, y - sz * 0.7, x + sz, y + sz * 0.7], fill=col)
        if inb > 0.5 and (i + int(t * 5)) % 9 == 0:
            d.line([x - 6, y, x + 6, y], fill=(255, 250, 220))
            d.line([x, y - 6, x, y + 6], fill=(255, 250, 220))
    return img


def set_envelope(t, u, p):
    img = toimg(vgrad(W, H, [(0, (196, 140, 96)), (1, (130, 80, 50))]))
    a = arr(img) * (0.7 + cached('envl', lambda: poly_mask(W, H, [(0, -40), (240, -40), (460, 700), (80, 700)], 40))
                    [..., None] * np.array([0.7, 0.55, 0.35], np.float32))
    img = toimg(a)
    fly = clamp((u - 0.55) / 0.45)
    ex, ey = CX + eout(fly) * 40, 340 - (fly ** 2) * 700
    rot = fly * 25
    lay = Image.new('RGBA', (260, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([10, 20, 250, 170], fill=(250, 244, 230))
    flap = clamp(u / 0.25)
    d.polygon([(10, 20), (250, 20), (130, 20 + 90 * flap)], fill=(232, 222, 200))
    d.line([(10, 170), (120, 90)], fill=(220, 210, 190), width=2)
    d.line([(250, 170), (140, 90)], fill=(220, 210, 190), width=2)
    hs = clamp((u - 0.3) / 0.08)
    if hs > 0:
        sc = 1 + (1 - eout(hs)) * 1.5
        hx, hy = 130, 20 + 90 * flap - 6
        rr = 13 * sc
        d.ellipse([hx - rr, hy - rr, hx, hy], fill=(230, 60, 80))
        d.ellipse([hx, hy - rr, hx + rr, hy], fill=(230, 60, 80))
        d.polygon([(hx - rr, hy - rr / 2), (hx + rr, hy - rr / 2), (hx, hy + rr * 0.9)], fill=(230, 60, 80))
    draw_text(lay, "INÈS", 130, 120, (40, 40, 80), scale=2, shadow=None)
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    sh.paste((20, 10, 5, 110), (0, 0), lay)
    sh = blur(sh, 8)
    off = 14 + fly * 120
    img.paste(sh, (int(ex - lay.width / 2 + off), int(ey - lay.height / 2 + off)), sh)
    img.paste(lay, (int(ex - lay.width / 2), int(ey - lay.height / 2)), lay)
    return img


# ================================================================ découpage (plans)
def two_shot(tod, mp, mc, **kw):
    return dict(tod=tod, ox=kw.get('ox', 120), actors=[('plume', HOME['plume'][0], 560, 0.95, dict(mood=mp, look=(1, 0), **kw.get('pk', {}))),
                                                        ('crayon', HOME['crayon'][0], 560, 0.95, dict(mood=mc, look=(-1, 0), **kw.get('ck', {})))])


def writer_path(u, lines=(1, 7)):
    """Position (page) d'écriture le long des lignes."""
    a, b = lines
    n = b - a
    k = min(n - 1, int(u * n))
    v = u * n - k
    return 18 + v * 158, LINES_Y[a + k] - 2


def build_shots():
    S_ = []

    def shot(t0, fn, p, cam=None, tin='cut', grade=None, ca=0.0):
        S_.append(dict(t0=t0, fn=fn, p=p, cam=cam or [(0, 1.0, CX, H / 2, 0), (1, 1.0, CX, H / 2, 0)], tin=tin,
                       grade=grade, ca=ca))

    Z = lambda z0, z1, cx0=CX, cy0=H / 2, cx1=None, cy1=None, r0=0, r1=0: [(0, z0, cx0, cy0, r0), (1, z1, cx1 or cx0, cy1 or cy0, r1)]  # noqa: E731,E501
    # --- N1 : accroche
    shot(0, set_macro_nib, dict(write=lambda u: 0.25 + u * 0.75, s=3.2), Z(1.12, 1.0, CX, 330, r0=-2, r1=1))
    shot(at('N1', "Et c'était"), set_macro_nib, dict(drop=lambda u: eout(u * 1.2), s=4.2, tilt=-8, mood='neutral'),
         Z(1.0, 1.25, CX, 420), tin='flash')
    # --- N2 : Monsieur Stylo-Plume
    shot(at('N2'), set_throne, dict(cy=lambda u: lerp(460, 250, ease(u))), Z(1.15, 1.0), tin='ink')
    shot(at('N2', "Il ne signait"), set_parchment, {}, Z(1.25, 1.05, 180, 400, r0=3, r1=-1))
    shot(at('N2', "Et sur ce bureau"), set_desk,
         dict(tod='eve', ox=lambda u: lerp(0, 240, ease(u)), fg=lambda u: lerp(260, -240, ease(u)),
              actors=[('plume', 190, 560, 0.95, dict(mood='grumpy', look=(1, 0))),
                      ('crayon', 430, 560, 0.95, dict(mood='happy', look=(0, 0)))]),
         Z(1.18, 1.1, CX, 380), tin='whip')
    # --- P1 : « Fort ridicule »
    shot(at('P1'), set_close, dict(who='plume', tod='eve', s=2.4, y=640, x=150, kw=dict(mood='suspicious', look=(1, 0), talk=1),
                                   fg=('crayon', 380, 2.6)), Z(1.0, 1.08, CX, 300), tin='cut')
    shot(at('P1', "avec sa gomme"), set_monocle, dict(tod='eve', kw=dict(mood='happy', look=(0, 0))), Z(1.0, 1.12))
    shot(at('P1', "Fort"), set_close, dict(who='plume', tod='eve', s=2.6, y=650, x=CX,
                                          kw=dict(mood='proud', look=(-0.6, -0.8), tilt=4, talk=1)),
         Z(1.1, 1.18, CX, 290, r0=0, r1=-2))
    # --- N3 : Petit Crayon
    shot(at('N3'), set_desk, dict(tod='eve', ox=lambda u: lerp(250, 230, u),
                                  actors=[('crayon', 430, 560, 1.15, dict(mood='suspicious', look=(-1, 0)))]),
         Z(1.45, 1.6, 300, 360, r0=-3, r1=-3), tin='whip')
    shot(at('N3', "Et il avait"), set_close, dict(who='crayon', tod='eve', s=3.2, y=780, x=CX,
                                                 kw=dict(mood='suspicious', look=(-1, 0)),
                                                 fg=('plume', 40, 2.4)), Z(1.0, 1.25, CX, 250))
    # --- C1 : « Il est jaloux »
    shot(at('C1'), set_close, dict(who='crayon', tod='eve', s=2.5, y=640, x=200,
                                   kw=dict(mood='smug', look=(-1, 0), talk=1)), Z(1.05, 1.0, CX, 300, r0=2, r1=2))
    shot(at('C1', "Jaloux de"), set_glam, {}, Z(1.0, 1.06), tin='flash')
    # --- N4 : la nuit, Lou
    shot(at('N4'), set_room, dict(lamp=lambda u: 0 if u < 0.3 else 1), Z(1.0, 1.2, CX, 380), tin='ink')
    shot(at('N4', "une lettre pour"), set_desk,
         dict(tod='night', ox=lambda u: 120, letter=(310, 600),
              actors=[('plume', 190, 560, 0.95, dict(mood='worried', look=(1, 0.3))),
                      ('crayon', 430, 560, 0.95, dict(mood='worried', look=(-1, 0.3)))]),
         Z(1.1, 1.3, CX, 420))
    # --- N5 : la Plume et la rature
    shot(at('N5'), set_close, dict(who='plume', tod='night', s=2.4, y=lambda: 0, x=CX,
                                   kw=dict(mood='proud', look=(0, -1))), Z(1.0, 1.0), tin='whip')
    S_[-1]['p']['y'] = 620
    S_[-1]['lift'] = True
    shot(at('N5', "Premier mot"), set_page,
         dict(tod='night', k=lambda u: lerp(3.0, 3.4, u), cx=lambda u: 30 + min(u, 0.55) * 120 + 10, cy=LINES_Y[1], sy=330, rot=-6,
              pencil=0, scratch=lambda u: clamp((u - 0.55) * 4), blot=lambda u: clamp((u - 0.75) * 3),
              hand=True,
              tool=lambda u, t: ('plume', 30 + min(u, 0.55) * 120 + (math.sin(t * 30) * 3 if u > 0.55 else 0),
                                 LINES_Y[1] - 2, -24, dict(mood='proud' if u < 0.55 else 'shock', scale=0.42))),
         Z(1.0, 1.08))
    shot(at('N5', "Indélébile"), set_close, dict(who='plume', tod='night', s=3.0, y=700, x=CX,
                                                kw=dict(mood='shock', look=(0, 0.4), stain=1.0, sweat=1)),
         Z(1.0, 1.35, CX, 260), tin='flash', grade='shock', ca=2.5)
    # --- N6 : essais ratés, boules de papier
    for i, w in enumerate(("Deuxième", "Troisième")):
        shot(at('N6', w), set_page,
             dict(tod='night', k=2.2, cx=100, cy=90, sy=300, rot=-5 + i * 7, blot=1.0, blot_at=(60 + i * 60, LINES_Y[1 + i]),
                  scratch=1.0, ghost=0), Z(1.0, 1.06, CX, 300, r0=i * 2, r1=-i), tin='flash' if i else 'cut')
    balls = [(x, 540 + (i % 3) * 14, at('N6', "Les boules") + 0.12 * i, 15 + (i * 7) % 8, i)
             for i, x in enumerate((150, 230, 110, 260, 180, 200, 130, 245, 165, 215))]
    shot(at('N6', "Les boules"), set_desk,
         dict(tod='night', ox=lambda u: 80, balls=balls,
              actors=[('plume', 190, 572, 1.0, dict(mood='ashamed', look=(0, 1), stain=1.0))]),
         Z(1.5, 1.7, 110, 400))
    # --- N7 : Petit Crayon au travail
    shot(at('N7'), set_close, dict(who='crayon', tod='night', s=2.4, y=620, x=CX,
                                   kw=dict(mood='joy', look=(0, -1))), Z(1.0, 1.0), tin='whip')
    S_[-1]['lift'] = True
    common = dict(tod='night', k=3.2, cy=LINES_Y[3], sy=320, rot=-4, hand=True)
    shot(at('N7', "Elle écrit"), set_page,
         dict(common, cx=lambda u: lerp(40, 120, u) + 10, pencil=lambda u: 0.3 + u * 0.06,
              tool=lambda u, t: ('crayon', lerp(40, 120, u), LINES_Y[3] - 2, -26, dict(mood='happy', scale=0.4))),
         Z(1.0, 1.05))
    shot(at('N7', "se trompe"), set_page,
         dict(common, cx=95, pencil=0.36, mistake=0.0,
              tool=lambda u, t: ('crayon', 60 + u * 60, LINES_Y[3] - 2, -26, dict(mood='worried', scale=0.4))),
         Z(1.05, 1.1), tin='cut', grade='shock')
    shot(at('N7', "gomme"), set_page,
         dict(common, cx=95, pencil=0.36, mistake=lambda u: clamp(u * 1.2), crumbs=lambda u: (u * 30, 1), hand=False,
              tool=lambda u, t: ('crayon', 90 + math.sin(t * 26) * 14, LINES_Y[3] - 3, 16,
                                 dict(mood='resolved', scale=0.4, upside=True, eraser=0.9))),
         Z(1.05, 1.12), tin='whip')
    shot(at('N7', "Et recommence"), set_page,
         dict(tod='night', k=lambda u: lerp(1.6, 1.4, u), cx=100, cy=140, sy=330, rot=lambda u: -6 + u * 3,
              pencil=lambda u: 0.36 + u * 0.4, crumbs=lambda u: (30 + u * 40, 1), hand=True,
              tool=lambda u, t: ('crayon', *writer_path(0.36 + u * 0.4), -26, dict(mood='resolved', scale=0.42))),
         Z(1.0, 1.1))
    # --- N8 : la gomme rapetisse
    for i, (w, er) in enumerate((("À chaque", 0.75), ("la magnifique", 0.5), ("rapetisse", 0.28))):
        shot(at('N8', w), set_page,
             dict(tod='night', k=3.4, cx=100, cy=LINES_Y[4], sy=470, rot=-4 + i * 4, pencil=0.6, mistake=lambda u: clamp(u * 1.3),
                  crumbs=(60 + i * 30, 2 + i),
                  tool=lambda u, t, er=er: ('crayon', 100 + math.sin(t * 24) * 12, LINES_Y[4] - 3, 14,
                                            dict(mood='resolved', scale=0.42, upside=True, eraser=er))),
             Z(1.0, 1.05, CX, 330), tin='flash' if i else 'cut')
    shot(at('N8', "Petit Crayon ne"), set_close, dict(who='crayon', tod='night', s=2.6, y=650, x=CX,
                                                     kw=dict(mood='tender', look=(0, 0.5), eraser=0.18, sweat=1)),
         Z(1.0, 1.15, CX, 300))
    # --- N9 : l'encre par-dessus
    shot(at('N9'), set_page,
         dict(tod='night', k=3.0, cx=lambda u: writer_path(0.1 + u * 0.4)[0] + 10, cy=lambda u: writer_path(0.1 + u * 0.4)[1], sy=360, rot=-3,
              pencil=1.0, ink=lambda u: 0.1 + u * 0.4, hand=True,
              tool=lambda u, t: ('plume', *writer_path(0.1 + u * 0.4), -24, dict(mood='tender', scale=0.42))),
         Z(1.0, 1.05), tin='whip')
    shot(at('N9', "Parfait"), set_page,
         dict(tod='night', k=lambda u: lerp(1.9, 1.55, ease(u)), cx=100, cy=140, sy=320, rot=lambda u: -2 + u * 2,
              pencil=1.0, ink=1.0, ghost=1.0), Z(1.0, 1.0), tin='flash')
    # --- N10 : la nuit, la lune
    shot(at('N10'), set_desk, dict(tod='moon', ox=lambda u: lerp(140, 125, u),
                                   actors=[('plume', 190, 560, 0.95, dict(mood='tender', look=(1, 0.4))),
                                           ('crayon', 430, 560, 0.95, dict(mood='neutral', look=(0, 0), eraser=0.18))]),
         Z(1.0, 1.1, CX, 420), tin='ink')
    shot(at('N10', "regarde"), set_monocle, dict(tod='moon', y=1010, kw=dict(mood='neutral', eraser=0.18)), Z(1.05, 1.15))
    # --- P2 : l'aveu
    shot(at('P2'), set_close, dict(who='plume', tod='moon', s=2.5, y=640, x=150, kw=dict(mood='tender', look=(1, 0), talk=1, mono=False),
                                   fg=('crayon', 390, 2.6), fg_er=0.18), Z(1.0, 1.1, CX, 300))
    shot(at('P2', "Pas de"), set_close, dict(who='crayon', tod='moon', s=2.6, y=650, x=210,
                                            kw=dict(mood='shock', look=(-1, 0), eraser=0.18)), Z(1.08, 1.0, CX, 300))
    shot(at('P2', "Du droit"), set_close, dict(who='plume', tod='moon', s=2.9, y=690, x=CX,
                                              kw=dict(mood='sad', look=(0.6, 0.2), talk=1, mono=False)),
         Z(1.05, 1.25, CX, 270))
    # --- C2 : réponse du Crayon
    shot(at('C2'), set_close, dict(who='crayon', tod='moon', s=2.6, y=650, x=CX,
                                   kw=dict(mood='tender', look=(-0.6, 0), eraser=0.18, talk=1)), Z(1.0, 1.1, CX, 300))
    shot(at('C2', "Tout ce"), set_page,
         dict(tod='moon', k=2.6, cx=lambda u: lerp(60, 120, u), cy=LINES_Y[2], sy=330, rot=-5, pencil=0.45,
              ghost=lambda u: ease(u * 1.1)), Z(1.0, 1.12))
    # --- N11 : le lendemain
    shot(at('N11'), set_envelope, {}, Z(1.0, 1.05), tin='ink')
    shot(at('N11', "Personne"), set_bin, {}, Z(1.0, 1.12, CX, 380))
    shot(at('N11', "ni les miettes"), set_crumbs, {}, Z(1.1, 1.0))
    # --- N12 : morale
    shot(at('N12'), set_desk, dict(tod='morning', ox=lambda u: lerp(100, 140, u),
                                   actors=[('plume', 250, 560, 0.95, dict(mood='tender', look=(1, 0), mono=False)),
                                           ('crayon', 400, 560, 0.95, dict(mood='happy', look=(-1, 0), eraser=0.18))]),
         Z(1.3, 1.2, CX, 400), tin='fade')
    shot(at('N12', "Alors use"), set_close, dict(who='crayon', tod='morning', s=2.7, y=660, x=CX,
                                                kw=dict(mood='joy', look=(0, 0), eraser=0.18)),
         Z(1.0, 1.15, CX, 280), tin='whip')
    shot(at('N12', "C'est comme"), set_page,
         dict(tod='morning', k=lambda u: lerp(2.4, 1.9, ease(u)), cx=100, cy=120, sy=330, rot=lambda u: -3 + u * 3,
              final_words=lambda u: (clamp(u * 2.2), clamp(u * 2.2 - 0.6)), hand=True,
              tool=lambda u, t: ('plume', 28 + 144 * clamp(u * 2.2 - 0.6), 120 + 4, -24,
                                 dict(mood='happy', scale=0.4, mono=False))),
         Z(1.0, 1.0))
    for i, s_ in enumerate(S_):
        s_['t1'] = S_[i + 1]['t0'] if i + 1 < len(S_) else DUR
    return S_


SHOTS = build_shots()

# ================================================================ textes à l'écran
GOLD, CREAM, PINK, YEL, SKY = (255, 210, 110), (255, 244, 228), (255, 150, 170), (255, 214, 80), (170, 200, 255)
CAPS = []


def cap(t0, t1, s, y, col=CREAM, scale=3, mode='pop', maxw=320, shadow=(30, 12, 30), hl=None):
    CAPS.append(dict(t0=t0, t1=t1, s=s, y=y, col=col, scale=scale, mode=mode, maxw=maxw, shadow=shadow, hl=hl or YEL))


def build_caps():
    cap(-1, at('N1', "Et c'était") - 0.05, "IL N'A JAMAIS FAIT", TOP, CREAM, 3, 'static')
    cap(-1, at('N1', "Et c'était") - 0.05, "UNE SEULE *FAUTE.*", TOP + 40, CREAM, 4, 'static', hl=GOLD)
    cap(at('N1', "Et c'était"), end('N1', 0.3), "ET C'ÉTAIT ÇA,", TOP, CREAM, 3)
    cap(at('N1', "son problème"), end('N1', 0.3), "SON *PROBLÈME.*", TOP + 40, CREAM, 4, hl=PINK)
    cap(at('N2', off=0.4), at('N2', "Il ne signait"), "MONSIEUR", TOP + 10, GOLD, 3, 'fade')
    cap(at('N2', off=0.7), at('N2', "Il ne signait"), "STYLO-PLUME", TOP + 44, GOLD, 4, 'fade')
    cap(at('N2', "Il ne signait"), at('N2', "Et sur ce"), "IL NE SIGNE QUE *L'IMPORTANT.*", TOP - 10, CREAM, 2, hl=GOLD)
    cap(at('N2', "une seule chose"), end('N2', 0.4), "UNE SEULE CHOSE LE DÉRANGE...", TOP, CREAM, 2)
    cap(at('P1'), at('P1', "Fort"), "« CE PETIT CRAYON, AVEC SA GOMME SUR LA TÊTE... »", TOP, GOLD, 2, 'type', maxw=300)
    cap(at('P1', "Fort"), end('P1', 0.4), "« FORT *RIDICULE.* »", TOP + 10, GOLD, 3, hl=PINK)
    cap(at('N3', off=0.2), at('N3', "Et il avait"), "PETIT CRAYON", TOP + 4, YEL, 4)
    cap(at('N3', "Et il avait"), end('N3', 0.3), "...IL A SA PETITE IDÉE.", TOP, CREAM, 2)
    cap(at('C1'), at('C1', "Jaloux de"), "« IL EST *JALOUX.* »", TOP + 6, YEL, 3, hl=PINK)
    cap(at('C1', "Jaloux de"), end('C1', 0.4), "« DE MA *MAGNIFIQUE*", TOP + 4, CREAM, 3, shadow=(150, 40, 70), hl=YEL)
    cap(at('C1', "magnifique") + 0.2, end('C1', 0.4), "GOMME. »", TOP + 44, CREAM, 4, shadow=(150, 40, 70))
    cap(at('N4', off=0.2), at('N4', "une lettre pour"), "UN SOIR...", TOP, CREAM, 3, 'fade')
    cap(at('N4', "la lettre la plus"), at('N4', "une lettre pour"), "LA LETTRE LA PLUS DURE QUI SOIT", TOP + 40, CREAM, 2, 'fade')
    cap(at('N4', "une lettre pour"), end('N4', 0.4), "UNE LETTRE POUR", TOP, CREAM, 2, 'fade')
    cap(at('N4', "demander pardon"), end('N4', 0.4), "DEMANDER *PARDON.*", TOP + 26, CREAM, 3, hl=PINK)
    cap(at('N5', "Premier"), at('N5', "Indélébile"), "PREMIER MOT...", TOP, CREAM, 2)
    cap(at('N5', "Indélébile"), end('N5', 0.4), "*INDÉLÉBILE.*", TOP + 4, CREAM, 4, hl=PINK)
    cap(at('N6', "Deuxième"), at('N6', "Troisième"), "ESSAI N°2", TOP, CREAM, 3)
    cap(at('N6', "Troisième"), at('N6', "Les boules"), "ESSAI N°3", TOP, CREAM, 3)
    cap(at('N7', "Elle écrit"), at('N7', "se trompe"), "ELLE ÉCRIT,", TOP, CREAM, 3)
    cap(at('N7', "se trompe"), at('N7', "gomme"), "SE *TROMPE,*", TOP, CREAM, 3, hl=PINK)
    cap(at('N7', "gomme"), at('N7', "Et recommence"), "*GOMME.*", TOP, CREAM, 4, hl=(250, 140, 165))
    cap(at('N7', "Et recommence"), end('N7', 0.3), "ET RECOMMENCE.", TOP, CREAM, 3)
    cap(at('N8', "rapetisse"), at('N8', "Petit Crayon ne"), "LA GOMME *RAPETISSE.*", TOP, CREAM, 2, hl=(250, 140, 165))
    cap(at('N8', "Petit Crayon ne"), end('N8', 0.4), "PETIT CRAYON NE DIT RIEN.", TOP, CREAM, 2, 'fade')
    cap(at('N9', "Parfait"), end('N9', 0.5), "*PARFAIT.*", TOP + 4, CREAM, 4, hl=GOLD)
    cap(at('N10', off=0.3), end('N10', 0.3), "CETTE NUIT-LÀ...", TOP, SKY, 3, 'fade')
    cap(at('P2'), at('P2', "Pas de"), "« TU AVAIS RAISON. J'ÉTAIS *JALOUX.* »", TOP, CREAM, 2, 'type', hl=GOLD)
    cap(at('P2', "Pas de"), at('P2', "Du droit"), "« PAS DE TA GOMME... »", TOP, CREAM, 2, 'type')
    cap(at('P2', "Du droit"), end('P2', 0.4), "« DU DROIT DE", TOP, CREAM, 3, 'fade')
    cap(at('P2', "te tromper"), end('P2', 0.4), "*TE TROMPER.* »", TOP + 40, CREAM, 3, 'fade', hl=GOLD)
    cap(at('C2'), at('C2', "Tout ce"), "« ET MOI, DE TOI. »", TOP, YEL, 3, 'type')
    cap(at('C2', "Tout ce"), end('C2', 0.4), "« TOUT CE QUE J'ÉCRIS FINIT PAR *S'EFFACER.* »", TOP, CREAM, 2, 'type', hl=SKY)
    cap(at('N11', off=0.2), at('N11', "Personne"), "LE LENDEMAIN.", TOP, CREAM, 3, 'fade')
    cap(at('N11', "Personne"), at('N11', "ni les miettes"), "PERSONNE N'A VU LES BROUILLONS.", TOP, CREAM, 2, 'fade')
    cap(at('N11', "ni les miettes"), end('N11', 0.4), "NI LES MIETTES.", TOP, CREAM, 3, 'fade')
    cap(at('N12', off=0.1), at('N12', "Alors use"), "MORALE", TOP - 6, GOLD, 3, 'fade')
    cap(at('N12', "ceux qui"), at('N12', "Alors use"), "CEUX QUI SE MOQUENT DE TA GOMME", TOP + 34, CREAM, 2, 'fade')
    cap(at('N12', "n'ont souvent"), at('N12', "Alors use"), "N'ONT SOUVENT JAMAIS EU", TOP + 92, CREAM, 2, 'fade')
    cap(at('N12', "le droit de"), at('N12', "Alors use"), "LE *DROIT DE SE TROMPER.*", TOP + 122, CREAM, 3, 'fade', hl=GOLD)
    cap(at('N12', "Alors use"), at('N12', "C'est comme"), "ALORS *USE-LA.*", TOP + 6, CREAM, 4, hl=(250, 140, 165))
    cap(at('N12', "C'est comme"), DUR, "C'EST COMME ÇA QU'ON ÉCRIT", TOP, CREAM, 2, 'fade')
    cap(at('N12', "ce qui reste"), DUR, "CE QUI *RESTE.*", TOP + 28, CREAM, 3, 'fade', hl=GOLD)


build_caps()


def draw_caps(ui, t):
    act = [c for c in CAPS if c['t0'] <= t < c['t1']]
    if act:
        ymax = max(c['y'] + 12 * c['scale'] * len(layout(c['s'], c['maxw'] // c['scale'])) for c in act)
        a0 = max(clamp((t - min(c['t0'] for c in act)) / 0.3), 0) if min(c['t0'] for c in act) > 0 else 1
        ys = np.arange(H, dtype=np.float32)
        al = np.clip((ymax + 50 - ys) / 60, 0, 1) * 150 * a0
        band = Image.new('RGBA', (W, H), (12, 6, 18, 0))
        band.putalpha(Image.fromarray(np.repeat(al[:, None], W, 1).astype(np.uint8), 'L'))
        ui.alpha_composite(band)
    for c in CAPS:
        if not (c['t0'] <= t < c['t1']):
            continue
        dt = t - c['t0']
        out = clamp((c['t1'] - t) / 0.15)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        y = c['y']
        sc = c['scale']
        reveal = 10 ** 9
        if c['mode'] == 'pop':
            pp = eback(dt / 0.25)
            y += int((1 - min(pp, 1)) * 14)
            if pp > 1.03 and dt < 0.2:
                sc += 0
            a = clamp(dt / 0.08) * out
        elif c['mode'] == 'fade':
            a = clamp(dt / 0.45) * out
        elif c['mode'] == 'type':
            reveal = int(dt * 32)
            a = out
        else:
            a = out
        draw_text(lay, c['s'], CX, int(y), c['col'], scale=sc, maxw=c['maxw'], shadow=c['shadow'], reveal=reveal,
                  hl_color=c['hl'])
        if a < 1:
            lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
        ui.alpha_composite(lay)


# ================================================================ composition
BLACK = Image.new('RGB', (W, H), (0, 0, 0))
YY, XX = np.mgrid[0:H, 0:W]
VIG = Image.fromarray((np.clip((np.sqrt(((XX - CX) / CX) ** 2 + ((YY - H / 2) / (H / 2)) ** 2) - 0.75) * 1.3, 0, 0.5)
                       * 255).astype(np.uint8), 'L')


def cam_at(keys, u):
    for (u0, *a), (u1, *b) in zip(keys, keys[1:]):
        if u <= u1:
            v = ease((u - u0) / max(1e-6, u1 - u0))
            return [lerp(x, y, v) for x, y in zip(a, b)]
    return keys[-1][1:]


def apply_cam(img, z, cx, cy, rot, t, shake=0.0):
    if shake:
        cx += math.sin(t * 13) * shake
        cy += math.cos(t * 11) * shake
    if abs(z - 1) < 0.004 and abs(rot) < 0.05 and abs(cx - CX) < 0.5 and abs(cy - H / 2) < 0.5:
        return img
    zz = z + abs(math.sin(math.radians(rot))) * 0.9
    w, h = W / zz, H / zz
    x0 = clamp(cx - w / 2, 0, W - w)
    y0 = clamp(cy - h / 2, 0, H - h)
    out = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
    if abs(rot) >= 0.05:
        out = out.rotate(rot, resample=Image.BICUBIC)
    return out


def ink_mask(p, seed=0, cx=CX, cy=H / 2):
    """Tache d'encre qui envahit l'écran (p 0..1)."""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    R = p * 820
    rr = random.Random(seed)
    phs = [rr.uniform(0, 6) for _ in range(3)]
    pts = [(cx + math.cos(a) * R * (1 + 0.18 * math.sin(a * 5 + phs[0]) + 0.1 * math.sin(a * 9 + phs[1])),
            cy + math.sin(a) * R * (1 + 0.18 * math.sin(a * 5 + phs[0]) + 0.1 * math.sin(a * 9 + phs[1])))
           for a in np.linspace(0, 6.283, 64)]
    d.polygon(pts, fill=255)
    for i in range(10):
        a = rr.uniform(0, 6.28)
        dd = R * rr.uniform(1.05, 1.4)
        r0 = R * rr.uniform(0.04, 0.1)
        x, y = cx + math.cos(a) * dd, cy + math.sin(a) * dd
        d.ellipse([x - r0, y - r0, x + r0, y + r0], fill=255)
    return m


INK = Image.new('RGB', (W, H), (10, 8, 22))


def grade(img, kind):
    if kind == 'shock':
        a = arr(img)
        g = a.mean(2, keepdims=True)
        a = a * 0.45 + g * 0.55
        a[..., 0] *= 1.12
        return toimg(a)
    return img


def chroma(img, n):
    n = int(n)
    if n <= 0:
        return img
    r, g, b = img.split()
    return Image.merge('RGB', (ImageChops.offset(r, n, 0), g, ImageChops.offset(b, -n, 0)))


def bloom(img, thr=200, k=0.45):
    bright = img.point(lambda v: max(0, v - thr) * 3)
    g = bright.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    return ImageChops.add(img, g.point(lambda v: int(v * k)))


def grain(img, t, amount=3):
    rng = np.random.default_rng(int(t * 8))
    a = np.asarray(img).astype(np.int16)
    n = rng.integers(-amount, amount + 1, size=(H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8), 'RGB')


def shot_at(t):
    for s_ in SHOTS:
        if s_['t0'] <= t < s_['t1']:
            return s_
    return SHOTS[-1]


def render_shot(s_, t):
    u = clamp((t - s_['t0']) / max(1e-3, s_['t1'] - s_['t0']))
    p = s_['p']
    if s_.get('lift'):
        # l'outil est saisi par Lou : il s'envole vers le haut
        lift = eout(clamp((u - 0.45) / 0.4))
        p = dict(p, y=620 - lift * 260)
    img = s_['fn'](t, u, p)
    z, cx, cy, rot = cam_at(s_['cam'], u)
    img = apply_cam(img, z, cx, cy, rot, t, shake=0.0)
    if s_.get('grade'):
        img = grade(img, s_['grade'])
    if s_.get('ca'):
        img = chroma(img, s_['ca'] * (1 - u))
    return img


def frame(t):
    s_ = shot_at(t)
    img = render_shot(s_, t)
    # transitions
    i = SHOTS.index(s_)
    nxt = SHOTS[i + 1] if i + 1 < len(SHOTS) else None
    dt_in = t - s_['t0']
    dt_out = (nxt['t0'] - t) if nxt else 9
    if s_['tin'] == 'ink' and dt_in < 0.3:
        img = Image.composite(INK, img, ink_mask(1 - dt_in / 0.3, i))
    if nxt and nxt['tin'] == 'ink' and dt_out < 0.3:
        img = Image.composite(INK, img, ink_mask(1 - dt_out / 0.3, i + 1))
    for dtt, sign in ((dt_in, -1), (dt_out, 1)):
        tin = s_['tin'] if sign < 0 else (nxt['tin'] if nxt else 'cut')
        if tin == 'whip' and dtt < 0.1:
            pw = 1 - dtt / 0.1
            shift = int(pw * 70) * sign
            sm = img
            for k_ in range(1, 5):
                sm = Image.blend(sm, img.transform(img.size, Image.AFFINE, (1, 0, shift * k_ / 4, 0, 1, 0)), 0.45)
            img = sm
        if tin == 'fade' and dtt < 0.3:
            img = Image.blend(img, BLACK, 0.9 * (1 - dtt / 0.3))
    if s_['tin'] == 'flash' and dt_in < 0.16:
        img = Image.blend(img, Image.new('RGB', (W, H), (255, 250, 240)), 0.7 * (1 - dt_in / 0.16))
    img = bloom(img)
    ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_caps(ui, t)
    img.paste(ui, (0, 0), ui)
    img.paste(BLACK, (0, 0), VIG)
    img = grain(img, t)
    if t > DUR - 1.0:
        img = Image.blend(img, BLACK, clamp((t - (DUR - 1.0)) / 1.0))
    return img


# ================================================================ son
SFX = []


def sfx(t, kind, d=0.3, g=1.0):
    SFX.append((t, kind, d, g))


def build_sfx():
    sfx(0.05, 'scratch', 2.6, 0.5)
    sfx(at('N1', "Et c'était"), 'boom', 1.2, 0.9)
    sfx(at('N1', "son problème"), 'drop', 0.4, 0.7)
    sfx(at('N2'), 'chime', 1.2, 0.5)
    sfx(at('N2', "Il ne signait"), 'scratch', 1.0, 0.5)
    for s_ in SHOTS:
        if s_['fn'] is set_parchment:
            sfx(s_['t0'] + (s_['t1'] - s_['t0']) * 0.68, 'stamp', 0.5, 1.0)
        if s_['tin'] in ('whip',):
            sfx(s_['t0'] - 0.12, 'whoosh', 0.3, 0.55)
        if s_['tin'] == 'ink':
            sfx(s_['t0'] - 0.3, 'swell', 0.6, 0.5)
    sfx(at('P1', "avec sa gomme"), 'ting', 0.6, 0.6)
    sfx(at('P1', "Fort"), 'pluck', 0.3, 0.6)
    sfx(at('C1', "Jaloux de"), 'sparkle', 1.0, 0.7)
    sfx(at('N4') + (at('N4', "une lettre pour") - at('N4')) * 0.3, 'click', 0.1, 1.0)
    sfx(at('N5', "Premier"), 'scratch', 1.0, 0.6)
    sfx(at('N5', "une rature"), 'scribble', 0.4, 0.8)
    sfx(at('N5', "Indélébile"), 'boom', 1.0, 0.9)
    sfx(at('N6', "Deuxième"), 'crumple', 0.5, 0.9)
    sfx(at('N6', "Troisième"), 'crumple', 0.5, 0.9)
    for i in range(10):
        sfx(at('N6', "Les boules") + 0.12 * i, 'thud', 0.15, 0.5)
    sfx(at('N7', "Elle écrit"), 'pencil', 0.8, 0.7)
    sfx(at('N7', "se trompe"), 'pencil', 0.4, 0.7)
    sfx(at('N7', "gomme"), 'rub', 0.7, 0.8)
    sfx(at('N7', "Et recommence"), 'pencil', 1.6, 0.5)
    for w in ("À chaque", "la magnifique", "rapetisse"):
        sfx(at('N8', w), 'rub', 0.5, 0.7)
    sfx(at('N9'), 'scratch', 2.0, 0.5)
    sfx(at('N9', "Parfait"), 'sparkle', 1.0, 0.7)
    sfx(at('C2', "Tout ce"), 'swell', 1.2, 0.35)
    sfx(at('N11') + 0.2, 'paper', 0.3, 0.6)
    sfx(at('N11') + (at('N11', "Personne") - at('N11')) * 0.55, 'whoosh', 0.4, 0.6)
    sfx(at('N12', "Alors use"), 'sparkle', 1.0, 0.5)
    sfx(at('N12', "C'est comme"), 'scratch', 1.6, 0.4)
    sfx(at('N12', "ce qui reste"), 'chime', 2.0, 0.6)


build_sfx()


def synth(n):
    rng = np.random.default_rng(1)
    out = np.zeros(n)

    def add(t, sig, g):
        i = int(t * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(n, i + len(sig))
        if j > i:
            out[i:j] += sig[:j - i] * g

    def lp(x, k):
        return np.convolve(x, np.ones(k) / k, mode='same')

    for t, kind, d, g in SFX:
        ln = int(d * SR)
        tt = np.arange(ln) / SR
        if kind in ('scratch', 'pencil'):
            no = rng.uniform(-1, 1, ln)
            hp = no - lp(no, 6 if kind == 'scratch' else 3)
            am = 0.5 + 0.5 * np.abs(np.sin(tt * (9 if kind == 'scratch' else 14) * np.pi + np.sin(tt * 3) * 2))
            env = np.minimum(1, tt / 0.03) * np.minimum(1, (d - tt) / 0.08)
            add(t, hp * am * env, 0.22 * g)
        elif kind == 'scribble':
            no = rng.uniform(-1, 1, ln)
            am = (np.sin(tt * 2 * np.pi * 18) > 0).astype(float)
            add(t, (no - lp(no, 4)) * am * np.exp(-tt * 3), 0.35 * g)
        elif kind == 'rub':
            no = lp(rng.uniform(-1, 1, ln), 8) * 3
            am = 0.4 + 0.6 * np.abs(np.sin(tt * 2 * np.pi * 7))
            env = np.minimum(1, tt / 0.05) * np.minimum(1, (d - tt) / 0.1)
            add(t, no * am * env, 0.3 * g)
        elif kind == 'boom':
            ph = np.cumsum(np.linspace(90, 30, ln)) / SR
            add(t, np.sin(2 * np.pi * ph) * np.exp(-tt * 3.2), 0.9 * g)
            add(t, lp(rng.uniform(-1, 1, ln), 30) * 3 * np.exp(-tt * 6), 0.3 * g)
        elif kind == 'drop':
            ph = np.cumsum(np.linspace(900, 300, ln)) / SR
            add(t, np.sin(2 * np.pi * ph) * np.exp(-tt * 14), 0.5 * g)
        elif kind == 'stamp':
            ph = np.cumsum(np.linspace(160, 50, ln)) / SR
            add(t, np.sin(2 * np.pi * ph) * np.exp(-tt * 10), 0.9 * g)
            add(t, lp(rng.uniform(-1, 1, ln), 5) * np.exp(-tt * 30), 0.5 * g)
        elif kind == 'whoosh':
            no = lp(rng.uniform(-1, 1, ln), 25) * 4
            add(t, no * np.sin(np.linspace(0, np.pi, ln)) ** 2, 0.35 * g)
        elif kind == 'swell':
            no = lp(rng.uniform(-1, 1, ln), 60) * 6
            add(t, no * np.linspace(0, 1, ln) ** 2, 0.3 * g)
        elif kind == 'crumple':
            no = rng.uniform(-1, 1, ln)
            clicks = (rng.uniform(0, 1, ln) > 0.985).astype(float)
            crack = lp(clicks * rng.uniform(-1, 1, ln), 3) * 6 + (no - lp(no, 3)) * 0.25
            add(t, crack * np.minimum(1, (d - tt) / 0.1), 0.45 * g)
        elif kind == 'thud':
            ph = np.cumsum(np.linspace(220, 90, ln)) / SR
            add(t, np.sin(2 * np.pi * ph) * np.exp(-tt * 30), 0.5 * g)
            add(t, lp(rng.uniform(-1, 1, ln), 4) * np.exp(-tt * 50), 0.25 * g)
        elif kind == 'click':
            ln = int(0.05 * SR)
            add(t, rng.uniform(-1, 1, ln) * np.exp(-np.arange(ln) / SR * 160), 0.7 * g)
            add(t + 0.03, rng.uniform(-1, 1, ln) * np.exp(-np.arange(ln) / SR * 200), 0.4 * g)
        elif kind == 'ting':
            for f, a in ((2637, 1), (3951, 0.5)):
                add(t, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 6), 0.12 * a * g)
        elif kind == 'pluck':
            for f in (330, 247):
                add(t, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9), 0.2 * g)
                t += 0.08
        elif kind in ('sparkle', 'chime'):
            notes = [1568, 1976, 2349, 2637, 3136] if kind == 'sparkle' else [523, 784, 1047, 1319]
            for j, f in enumerate(notes):
                sl = int((d - j * 0.06) * SR)
                if sl <= 0:
                    continue
                st = np.arange(sl) / SR
                add(t + j * (0.06 if kind == 'sparkle' else 0.12),
                    np.sin(2 * np.pi * f * st) * np.exp(-st * (5 if kind == 'sparkle' else 2.2)), 0.08 * g)
        elif kind == 'paper':
            no = rng.uniform(-1, 1, ln)
            add(t, (no - lp(no, 3)) * np.exp(-tt * 12), 0.3 * g)
    return out


def load_voice(n):
    path = os.path.join(HERE, 'audio', 'narration.wav')
    v = np.zeros(n)
    if os.path.exists(path):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                             capture_output=True, check=True).stdout
        src = np.frombuffer(raw, np.int16).astype(float) / 32768
        m = min(n, len(src))
        v[:m] = src[:m] / max(1e-9, np.abs(src).max())
    return v


def render(out):
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            frame(float(ts)).resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(HERE, f'_preview_{ts}.png'))
        return
    n = int(DUR * SR)
    voice = load_voice(n)
    fx = synth(n)
    mix = fx * 0.55 + voice * 1.0
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    wav = os.path.join(HERE, '_audio.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * S}x{H * S}',
           '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', '-c:a', 'aac',
           '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)):
        proc.stdin.write(frame(f / FPS).resize((W * S, H * S), Image.NEAREST).tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print('->', out)


if __name__ == '__main__':
    render(os.path.join(HERE, 'plume_crayon_tiktok.mp4'))
