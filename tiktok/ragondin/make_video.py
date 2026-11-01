"""Vidéo TikTok « Le ragondin compte sur toi » — nouvelle DA, plus riche.

Rendu interne 360x640 (2x plus fin que les autres vidéos), agrandi x3 en
1080x1920. Décors en couches avec parallaxe, dégradés tramés, caméra (zoom et
recadrage), transitions « whip », mots qui rebondissent en rythme avec la voix.
Utilise seulement la police, les bruitages et la narration du moteur commun.
Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit ragondin_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import pixel_engine as pe  # noqa: E402
from pixel_engine import SFX, draw_text, layout, clamp, ease_out_back, ease_io  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, S, FPS, SR = 360, 640, 3, 30, 44100
CX = W // 2
TOP = 96            # sous la barre de recherche TikTok
SAFE_B = 480        # au-dessus de la description

IDS = ['virus', 'vie', 'plancton', 'pigeon', 'humain', 'eux', 'toi', 'action', 'fin']
TXT = dict(zip(IDS, open(os.path.join(HERE, 'texte_narration.txt')).read().strip().split('\n\n')))
# {id: (début, fin)} mesurés sur audio/narration.mp3 (pauses > 0,3 s, alignées sur la longueur du texte)
MEASURED = {
    'virus': (0.0, 5.61), 'vie': (5.99, 9.82), 'plancton': (10.40, 17.58), 'pigeon': (18.13, 23.64),
    'humain': (24.04, 31.00), 'eux': (31.46, 39.51), 'toi': (39.84, 44.75), 'action': (45.07, 51.51),
    'fin': (51.88, 53.30),
}


def estimate(rate=16.5, pause=0.45):
    out, t = {}, 0.05
    for pid in IDS:
        d = len(TXT[pid]) / rate
        out[pid] = (t, t + d)
        t += d + pause
    return out


PH = MEASURED or estimate()
END = PH['fin'][1] + 0.1
DUR = END + 1.6


def at(pid, words):
    a, b = PH[pid]
    return a + (b - a) * TXT[pid].index(words) / len(TXT[pid])


def para(t):
    """Paragraphe en cours (le suivant démarre au milieu de la pause)."""
    cur = IDS[0]
    for i, pid in enumerate(IDS[1:], 1):
        prev = IDS[i - 1]
        if t >= (PH[prev][1] + PH[pid][0]) / 2:
            cur = pid
    return cur


def bounds():
    return [(PH[IDS[i - 1]][1] + PH[IDS[i]][0]) / 2 for i in range(1, len(IDS))]


# ================================================================ outils de dessin
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
_yy, _xx = np.mgrid[0:H, 0:W]
_bay = BAYER[_yy % 4, _xx % 4]
_cache = {}


def gradient(stops, key, h=H, steps=7):
    """Dégradé vertical tramé (ordered dithering), mis en cache."""
    if key in _cache:
        return _cache[key].copy()
    ys = _yy[:h] / (h - 1)
    pos = np.array([p for p, _ in stops])
    cols = np.array([c for _, c in stops], float)
    q = np.floor(ys * steps + _bay[:h]) / steps
    q = np.clip(q, 0, 1)
    out = np.zeros((h, W, 3))
    for k in range(3):
        out[..., k] = np.interp(q, pos, cols[:, k])
    im = Image.fromarray(out.astype(np.uint8), 'RGB')
    _cache[key] = im
    return im.copy()


def mix(a, b, u):
    return tuple(int(a[k] + (b[k] - a[k]) * u) for k in range(3))


def ell(d, cx, cy, rx, ry, fill, outline=None):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline)


UI = {'layer': None}   # les textes vont sur un calque posé APRÈS la caméra (pas zoomés)


def text(img, s, y, col=(255, 241, 232), scale=3, cx=CX, maxw=330, shadow=(20, 10, 30), world=False, **kw):
    target = img if world or UI['layer'] is None else UI['layer']
    draw_text(target, s, cx, y, col, scale=scale, maxw=maxw, shadow=shadow, **kw)


def pop_word(img, s, t, t0, y, col, scale=4, cx=CX, maxw=340, shadow=(30, 10, 40)):
    """Mot qui apparaît en rebondissant (2 tailles successives, effet pixel)."""
    if t < t0:
        return
    p = ease_out_back((t - t0) / 0.28)
    sc = scale + 1 if p > 1.02 else scale
    dy = int((1 - min(p, 1)) * 18)
    text(img, s, y + dy, col, scale=sc, cx=cx, maxw=maxw, shadow=shadow)


def sparkles(img, t, cx, cy, r, n=14, cols=((255, 236, 39), (255, 255, 255), (255, 119, 168))):
    d = ImageDraw.Draw(img)
    for i in range(n):
        a = i * 6.283 / n + t * 0.8
        rr = r + math.sin(t * 3 + i) * 6
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8
        s = 2 if (int(t * 8) + i) % 3 else 3
        c = cols[i % len(cols)]
        d.rectangle([x - s, y, x + s, y], fill=c)
        d.rectangle([x, y - s, x, y + s], fill=c)


# ================================================================ personnages
def ragondin(img, cx, cy, s=1.0, t=0.0, look=1, sunglasses=False, thumb=False):
    """Ragondin albinos : pelage crème, nez rose, yeux rouges, incisives orange."""
    d = ImageDraw.Draw(img)
    bob = math.sin(t * 3) * 2 * s
    cy = cy + bob
    fur, shade, pink = (246, 238, 226), (205, 196, 186), (255, 160, 170)
    # queue
    for k in range(18):
        x = cx - look * (40 + k * 3) * s
        y = cy + (16 + math.sin(k * 0.4 + t * 2) * 3) * s
        ell(d, x, y, 3 * s, 3 * s, pink)
    ell(d, cx, cy + 6 * s, 44 * s, 30 * s, shade)                    # corps ombre
    ell(d, cx, cy, 42 * s, 28 * s, fur)                                # corps
    ell(d, cx + look * 34 * s, cy - 14 * s, 22 * s, 18 * s, fur)      # tête
    ell(d, cx + look * 22 * s, cy - 30 * s, 6 * s, 6 * s, pink)       # oreille
    ell(d, cx + look * 22 * s, cy - 30 * s, 3 * s, 3 * s, (255, 200, 205))
    ell(d, cx + look * 54 * s, cy - 12 * s, 5 * s, 4 * s, pink)       # nez
    # incisives orange (véridique : les ragondins ont les dents orange)
    d.rectangle([cx + look * 48 * s - 3 * s, cy - 4 * s, cx + look * 48 * s + 3 * s, cy + 4 * s], fill=(255, 150, 40))
    if sunglasses:
        d.rectangle([cx + look * 26 * s, cy - 22 * s, cx + look * 50 * s, cy - 14 * s], fill=(15, 15, 25))
        d.rectangle([cx + look * 28 * s, cy - 21 * s, cx + look * 32 * s, cy - 19 * s], fill=(120, 200, 255))
    else:
        ell(d, cx + look * 40 * s, cy - 18 * s, 3.5 * s, 3.5 * s, (220, 30, 50))  # œil rouge
        ell(d, cx + look * 41 * s, cy - 19 * s, 1.2 * s, 1.2 * s, (255, 255, 255))
    # moustaches
    for k in (-1, 0, 1):
        d.line([cx + look * 52 * s, cy - 10 * s, cx + look * 70 * s, cy - 12 * s + k * 5 * s], fill=(255, 255, 255))
    # pattes
    for dx in (-24, 14):
        ell(d, cx + dx * s, cy + 26 * s, 9 * s, 5 * s, pink)
    if thumb:
        x, y = cx + look * 62 * s, cy - 2 * s
        d.line([cx + look * 30 * s, cy + 6 * s, x, y], fill=fur, width=int(8 * s))
        ell(d, x, y, 7 * s, 6 * s, pink)
        d.rectangle([x - 2 * s, y - 16 * s, x + 3 * s, y - 4 * s], fill=pink)


def virus(img, cx, cy, r, t=0.0, col=(120, 220, 90), face=True, shades=False):
    d = ImageDraw.Draw(img)
    rot = t * 0.8
    for i in range(10):
        a = rot + i * 0.628
        x1, y1 = cx + math.cos(a) * r, cy + math.sin(a) * r
        x2, y2 = cx + math.cos(a) * r * 1.45, cy + math.sin(a) * r * 1.45
        d.line([x1, y1, x2, y2], fill=mix(col, (0, 0, 0), 0.3), width=max(1, int(r / 8)))
        ell(d, x2, y2, r * 0.16, r * 0.16, (255, 120, 160))
    ell(d, cx, cy + r * 0.08, r, r, mix(col, (0, 0, 0), 0.3))
    ell(d, cx, cy, r, r, col)
    ell(d, cx - r * 0.35, cy - r * 0.35, r * 0.3, r * 0.22, mix(col, (255, 255, 255), 0.5))
    if face:
        if shades:
            d.rectangle([cx - r * 0.65, cy - r * 0.25, cx + r * 0.65, cy + r * 0.05], fill=(15, 15, 25))
        else:
            for sx in (-1, 1):
                ell(d, cx + sx * r * 0.33, cy - r * 0.1, r * 0.14, r * 0.2, (20, 20, 30))
        d.arc([cx - r * 0.3, cy + r * 0.05, cx + r * 0.3, cy + r * 0.45], 20, 160, fill=(20, 20, 30), width=2)


def pigeon(img, cx, cy, s=1.0, t=0.0, peck=0.0, flying=False, look=1):
    d = ImageDraw.Draw(img)
    grey, dark, neck, neck2 = (150, 155, 170), (100, 104, 120), (80, 150, 120), (140, 90, 170)
    if flying:
        flap = math.sin(t * 22)
        for sgn in (-1, 1):
            d.polygon([(cx, cy - 4 * s), (cx - look * 6 * s, cy - (24 + 14 * flap * sgn) * s),
                       (cx + look * 22 * s, cy - 6 * s)], fill=dark)
    ell(d, cx, cy, 26 * s, 16 * s, grey)
    d.polygon([(cx - look * 22 * s, cy - 4 * s), (cx - look * 42 * s, cy + 2 * s), (cx - look * 22 * s, cy + 8 * s)],
              fill=dark)
    hx = cx + look * (24 + 6 * peck) * s
    hy = cy - (14 - 18 * peck) * s
    ell(d, cx + look * 16 * s, cy - 6 * s, 10 * s, 10 * s, neck if int(t * 3) % 2 else neck2)
    ell(d, hx, hy, 9 * s, 8 * s, grey)
    ell(d, hx + look * 3 * s, hy - 2 * s, 2.2 * s, 2.2 * s, (255, 140, 30))
    d.polygon([(hx + look * 8 * s, hy), (hx + look * 15 * s, hy + 2 * s), (hx + look * 8 * s, hy + 3 * s)],
              fill=(230, 200, 150))
    ell(d, cx - look * 6 * s, cy - 2 * s, 14 * s, 7 * s, dark)
    if not flying:
        for dx in (-5, 5):
            d.line([cx + dx * s, cy + 14 * s, cx + dx * s, cy + 24 * s], fill=(240, 120, 130), width=max(1, int(2 * s)))


def human(img, cx, cy, s=1.0, col=(30, 20, 40), arms_up=0.0):
    d = ImageDraw.Draw(img)
    ell(d, cx, cy - 46 * s, 10 * s, 11 * s, col)
    d.rectangle([cx - 9 * s, cy - 34 * s, cx + 9 * s, cy], fill=col)
    for sgn in (-1, 1):
        sx, sy = cx + sgn * 8 * s, cy - 30 * s
        hx = cx + sgn * (14 + 10 * arms_up) * s
        hy = cy - (2 + 70 * arms_up) * s
        d.line([sx, sy, hx, hy], fill=col, width=int(5 * s))
        d.line([cx + sgn * 5 * s, cy, cx + sgn * 8 * s, cy + 28 * s], fill=col, width=int(6 * s))


def kid(img, cx, cy, t, s=1.0):
    d = ImageDraw.Draw(img)
    run = math.sin(t * 18)
    skin, shirt = (240, 190, 150), (255, 80, 90)
    ell(d, cx, cy - 34 * s, 9 * s, 9 * s, skin)
    d.rectangle([cx - 10 * s, cy - 44 * s, cx + 10 * s, cy - 38 * s], fill=(90, 60, 40))
    d.rectangle([cx - 8 * s, cy - 25 * s, cx + 8 * s, cy - 4 * s], fill=shirt)
    for sgn in (-1, 1):
        d.line([cx, cy - 4 * s, cx + sgn * run * 10 * s, cy + 14 * s], fill=(40, 60, 120), width=int(5 * s))
        d.line([cx, cy - 22 * s, cx - sgn * run * 12 * s, cy - 10 * s], fill=skin, width=int(4 * s))


def phone(img, cx, cy, s=1.0, screen=(60, 100, 200)):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - 30 * s, cy - 56 * s, cx + 30 * s, cy + 56 * s], radius=int(8 * s), fill=(25, 25, 35))
    d.rectangle([cx - 25 * s, cy - 48 * s, cx + 25 * s, cy + 46 * s], fill=screen)


# ================================================================ décors
def sky_marsh(t, dusk=0.0):
    img = gradient([(0, (30, 20, 70)), (0.35, (120, 60, 120)), (0.55, (250, 140, 90)), (0.62, (255, 200, 120)),
                    (1, (40, 30, 60))], 'marsh', steps=9)
    d = ImageDraw.Draw(img)
    ell(d, 300, 215, 20, 20, (255, 240, 210))
    r = random.Random(3)
    for _ in range(40):
        x, y = r.randrange(W), r.randrange(0, 200)
        if (int(t * 2) + x) % 7:
            img.putpixel((x, y), (255, 240, 230))
    # eau + reflets
    d.rectangle([0, 400, W, H], fill=(40, 40, 80))
    for k in range(14):
        y = 410 + k * 16
        off = int(math.sin(t * 1.5 + k) * 20)
        d.line([60 + off, y, 300 + off - k * 8, y], fill=(250, 160, 110) if k < 6 else (90, 80, 130), width=2)
    return img


def reeds(img, t, base, layer=0):
    d = ImageDraw.Draw(img)
    r = random.Random(10 + layer)
    col = [(30, 25, 45), (20, 15, 30)][layer]
    for _ in range(18 if layer == 0 else 12):
        x = r.randrange(-20, W + 20)
        h = r.randrange(60, 160) * (1 + layer * 0.5)
        sway = math.sin(t * 1.4 + x * 0.05) * 6 * (layer + 1)
        d.line([x, base, x + sway, base - h], fill=col, width=3 + layer * 2)
        ell(d, x + sway, base - h, 4 + layer * 2, 12 + layer * 4, (90, 60, 40) if layer == 0 else (60, 40, 30))


def underwater(t):
    img = gradient([(0, (60, 170, 220)), (0.5, (20, 80, 150)), (1, (5, 15, 50))], 'sea', steps=10)
    d = ImageDraw.Draw(img)
    for k in range(5):
        x = int((k * 90 + t * 10) % (W + 120)) - 60
        d.polygon([(x, 0), (x + 30, 0), (x + 120, H), (x + 70, H)], fill=None, outline=(110, 200, 240))
    return img


def city(t):
    img = gradient([(0, (60, 40, 110)), (0.5, (250, 120, 100)), (0.7, (255, 190, 120)), (1, (60, 50, 70))],
                   'city', steps=9)
    d = ImageDraw.Draw(img)
    for layer, (col, base, speed) in enumerate(((90, 60, 110), (60, 40, 80))) if False else enumerate(
            (((110, 70, 120), 380, 4), ((60, 40, 80), 420, 10))):
        r = random.Random(20 + layer)
        x = -((t * speed) % 60) - 30
        while x < W + 60:
            w = r.randrange(30, 70)
            h = r.randrange(80, 220) - layer * 40
            d.rectangle([x, base - h, x + w, base], fill=col)
            for wy in range(base - h + 8, base - 10, 14):
                for wx in range(int(x) + 6, int(x + w) - 6, 12):
                    if r.random() < 0.4:
                        d.rectangle([wx, wy, wx + 5, wy + 6], fill=(255, 220, 120))
            x += w + 4
    d.rectangle([0, 420, W, H], fill=(70, 65, 80))
    d.rectangle([0, 420, W, 426], fill=(120, 115, 130))
    return img


def sunset_hill(t):
    img = gradient([(0, (40, 30, 90)), (0.3, (200, 80, 130)), (0.5, (255, 160, 90)), (0.62, (255, 225, 150)),
                    (1, (255, 225, 150))], 'sunset', steps=10)
    d = ImageDraw.Draw(img)
    ell(d, CX, 330, 70, 70, (255, 240, 190))
    ell(d, CX, 330, 56, 56, (255, 250, 220))
    for k, (col, base, amp) in enumerate((((150, 70, 110), 360, 30), ((90, 40, 90), 400, 24),
                                          ((40, 20, 60), 450, 18))):
        pts = [(0, H)]
        for x in range(0, W + 10, 10):
            pts.append((x, base + math.sin(x * 0.02 + k * 2 + t * 0.2 * (k + 1)) * amp))
        pts.append((W, H))
        d.polygon(pts, fill=col)
    return img


def night_room(t):
    img = gradient([(0, (15, 15, 35)), (1, (35, 25, 55))], 'room', steps=6)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 120, 150, 230], fill=(30, 40, 80))
    d.line([95, 120, 95, 230], fill=(15, 15, 35), width=3)
    d.line([40, 175, 150, 175], fill=(15, 15, 35), width=3)
    for k in range(30):
        x = (k * 37 + int(t * 120)) % 110 + 40
        y = (k * 53 + int(t * 300)) % 110 + 120
        d.line([x, y, x - 2, y + 6], fill=(120, 140, 200))
    return img


def day_sky(t):
    img = gradient([(0, (60, 140, 230)), (0.7, (170, 220, 255)), (1, (220, 245, 255))], 'day', steps=8)
    d = ImageDraw.Draw(img)
    for k in range(4):
        x = (k * 120 + t * 12) % (W + 160) - 80
        y = 140 + k * 60
        for dx, dy, r in ((0, 0, 26), (24, -8, 22), (46, 2, 20), (-22, 4, 18)):
            ell(d, x + dx, y + dy, r, r * 0.7, (255, 255, 255))
    return img


# ================================================================ scènes
def sc_virus(img, t):
    a = PH['virus'][0]
    lt = t - a
    img.paste(sky_marsh(t))
    reeds(img, t, 420, 0)
    ragondin(img, 200, 395, 1.3, t)
    d = ImageDraw.Draw(img)
    for k, (x, y) in enumerate(((110, 425), (126, 430), (98, 432))):
        ell(d, x, y, 7, 5, (110, 70, 40))
    reeds(img, t, 470, 1)
    # loupe : on « zoome » dans la crotte
    z_t = at('virus', "un virus dans")
    if t >= z_t:
        p = ease_io((t - z_t) / 0.8)
        r = int(20 + 120 * p)
        cx, cy = int(112 + (CX - 112) * p), int(428 + (300 - 428) * p)
        lens = gradient([(0, (150, 210, 120)), (1, (60, 120, 70))], 'lens', steps=8)
        dl = ImageDraw.Draw(lens)
        for k in range(20):
            ell(dl, (k * 47) % W, (k * 89 + int(t * 30)) % H, 3, 3, (190, 240, 170))
        virus(lens, cx, cy, int(36 * p) + 4, t)
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        img.paste(lens, (0, 0), m)
        d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], outline=(40, 30, 40), width=8)
        d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], outline=(200, 200, 220), width=3)
    pop_word(img, "TU AURAIS PU ÊTRE", t, a, TOP, (255, 241, 232), scale=3)
    pop_word(img, "UN VIRUS", t, at('virus', "un virus."), TOP + 30, (140, 255, 110), scale=5)
    if t >= at('virus', "dans les crottes"):
        text(img, "DANS LES CROTTES", 470, (255, 241, 232), scale=3)
        text(img, "D'UN RAGONDIN ALBINOS", 498, (255, 200, 205), scale=3)


def sc_vie(img, t):
    img.paste(gradient([(0, (60, 120, 70)), (1, (20, 50, 30))], 'lens2', steps=8))
    d = ImageDraw.Draw(img)
    for k in range(30):
        ell(d, (k * 47) % W, (k * 89 + int(t * 30)) % H, 3, 3, (100, 170, 110))
    virus(img, CX, 300, 60, t)
    a = PH['vie'][0]
    left = max(0, 4 * 3600 - (t - a) * 3600 * 1.1)
    hh, mm, ss = int(left // 3600), int(left % 3600 // 60), int(left % 60)
    text(img, "ESPÉRANCE DE VIE", TOP, (220, 255, 210), scale=2)
    text(img, f"{hh:02d}:{mm:02d}:{ss:02d}", TOP + 22, (255, 255, 255), scale=5)
    ach = at('vie', "Ton plus grand")
    if t >= ach:
        p = ease_out_back((t - ach) / 0.35)
        y = int(560 - 160 * min(p, 1))
        d.rounded_rectangle([20, y, W - 20, y + 74], radius=10, fill=(25, 25, 40), outline=(255, 210, 60), width=4)
        d.rectangle([34, y + 14, 80, y + 60], fill=(255, 210, 60))
        star = [(57, y + 18), (62, y + 32), (76, y + 32), (65, y + 41), (69, y + 55), (57, y + 46), (45, y + 55),
                (49, y + 41), (38, y + 32), (52, y + 32)]
        d.polygon(star, fill=(25, 25, 40))
        text(img, "SUCCÈS DÉBLOQUÉ", y + 12, (255, 210, 60), scale=2, cx=210, maxw=240, shadow=None, world=True)
        if t >= at('vie', "une petite"):
            text(img, "PETITE DIARRHÉE", y + 38, (255, 255, 255), scale=3, cx=210, maxw=260, shadow=None, world=True)
        sparkles(img, t, CX, y + 37, 170, 16)


def sc_plancton(img, t):
    img.paste(underwater(t))
    d = ImageDraw.Draw(img)
    r = random.Random(5)
    for layer in range(3):
        for _ in range(140 + layer * 60):
            x = (r.random() * W + t * (6 + layer * 6)) % W
            y = (r.random() * H - t * (3 + layer * 4)) % H
            c = [(150, 230, 210), (210, 255, 230), (255, 255, 255)][layer]
            s = 1 + layer
            d.rectangle([x, y, x + s, y + s], fill=c)
    # « toi », perdu dans la foule
    me = at('plancton', "Bonne chance")
    if t >= PH['plancton'][0] + 0.8:
        x, y = 228 + math.sin(t * 2) * 6, 330 + math.cos(t * 1.7) * 6
        d.rectangle([x, y, x + 3, y + 3], fill=(255, 236, 39))
        if t >= me:
            d.line([x + 30, y - 40, x + 6, y - 6], fill=(255, 236, 39), width=3)
            text(img, "TOI", y - 66, (255, 236, 39), scale=3, cx=int(x) + 34, world=True)
    pop_word(img, "TU AURAIS PU ÊTRE", t, PH['plancton'][0], TOP, (255, 255, 255), scale=3)
    pop_word(img, "DU PLANCTON", t, at('plancton', "du plancton"), TOP + 30, (150, 255, 230), scale=5)
    if t >= at('plancton', "Dans un seul"):
        lt = clamp((t - at('plancton', "il y a plus")) / 1.0)
        d.rounded_rectangle([24, 400, W - 24, 500], radius=8, fill=(5, 20, 50))
        text(img, "1 LITRE D'EAU DE MER", 410, (200, 240, 255), scale=2, world=True)
        for k, (lab, v, c) in enumerate((("VIRUS", 1.0, (140, 255, 110)), ("HUMAINS", 0.8, (255, 200, 150)))):
            y = 440 + k * 26
            text(img, lab, y, c, scale=2, cx=78, maxw=100, shadow=None, world=True)
            d.rectangle([130, y, 130 + int(190 * v * lt), y + 14], fill=c)


def sc_pigeon(img, t):
    img.paste(city(t))
    d = ImageDraw.Draw(img)
    a = PH['pigeon'][0]
    chase = at('pigeon', "et te faire")
    for k in range(9):
        ell(d, 140 + (k * 37) % 120, 432 + (k * 13) % 8, 3, 2, (230, 180, 100))
    if t < chase + 0.5:
        peck = max(0, math.sin(t * 9)) ** 3
        pigeon(img, 200, 410, 1.6, t, peck=peck)
    else:
        lt = t - chase - 0.5
        pigeon(img, 200 + lt * 140, 410 - lt * 220, 1.6, t, flying=True)
    if t >= chase:
        lt = t - chase
        kid(img, -30 + lt * 160, 440, t, 1.4)
    pop_word(img, "TU AURAIS PU ÊTRE", t, a, TOP, (255, 255, 255), scale=3)
    pop_word(img, "UN PIGEON", t, at('pigeon', "un pigeon"), TOP + 30, (200, 210, 255), scale=5)
    if t >= at('pigeon', "Manger"):
        text(img, "MIETTES DE KEBAB", 470, (255, 220, 150), scale=3)


def sc_humain(img, t):
    img.paste(sunset_hill(t))
    a = PH['humain'][0]
    lt = t - a
    d = ImageDraw.Draw(img)
    human(img, CX, 452, 1.4, arms_up=clamp((t - at('humain', "tu as atterri")) / 0.6))
    if t >= at('humain', "tu as atterri"):
        sparkles(img, t, CX, 390, 90, 20)
    pop_word(img, "MAIS NON.", t, a, TOP, (255, 255, 255), scale=5)
    words = [("RIRE", "rire", (255, 236, 39)), ("AIMER", "aimer", (255, 119, 168)),
             ("LA MUSIQUE", "écouter", (120, 220, 255))]
    if t < at('humain', "et regarder"):
        for k, (lab, key, col) in enumerate(words):
            tw = at('humain', key)
            pop_word(img, lab, t, tw, 170 + k * 36, col, scale=4)
    if t >= at('humain', "et regarder"):
        p = ease_out_back((t - at('humain', "et regarder")) / 0.4)
        phone(img, CX, 290 + (1 - min(p, 1)) * 60, 0.9, screen=(30, 20, 70))
        ragondin(img, CX, 300, 0.32, t)
        text(img, "CETTE VIDÉO", 362, (255, 241, 232), scale=2)


def sc_eux(img, t):
    d = ImageDraw.Draw(img)
    p1, p2, p3 = at('eux', "Le ragondin"), at('eux', "Le pigeon"), at('eux', "Le virus")
    if t < p2:
        img.paste(sunset_hill(t))
        ragondin(img, 120, 450, 1.0, t, look=-1)
        text(img, "LE RAGONDIN", TOP, (255, 255, 255), scale=3)
        text(img, "NE REGARDERA JAMAIS", TOP + 28, (255, 230, 200), scale=2)
        text(img, "UN COUCHER DE SOLEIL", TOP + 48, (255, 230, 200), scale=2)
    elif t < p3:
        img.paste(city(t))
        pigeon(img, 150, 410, 1.6, t, peck=max(0, math.sin(t * 9)) ** 3)
        hx, hy = 250, 330
        for dx in (-10, 10):
            ell(d, hx + dx, hy, 12, 12, (255, 80, 110))
        d.polygon([(hx - 22, hy + 4), (hx + 22, hy + 4), (hx, hy + 30)], fill=(255, 80, 110))
        d.line([hx - 4, hy - 8, hx + 6, hy + 6, hx - 2, hy + 18], fill=(30, 20, 40), width=3)
        text(img, "LE PIGEON", TOP, (255, 255, 255), scale=3)
        text(img, "NE DIRA JAMAIS « JE T'AIME »", TOP + 28, (255, 200, 210), scale=2)
    else:
        img.paste(gradient([(0, (60, 120, 70)), (1, (20, 50, 30))], 'lens2', steps=8))
        virus(img, CX, 300, 70, t, shades=t >= at('eux', "bon, le virus"))
        text(img, "LE VIRUS...", TOP, (255, 255, 255), scale=3)
        if t >= at('eux', "bon, le virus"):
            pop_word(img, "S'EN FICHE", t, at('eux', "s'en fiche"), TOP + 32, (140, 255, 110), scale=4)


def sc_toi(img, t):
    img.paste(night_room(t))
    d = ImageDraw.Draw(img)
    a = PH['toi'][0]
    ok = at('toi', "Et parfois")
    if t < ok:
        img.paste(sunset_hill(t))
        human(img, CX, 452, 1.4, col=(30, 20, 40), arms_up=0.6)
        pop_word(img, "TOI, TU AS TOUT ÇA", t, a, TOP, (255, 255, 255), scale=3)
        sparkles(img, t, CX, 390, 90, 20)
        return
    # silhouette penchée sur son téléphone, nuage de pluie
    human(img, 230, 470, 1.3, col=(10, 10, 20))
    phone(img, 200, 380, 0.55, screen=(80, 120, 220))
    glow = Image.new('RGB', (W, H), (80, 120, 220))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([120, 300, 280, 460], fill=50)
    img.paste(glow, (0, 0), m)
    cx, cy = 230, 300
    for dx, r in ((-24, 20), (0, 26), (26, 20)):
        ell(d, cx + dx, cy, r, r * 0.7, (90, 90, 110))
    for k in range(8):
        x = cx - 30 + k * 9
        y = cy + 18 + (k * 13 + int(t * 200)) % 40
        d.line([x, y, x - 2, y + 6], fill=(140, 170, 230), width=2)
    d.rounded_rectangle([40, 150, W - 40, 220], radius=10, fill=(245, 245, 250))
    text(img, "MESSAGE", 160, (60, 60, 80), scale=2, shadow=None, world=True)
    text(img, "VU À 14:32", 186, (150, 150, 170), scale=3, shadow=None, world=True)
    text(img, "RUMINER...", 520, (180, 190, 230), scale=3)


def sc_action(img, t):
    img.paste(day_sky(t))
    d = ImageDraw.Draw(img)
    a = PH['action'][0]
    items = [("APPELLE QUELQU'UN", "Appelle", (255, 119, 168)), ("MANGE UN BON PLAT", "Mange", (255, 180, 60)),
             ("LÈVE LES YEUX", "Lève", (60, 140, 230))]
    text(img, "AUJOURD'HUI,", TOP, (30, 40, 80), scale=3, shadow=(255, 255, 255))
    text(img, "FAIS UN TRUC QU'AUCUN", TOP + 32, (30, 40, 80), scale=2, shadow=(255, 255, 255))
    text(img, "PIGEON NE FERA JAMAIS", TOP + 52, (30, 40, 80), scale=2, shadow=(255, 255, 255))
    for k, (lab, key, col) in enumerate(items):
        tk = at('action', key)
        if t < tk:
            continue
        p = ease_out_back((t - tk) / 0.35)
        y = 220 + k * 76
        x0 = int(30 + (1 - min(p, 1)) * -300)
        d.rounded_rectangle([x0, y, x0 + 300, y + 60], radius=12, fill=(255, 255, 255), outline=col, width=4)
        d.rectangle([x0 + 14, y + 14, x0 + 46, y + 46], fill=col)
        if t > tk + 0.25:
            d.line([x0 + 20, y + 30, x0 + 28, y + 40, x0 + 42, y + 18], fill=(255, 255, 255), width=5)
        text(img, lab, y + 20, (30, 30, 50), scale=2, cx=x0 + 175, maxw=230, shadow=None)
    if t >= at('action', "Lève"):
        pigeon(img, 300, 170 + math.sin(t * 2) * 6, 0.8, t, flying=True, look=-1)


def sc_fin(img, t):
    img.paste(sky_marsh(t))
    reeds(img, t, 430, 0)
    ragondin(img, CX - 20, 400, 2.0, t, sunglasses=True, thumb=t >= at('fin', "compte"))
    sparkles(img, t, CX, 340, 130, 22)
    a = PH['fin'][0]
    pop_word(img, "LE RAGONDIN", t, a, TOP, (255, 255, 255), scale=4)
    pop_word(img, "COMPTE SUR TOI", t, at('fin', "compte"), TOP + 40, (255, 200, 205), scale=4)


SCENES = {'virus': sc_virus, 'vie': sc_vie, 'plancton': sc_plancton, 'pigeon': sc_pigeon, 'humain': sc_humain,
          'eux': sc_eux, 'toi': sc_toi, 'action': sc_action, 'fin': sc_fin}

# caméra par scène : (zoom début, zoom fin, centre x, centre y)
CAMERA = {'virus': (1.0, 1.08, CX, 380), 'vie': (1.1, 1.0, CX, 320), 'plancton': (1.0, 1.06, 228, 330),
          'pigeon': (1.05, 1.0, CX, 400), 'humain': (1.15, 1.0, CX, 330), 'eux': (1.0, 1.05, CX, 330),
          'toi': (1.0, 1.1, 230, 360), 'action': (1.0, 1.0, CX, 320), 'fin': (1.2, 1.0, CX, 360)}


def camera(img, pid, t):
    z0, z1, cx, cy = CAMERA[pid]
    a, b = PH[pid]
    z = z0 + (z1 - z0) * ease_io((t - a) / max(0.5, b - a))
    if abs(z - 1) < 0.01:
        return img
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.NEAREST, box=(x0, y0, x0 + w, y0 + h))


def vignette():
    r = np.sqrt(((_xx - CX) / CX) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.75) * 1.4 + _bay * 0.15, 0, 0.55)
    return Image.fromarray((a * 255).astype(np.uint8), 'L')


VIGNETTE = vignette()
BLACK = Image.new('RGB', (W, H), (0, 0, 0))


def frame(t):
    pid = para(t)
    img = Image.new('RGB', (W, H))
    UI['layer'] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[pid](img, t)
    img = camera(img, pid, t)
    img.paste(UI['layer'], (0, 0), UI['layer'])
    # transition « whip » autour de chaque changement de paragraphe
    for b in bounds():
        d = t - b
        if -0.12 <= d <= 0.12:
            p = 1 - abs(d) / 0.12
            shift = int(p * 90) * (1 if d < 0 else -1)
            smear = img.copy()
            for k in range(1, 5):
                smear = Image.blend(smear, img.transform(img.size, Image.AFFINE, (1, 0, shift * k / 4, 0, 1, 0)),
                                    0.4)
            img = smear
    img.paste(BLACK, (0, 0), VIGNETTE)
    if t > DUR - 0.5:
        img = Image.blend(img, BLACK, clamp((t - (DUR - 0.5)) / 0.5))
    return img


# ================================================================ audio + rendu
SFX.append((0.0, 'crash', None))
for b in bounds():
    SFX.append((b - 0.1, 'whoosh', None))
SFX.append((at('vie', "Ton plus grand"), 'coin', None))
SFX.append((at('humain', "tu as atterri"), 'sparkle', None))
for key in ("Appelle", "Mange", "Lève"):
    SFX.append((at('action', key), 'place', 14))
SFX.append((at('fin', "compte"), 'sparkle', None))


def render():
    out = os.path.join(HERE, 'ragondin_tiktok.mp4')
    n = int(DUR * SR)
    nar = pe.Narration(os.path.join(HERE, 'audio', 'narration.mp3'), PH, [], END)
    voice = nar.load(n)
    sfx = pe.make_sfx(n, np.random.RandomState(1))
    mix_ = sfx * 0.5 + voice * 1.9
    mix_ /= max(1e-9, np.abs(mix_).max()) / 0.89
    wav = os.path.join(HERE, '_audio.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix_ * 32767).astype(np.int16).tobytes())
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * S}x{H * S}',
           '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
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
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            frame(float(ts)).resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(HERE, f'_preview_{ts}.png'))
    else:
        render()
