"""Vidéo TikTok « La Plume et le Crayon » — fable, DA « livre illustré ».

Bureau en bois à la lumière d'une lampe, Monsieur Stylo-Plume (bleu nuit et
or, monocle) et le petit Crayon (jaune, gomme rose). Caméra par images clés
(zooms et recadrages d'un personnage à l'autre), écriture animée sur la page :
brouillon au crayon, gomme, puis encre. Bloom doux, poussières, grain léger.
Pas de musique.

    python3 make_video.py                 # produit plume_crayon_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import fine_engine as fe  # noqa: E402
from fine_engine import (W, H, CX, TOP, SFX, Story, gradient, ell, text, pop_word, fade_word,  # noqa: E402
                         render, clamp, ease_io, ease_out_back, BLACK, motes)

HERE = os.path.dirname(os.path.abspath(__file__))
IDS = ['bureau', 'plume', 'crayon', 'soir', 'brouillon', 'encre', 'sans', 'lendemain', 'morale']
MEASURED = None  # {id: (début, fin)} mesurés sur audio/narration.mp3
ST = Story(IDS, os.path.join(HERE, 'texte_narration.txt'), MEASURED)
at, start = ST.at, ST.start
DUR = ST.end + 1.8

CREAM = (255, 244, 225)
GOLD = (240, 190, 90)
INKC = (30, 22, 40)
NAVY = (28, 36, 80)
PAPER = (246, 238, 220)

# positions sur le bureau
PLUME_X, CRAYON_X, FLOOR = 110, 250, 470
PAGE = (40, 300, 320, 470)          # rectangle de la page (vue en légère perspective)


# ================================================================ décor
def desk(t, lamp=1.0):
    img = gradient([(0, (40, 25, 30)), (0.45, (90, 55, 45)), (0.62, (120, 75, 55)), (1, (60, 38, 32))],
                   'desk', steps=10)
    d = ImageDraw.Draw(img)
    # mur et étagère floue
    d.rectangle([0, 0, W, 300], fill=(48, 32, 40))
    for k in range(6):
        x = 20 + k * 58
        h = 70 + (k * 37) % 40
        d.rectangle([x, 220 - h, x + 40, 220], fill=(70 + k * 6, 40, 50 + k * 4))
        d.line([x + 4, 220 - h + 8, x + 36, 220 - h + 8], fill=(140, 110, 70))
    d.rectangle([0, 220, W, 228], fill=(80, 50, 40))
    # plateau du bureau en bois
    d.polygon([(0, 300), (W, 300), (W, H), (0, H)], fill=(120, 72, 48))
    rng = random.Random(4)
    for k in range(26):
        y = 304 + k * 13 + rng.randint(-2, 2)
        d.line([0, y, W, y + rng.randint(-3, 3)], fill=(105, 62, 42), width=1)
    d.line([0, 300, W, 300], fill=(150, 95, 62), width=3)
    # lampe (en haut à droite) + halo
    d.line([352, 0, 330, 70], fill=(60, 50, 50), width=4)
    d.polygon([(300, 70), (360, 70), (350, 40), (310, 40)], fill=(40, 90, 70))
    if lamp > 0:
        glow = Image.new('RGB', (W, H), (255, 200, 120))
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).polygon([(305, 70), (355, 70), (380, 640), (0, 640), (40, 380)], fill=int(70 * lamp))
        img.paste(glow, (0, 0), m.filter(ImageFilter.GaussianBlur(30)))
    # encrier
    ell(d, 320, 330, 18, 6, (20, 20, 30))
    d.rectangle([304, 300, 336, 330], fill=(30, 35, 60))
    d.rectangle([310, 292, 330, 300], fill=(60, 60, 70))
    motes(img, t, 50, (255, 235, 190), seed=3, area=(120, 60, 360, 420))
    return img


def page(img, t, writing_draft=0.0, erase=0.0, ink=0.0, perfect=False):
    """La feuille : lignes, brouillon au crayon, rature gommée, encre par-dessus."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = PAGE
    d.polygon([(x0 + 18, y0), (x1 - 18, y0), (x1, y1), (x0, y1)], fill=(60, 40, 30))
    d.polygon([(x0 + 16, y0 - 3), (x1 - 20, y0 - 3), (x1 - 2, y1 - 3), (x0 - 2, y1 - 3)], fill=PAPER)
    for k in range(7):
        y = y0 + 22 + k * 20
        sh = (y - y0) / (y1 - y0) * 16
        d.line([x0 + 30 - sh, y, x1 - 30 + sh, y], fill=(200, 210, 230))
    # écriture : 5 lignes de « gribouillis » cursifs, révélés progressivement
    rng = random.Random(9)
    lines = []
    for k in range(5):
        y = y0 + 18 + k * 20
        sh = (y - y0) / (y1 - y0) * 16
        xs = x0 + 40 - sh
        xe = x1 - 50 + sh - (40 if k == 4 else 0)
        pts = []
        x = xs
        ph = rng.uniform(0, 6)
        while x < xe:
            pts.append((x, y - 3 + math.sin(x * 0.55 + ph) * 3 + math.sin(x * 0.13) * 1.5))
            x += 1.5
        lines.append(pts)
    total = sum(len(p) for p in lines)

    def stroke(prog, col, width, skip_mistake=False):
        n = int(total * prog)
        for k, pts in enumerate(lines):
            if n <= 0:
                break
            seg = pts[:n]
            if len(seg) > 1:
                d.line(seg, fill=col, width=width)
            n -= len(pts)

    stroke(writing_draft, (110, 110, 120), 1)
    # la faute : une rature sur la 3e ligne, gommée ensuite
    if writing_draft > 0.55 and erase < 1:
        mx, my = x0 + 150, y0 + 58
        a = 1 - erase
        col = tuple(int(110 + (246 - 110) * (1 - a)) for _ in range(3))
        for k in range(4):
            d.line([mx - 22, my - 4 + k * 2, mx + 22, my - 8 + k * 2], fill=col, width=2)
    if 0 < erase < 1:
        rng2 = random.Random(int(t * 20))
        for _ in range(10):
            ell(d, x0 + 150 + rng2.uniform(-24, 24), y0 + 66 + rng2.uniform(0, 10), 1.5, 1.2, (230, 150, 160))
    stroke(ink, NAVY, 2)
    if perfect:
        d.line([x1 - 120, y1 - 22, x1 - 60, y1 - 26], fill=NAVY, width=2)   # signature
        ell(d, x1 - 56, y1 - 26, 3, 3, NAVY)


# ================================================================ personnages
def eyes(d, cx, cy, s, look=0.0, mood='neutral', blink=False):
    for sx in (-1, 1):
        ex = cx + sx * 7 * s
        if blink:
            d.line([ex - 4 * s, cy, ex + 4 * s, cy], fill=INKC, width=max(1, int(2 * s)))
            continue
        ell(d, ex, cy, 5 * s, 6 * s, (255, 255, 255))
        ell(d, ex + look * 2.2 * s, cy + 0.5 * s, 2.4 * s, 3 * s, INKC)
        ell(d, ex + look * 2.2 * s - 0.8 * s, cy - 1 * s, 0.9 * s, 0.9 * s, (255, 255, 255))
        if mood == 'grumpy':
            d.line([ex - 6 * s, cy - 9 * s + sx * 2 * s * (-1), ex + 6 * s, cy - 9 * s + sx * 2 * s], fill=INKC,
                   width=max(1, int(2 * s)))
        elif mood == 'proud':
            d.arc([ex - 6 * s, cy - 13 * s, ex + 6 * s, cy - 5 * s], 200, 340, fill=INKC, width=max(1, int(2 * s)))


def mouth(d, cx, cy, s, mood):
    if mood == 'grumpy':
        d.arc([cx - 6 * s, cy, cx + 6 * s, cy + 8 * s], 200, 340, fill=INKC, width=max(1, int(2 * s)))
    elif mood in ('happy', 'proud'):
        d.arc([cx - 7 * s, cy - 6 * s, cx + 7 * s, cy + 4 * s], 20, 160, fill=INKC, width=max(1, int(2 * s)))
    else:
        d.line([cx - 4 * s, cy + 2 * s, cx + 4 * s, cy + 2 * s], fill=INKC, width=max(1, int(2 * s)))


def plume(img, cx, base, s, t, look=0.0, mood='grumpy', tilt=0.0, blink=False):
    """Monsieur Stylo-Plume : corps bleu nuit, bagues dorées, plume, monocle, moustache."""
    layer = Image.new('RGBA', (int(120 * s), int(260 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = layer.size
    mx = w / 2
    # pointe (plume métallique) en bas
    d.polygon([(mx - 11 * s, h - 46 * s), (mx + 11 * s, h - 46 * s), (mx, h - 2 * s)], fill=(200, 175, 110))
    d.line([mx, h - 40 * s, mx, h - 8 * s], fill=(90, 70, 40), width=max(1, int(s)))
    ell(d, mx, h - 30 * s, 2 * s, 2 * s, (90, 70, 40))
    # section et corps
    d.rounded_rectangle([mx - 14 * s, h - 70 * s, mx + 14 * s, h - 44 * s], radius=int(5 * s), fill=(20, 22, 40))
    d.rounded_rectangle([mx - 18 * s, 30 * s, mx + 18 * s, h - 68 * s], radius=int(16 * s), fill=NAVY)
    d.rectangle([mx - 18 * s, 70 * s, mx + 18 * s, 76 * s], fill=GOLD)
    d.rectangle([mx - 18 * s, h - 80 * s, mx + 18 * s, h - 74 * s], fill=GOLD)
    d.rounded_rectangle([mx - 10 * s, 26 * s, mx + 10 * s, 34 * s], radius=int(3 * s), fill=GOLD)
    d.line([mx + 12 * s, 36 * s, mx + 14 * s, 96 * s], fill=GOLD, width=max(1, int(3 * s)))   # agrafe
    d.line([mx - 12 * s, 40 * s, mx - 12 * s, h - 90 * s], fill=(70, 90, 160), width=max(1, int(2 * s)))
    # visage
    fy = 112 * s
    eyes(d, mx, fy, s, look, mood, blink)
    d.ellipse([mx + 1 * s, fy - 8 * s, mx + 15 * s, fy + 6 * s], outline=GOLD, width=max(1, int(1.5 * s)))
    d.line([mx + 15 * s, fy, mx + 18 * s, fy + 26 * s], fill=GOLD, width=1)
    d.arc([mx - 12 * s, fy + 8 * s, mx, fy + 18 * s], 200, 360, fill=(230, 230, 240), width=max(1, int(3 * s)))
    d.arc([mx, fy + 8 * s, mx + 12 * s, fy + 18 * s], 180, 340, fill=(230, 230, 240), width=max(1, int(3 * s)))
    mouth(d, mx, fy + 18 * s, s * 0.8, mood)
    if tilt:
        layer = layer.rotate(tilt, resample=Image.BICUBIC, expand=True)
    img.paste(layer, (int(cx - layer.width / 2), int(base - layer.height)), layer)


def crayon(img, cx, base, s, t, look=0.0, mood='proud', tilt=0.0, blink=False, eraser_scale=1.0):
    """Le petit Crayon : six pans jaunes, virole argentée, gomme rose, mine taillée."""
    layer = Image.new('RGBA', (int(110 * s), int(220 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = layer.size
    mx = w / 2
    d.polygon([(mx - 14 * s, h - 40 * s), (mx + 14 * s, h - 40 * s), (mx, h - 4 * s)], fill=(235, 200, 150))
    d.polygon([(mx - 4 * s, h - 16 * s), (mx + 4 * s, h - 16 * s), (mx, h - 2 * s)], fill=(60, 60, 70))
    d.rectangle([mx - 14 * s, 44 * s, mx + 14 * s, h - 40 * s], fill=(250, 195, 40))
    d.rectangle([mx - 14 * s, 44 * s, mx - 6 * s, h - 40 * s], fill=(255, 215, 80))
    d.rectangle([mx + 7 * s, 44 * s, mx + 14 * s, h - 40 * s], fill=(220, 160, 30))
    d.rectangle([mx - 15 * s, 30 * s, mx + 15 * s, 46 * s], fill=(190, 195, 205))
    for k in range(3):
        d.line([mx - 15 * s, 33 * s + k * 4 * s, mx + 15 * s, 33 * s + k * 4 * s], fill=(150, 155, 170))
    er = 14 * s * eraser_scale
    d.rounded_rectangle([mx - er, 30 * s - 20 * s * eraser_scale, mx + er, 32 * s], radius=int(6 * s),
                        fill=(250, 140, 160))
    d.line([mx - er + 3 * s, 30 * s - 16 * s * eraser_scale, mx - er + 3 * s, 28 * s], fill=(255, 190, 200),
           width=max(1, int(2 * s)))
    upside = abs(tilt) >= 150
    if upside:  # tête en bas pour gommer : on retourne le corps, pas le visage
        layer = layer.rotate(tilt, resample=Image.BICUBIC, expand=True)
        d = ImageDraw.Draw(layer)
        w, h = layer.size
        mx = w / 2
        fy = h - 150 * s
    else:
        fy = 92 * s
    eyes(d, mx, fy, s, look, mood, blink)
    ell(d, mx - 13 * s, fy + 11 * s, 3 * s, 2 * s, (255, 150, 120))
    ell(d, mx + 13 * s, fy + 11 * s, 3 * s, 2 * s, (255, 150, 120))
    mouth(d, mx, fy + 16 * s, s * 0.8, mood)
    if tilt and not upside:
        layer = layer.rotate(tilt, resample=Image.BICUBIC, expand=True)
    img.paste(layer, (int(cx - layer.width / 2), int(base - layer.height)), layer)


def blink_at(t, seed):
    return (t * 0.6 + seed) % 3.2 < 0.12


# ================================================================ caméra par images clés
def keycam(t, keys):
    """keys = [(t, zoom, cx, cy)] : interpolation douce entre images clés."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if t < tb:
            u = ease_io((t - ta) / max(0.01, tb - ta))
            return tuple(a[k] + (b[k] - a[k]) * u for k in range(3))
    return keys[-1][1:]


def apply_cam(img, z, cx, cy):
    if abs(z - 1) < 0.005 and abs(cx - CX) < 1 and abs(cy - H / 2) < 1:
        return img
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


# ================================================================ scènes
def base_scene(t, lamp=1.0):
    return desk(t, lamp)


def sc_bureau(img, t):
    img.paste(base_scene(t))
    page(img, t)
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1, mood='grumpy', blink=blink_at(t, 0))
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1, mood='grumpy', blink=blink_at(t, 1.3))
    a = start('bureau')
    fade_word(img, "LA PLUME", t, a, TOP, CREAM, scale=4, shadow=(60, 30, 20))
    fade_word(img, "ET LE CRAYON", t, a + 0.4, TOP + 44, GOLD, scale=3, shadow=(60, 30, 20))
    if t >= at('bureau', "deux voisins"):
        fade_word(img, "DEUX VOISINS QUI NE POUVAIENT PAS SE VOIR", t, at('bureau', "deux voisins"), TOP + 84, CREAM,
                  scale=2, maxw=320)


def sc_plume(img, t):
    img.paste(base_scene(t))
    page(img, t)
    rid = at('plume', "fort ridicule")
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1 if t > rid - 0.8 else 0, mood='grumpy' if t > rid - 0.8 else 'proud',
          blink=blink_at(t, 0), tilt=4 if t > rid else 0)
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1, mood='neutral', blink=blink_at(t, 1.3))
    a = start('plume')
    fade_word(img, "MONSIEUR STYLO-PLUME", t, a + 0.2, TOP, GOLD, scale=3, shadow=(40, 20, 30))
    for k, (key, lab) in enumerate((("Élégant", "ÉLÉGANT"), ("l'encre", "L'ENCRE NOBLE"), ("la pointe", "LA POINTE FINE"))):
        if t >= at('plume', key) and t < rid - 0.8:
            pop_word(img, lab, t, at('plume', key), 164 + k * 26, CREAM, scale=2, shadow=(40, 20, 30))
    if t >= rid:
        pop_word(img, "« FORT RIDICULE »", t, rid, 172, (255, 160, 170), scale=3, shadow=(40, 20, 30))


def sc_crayon(img, t):
    img.paste(base_scene(t))
    page(img, t)
    jal = at('crayon', "c'était de la jalousie")
    gom = at('crayon', "magnifique gomme")
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1, mood='grumpy', blink=blink_at(t, 0))
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1 if t < gom else 0, mood='grumpy' if t < jal else 'proud',
           blink=blink_at(t, 1.3), eraser_scale=1.0 + 0.25 * clamp((t - gom) / 0.3) * (0.8 + 0.2 * math.sin(t * 8)))
    a = start('crayon')
    fade_word(img, "LE PETIT CRAYON", t, a + 0.2, TOP, (255, 210, 80), scale=3, shadow=(40, 20, 30))
    if t >= jal:
        pop_word(img, "JALOUX !", t, jal, 160, (255, 160, 170), scale=4, shadow=(40, 20, 30))
    if t >= gom:
        pop_word(img, "DE SA MAGNIFIQUE GOMME", t, gom, 205, CREAM, scale=2, shadow=(40, 20, 30))


def sc_soir(img, t):
    a = start('soir')
    lamp = clamp((t - a - 0.3) / 0.4)
    scene = base_scene(t, lamp)
    if lamp < 1:
        scene = Image.blend(Image.new('RGB', (W, H), (10, 8, 20)), scene, 0.35 + 0.65 * lamp)
    img.paste(scene)
    page(img, t)
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1, mood='neutral', blink=blink_at(t, 0))
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1, mood='neutral', blink=blink_at(t, 1.3))
    if t >= at('soir', "Une page"):
        fade_word(img, "UNE PAGE BLANCHE", t, at('soir', "Une page"), TOP, CREAM, scale=3, shadow=(40, 20, 30))
    if t >= at('soir', "Une lettre"):
        fade_word(img, "UNE LETTRE À ÉCRIRE", t, at('soir', "Une lettre"), TOP + 34, GOLD, scale=2,
                  shadow=(40, 20, 30))
    if t >= at('soir', "il va falloir"):
        pop_word(img, "ENSEMBLE", t, at('soir', "il va falloir"), 160, CREAM, scale=4, shadow=(40, 20, 30))


def writer_pos(prog):
    """Position de la pointe qui écrit sur la page (suit les lignes)."""
    x0, y0, x1, y1 = PAGE
    k = min(4, int(prog * 5))
    u = prog * 5 - k
    y = y0 + 18 + k * 20
    sh = (y - y0) / (y1 - y0) * 16
    return x0 + 40 - sh + (x1 - 90 + 2 * sh - (x0 + 40 - sh)) * u, y


def sc_brouillon(img, t):
    a, b = ST.ph['brouillon']
    img.paste(base_scene(t))
    erase_t = at('brouillon', "et sa gomme")
    prog = clamp((t - a) / max(1, erase_t - a)) if t < erase_t else 1.0
    erase = clamp((t - erase_t) / 1.2)
    page(img, t, writing_draft=prog, erase=erase)
    plume(img, 52, FLOOR - 10, 0.8, t, look=1, mood='grumpy', blink=blink_at(t, 0))
    if t < erase_t:
        x, y = writer_pos(prog)
        crayon(img, x + 6, y + 4, 0.75, t, look=0, mood='neutral', tilt=-28, blink=blink_at(t, 1.3))
    else:
        mx, my = PAGE[0] + 150 + math.sin(t * 22) * 12, PAGE[1] + 66
        crayon(img, mx, my + 6, 0.75, t, look=0, mood='happy', tilt=180, blink=False)
    fade_word(img, "LE BROUILLON", t, a + 0.1, TOP, CREAM, scale=3, shadow=(40, 20, 30))
    if t >= at('brouillon', "il se trompe"):
        pop_word(img, "OUPS...", t, at('brouillon', "il se trompe"), 424, (255, 160, 170), scale=3,
                 shadow=(40, 20, 30))
    if t >= erase_t:
        pop_word(img, "LA GOMME !", t, erase_t, 458, (250, 140, 160), scale=3, shadow=(40, 20, 30))


def sc_encre(img, t):
    a, b = ST.ph['encre']
    img.paste(base_scene(t))
    ink_end = at('encre', "Et ce qu'il")
    prog = clamp((t - a) / max(1, ink_end + 1.0 - a))
    page(img, t, writing_draft=1.0, erase=1.0, ink=prog)
    crayon(img, 318, FLOOR - 6, 0.75, t, look=-1, mood='neutral', blink=blink_at(t, 1.3))
    x, y = writer_pos(prog)
    plume(img, x + 8, y + 2, 0.7, t, look=0, mood='proud', tilt=-25, blink=blink_at(t, 0))
    fade_word(img, "L'ENCRE", t, a + 0.1, TOP, GOLD, scale=4, shadow=(40, 20, 30))
    if t >= at('encre', "ne s'efface"):
        pop_word(img, "NE S'EFFACE PLUS", t, at('encre', "ne s'efface"), 450, CREAM, scale=3, shadow=(40, 20, 30))


def sc_sans(img, t):
    img.paste(base_scene(t))
    page(img, t, writing_draft=1.0, erase=1.0, ink=1.0)
    split = at('sans', "Sans la Plume")
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1, mood='neutral' if t < split else 'proud', blink=blink_at(t, 0))
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1, mood='proud' if t < split else 'neutral', blink=blink_at(t, 1.3))
    a = start('sans')
    fade_word(img, "SANS LE CRAYON :", t, a + 0.1, TOP, (255, 210, 80), scale=2, shadow=(40, 20, 30))
    fade_word(img, "PLEINE DE FAUTES", t, a + 0.6, TOP + 24, CREAM, scale=3, shadow=(40, 20, 30))
    if t >= split:
        fade_word(img, "SANS LA PLUME :", t, split, 150, GOLD, scale=2, shadow=(40, 20, 30))
        fade_word(img, "EFFACÉE PAR LE TEMPS", t, split + 0.4, 174, CREAM, scale=3, shadow=(40, 20, 30))


def sc_lendemain(img, t):
    a = start('lendemain')
    scene = base_scene(t)
    morning = Image.new('RGB', (W, H), (255, 230, 200))
    img.paste(Image.blend(scene, morning, 0.12))
    page(img, t, writing_draft=1.0, erase=1.0, ink=1.0, perfect=True)
    parf = at('lendemain', "Mais la lettre")
    # dos à dos, boudeurs... puis un coup d'œil
    plume(img, PLUME_X - 10, FLOOR, 1.0, t, look=-1 if t < parf + 0.8 else 1, mood='grumpy', blink=blink_at(t, 0))
    crayon(img, CRAYON_X + 10, FLOOR, 1.0, t, look=1 if t < parf + 0.8 else -1, mood='grumpy', blink=blink_at(t, 1.3))
    fade_word(img, "LE LENDEMAIN", t, a + 0.1, TOP, CREAM, scale=3, shadow=(40, 20, 30))
    if t >= parf:
        pop_word(img, "PARFAITE", t, at('lendemain', "était parfaite"), 160, GOLD, scale=4, shadow=(40, 20, 30))


def sc_morale(img, t):
    a = start('morale')
    img.paste(base_scene(t))
    page(img, t, writing_draft=1.0, erase=1.0, ink=1.0, perfect=True)
    plume(img, PLUME_X, FLOOR, 1.0, t, look=1, mood='proud', blink=blink_at(t, 0))
    crayon(img, CRAYON_X, FLOOR, 1.0, t, look=-1, mood='happy', blink=blink_at(t, 1.3))
    # carte « morale » façon livre
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    p = ease_out_back(clamp((t - a) / 0.6))
    y0 = int(90 + (1 - min(p, 1)) * 40)
    dl.rounded_rectangle([24, y0, W - 24, y0 + 200], radius=10, fill=(246, 238, 220, 235), outline=(150, 110, 60, 255),
                         width=3)
    dl.rounded_rectangle([32, y0 + 8, W - 32, y0 + 192], radius=8, outline=(200, 160, 90, 255), width=1)
    fe.UI['layer'].alpha_composite(layer)
    text(img, "MORALE", y0 + 16, (140, 90, 40), scale=3, shadow=None)
    if t >= at('morale', "on ne demande"):
        fade_word(img, "ON NE DEMANDE PAS AUX AUTRES DE NOUS RESSEMBLER.", t, at('morale', "on ne demande"), y0 + 60,
                  INKC, scale=2, maxw=280, shadow=None)
    if t >= at('morale', "On leur demande"):
        fade_word(img, "ON LEUR DEMANDE D'ÉCRIRE LA MÊME HISTOIRE.", t, at('morale', "On leur demande"), y0 + 124,
                  (150, 60, 50), scale=2, maxw=280, shadow=None)


SCENES = {'bureau': sc_bureau, 'plume': sc_plume, 'crayon': sc_crayon, 'soir': sc_soir, 'brouillon': sc_brouillon,
          'encre': sc_encre, 'sans': sc_sans, 'lendemain': sc_lendemain, 'morale': sc_morale}


def cam_keys(pid):
    a, b = ST.ph[pid]
    m = (a + b) / 2
    return {
        'bureau': [(a, 1.35, CX, 330), (b, 1.0, CX, 320)],
        'plume': [(a, 1.0, CX, 320), (a + 0.8, 1.6, PLUME_X, 300), (at('plume', "Et il") - 0.2, 1.6, PLUME_X, 300),
                  (at('plume', "Et il") + 0.4, 1.35, 180, 320), (b, 1.4, 190, 320)],
        'crayon': [(a, 1.4, 190, 320), (a + 0.8, 1.6, CRAYON_X, 300), (at('crayon', "magnifique") - 0.2, 1.6,
                                                                       CRAYON_X, 300),
                   (at('crayon', "magnifique") + 0.2, 2.2, CRAYON_X, 235), (b, 2.2, CRAYON_X, 235)],
        'soir': [(a, 1.0, CX, 300), (b, 1.25, CX, 330)],
        'brouillon': [(a, 1.5, 160, 380), (b, 1.7, 190, 380)],
        'encre': [(a, 1.6, 140, 380), (b, 1.6, 220, 380)],
        'sans': [(a, 1.2, CX, 330), (m, 1.25, CX, 330), (b, 1.2, CX, 330)],
        'lendemain': [(a, 1.0, CX, 320), (b, 1.3, CX, 400)],
        'morale': [(a, 1.0, CX, 320), (b, 1.0, CX, 320)],
    }[pid]


def bloom(img, strength=0.5):
    bright = img.point(lambda v: max(0, v - 190) * 3)
    g = bright.resize((W // 3, H // 3), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H),
                                                                                                 Image.BILINEAR)
    return ImageChops.add(img, Image.eval(g, lambda v: int(v * strength)))


def frame(t):
    pid = ST.para(t)
    img = Image.new('RGB', (W, H))
    fe.UI['layer'] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[pid](img, t)
    img = apply_cam(img, *keycam(t, cam_keys(pid)))
    img = bloom(img)
    img.paste(fe.UI['layer'], (0, 0), fe.UI['layer'])
    for bd in ST.bounds():
        dd = t - bd
        if -0.2 <= dd <= 0.2:
            img = Image.blend(img, BLACK, 0.6 * (1 - abs(dd) / 0.2))
    img.paste(BLACK, (0, 0), fe.VIGNETTE)
    img = fe.grain(img, t, amount=3)
    if t > DUR - 0.7:
        img = Image.blend(img, BLACK, clamp((t - (DUR - 0.7)) / 0.7))
    return img


SFX.append((at('plume', "fort ridicule"), 'place', 2))
SFX.append((at('crayon', "c'était de la jalousie"), 'place', 14))
SFX.append((at('crayon', "magnifique"), 'sparkle', None))
SFX.append((start('soir') + 0.3, 'place', 6))
SFX.append((at('brouillon', "il se trompe"), 'place', 0))
SFX.append((at('lendemain', "était parfaite"), 'sparkle', None))
SFX.append((start('morale'), 'coin', None))

if __name__ == '__main__':
    render(os.path.join(HERE, 'plume_crayon_tiktok.mp4'), DUR, frame,
           os.path.join(HERE, 'audio', 'narration.mp3'), ST.ph, ST.end)
