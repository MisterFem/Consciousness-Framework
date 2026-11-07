"""Vidéo TikTok « Utopiste ? · Le nucléaire » — la sortie du nucléaire selon LFI.

Structure de la série Utopiste (ouverture choc, Sceptique, proposition, raisons,
objection, réponse, verdict), nouvelle DA : grand paysage panoramique au
crépuscule (tours de refroidissement, éoliennes, mer) parcouru en travelling,
lueurs (bloom), illustrations détaillées en 360x640 agrandies x3.

Faits (à vérifier avant publication) : programme L'Avenir en commun, sortie du
nucléaire et 100 % renouvelables « en 2060 au plus tard » (édition 2026, 2050
en 2022) ; Flamanville 3 : 3,3 Md€ prévus, 23,7 Md€ (€ 2023) selon la Cour des
comptes, 12 ans de retard ; dernière mine d'uranium française fermée en 2001 ;
RTE, Futurs énergétiques 2050 : scénarios sans nouveau nucléaire possibles mais
plus coûteux. Pas de musique.

    python3 make_video.py                 # produit nucleaire_tiktok.mp4
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
                         render, clamp, ease_io, ease_out_back, BLACK, BAYER, draw_text)

HERE = os.path.dirname(os.path.abspath(__file__))
IDS = ['flam', 'scep1', 'intro', 'plan', 'cout', 'uranium', 'dechets', 'scep2', 'reponse', 'rte', 'verdict',
       'cta']
MEASURED = None  # {id: (début, fin)} mesurés sur audio/narration.mp3
ST = Story(IDS, os.path.join(HERE, 'texte_narration.txt'), MEASURED)
at, start = ST.at, ST.start
DUR = ST.end + 1.6

CREAM = (255, 244, 225)
GOLD = (255, 205, 110)
CYAN = (110, 220, 255)
GREEN = (120, 240, 150)
RED = (255, 70, 90)
STAMP = (235, 45, 65)
INKC = (25, 18, 35)

# ================================================================ panorama
PW = 1080                                   # largeur du monde (3 écrans)
_py, _px = np.mgrid[0:H, 0:PW]
_pbay = BAYER[_py % 4, _px % 4]
_pcache = {}


def pano_sky(key, stops, steps=12):
    if key not in _pcache:
        pos = np.array([p for p, _ in stops])
        cols = np.array([c for _, c in stops], float)
        q = np.clip(np.floor(_py / (H - 1) * steps + _pbay) / steps, 0, 1)
        out = np.stack([np.interp(q, pos, cols[:, k]) for k in range(3)], -1)
        _pcache[key] = Image.fromarray(out.astype(np.uint8), 'RGB')
    return _pcache[key].copy()


DUSK = [(0, (25, 18, 60)), (0.35, (110, 50, 110)), (0.52, (240, 120, 100)), (0.6, (255, 190, 130)),
        (0.66, (255, 220, 170)), (1, (60, 40, 70))]
NIGHT = [(0, (5, 6, 20)), (0.5, (15, 18, 45)), (0.66, (30, 30, 60)), (1, (10, 10, 25))]


def tower(d, x, base, h, w, col, rim):
    """Tour de refroidissement (hyperboloïde)."""
    top_w, waist = w * 0.62, w * 0.5
    pts = []
    for k in range(21):
        u = k / 20
        half = w / 2 * (1 - u) + top_w / 2 * u - (w / 2 - waist / 2) * math.sin(u * math.pi) * 0.9
        pts.append((x - half, base - h * u))
    right = [(2 * x - px, py) for px, py in reversed(pts)]
    d.polygon(pts + right, fill=col)
    d.line(pts, fill=rim, width=2)


def steam(img, x, top, t, scale=0.55, alpha=1.0, col=(190, 140, 160)):
    d = ImageDraw.Draw(img)
    for k in range(7):
        u = ((t * 0.12 + k / 7) % 1)
        y = top - u * 160 * scale
        r = (14 + u * 40) * scale
        dx = math.sin(u * 4 + k) * 14 * scale + u * 40 * scale
        c = tuple(int(cc * (1 - u * 0.45) * alpha) for cc in col)
        ell(d, x + dx, y, r, r * 0.8, c)


def turbine(img, x, base, h, t, col=(235, 235, 245), speed=1.0, phase=0.0):
    d = ImageDraw.Draw(img)
    d.polygon([(x - 3, base), (x + 3, base), (x + 1.5, base - h), (x - 1.5, base - h)], fill=col)
    a0 = t * speed * 2 + phase
    for k in range(3):
        a = a0 + k * 2.094
        L = h * 0.45
        tip = (x + math.cos(a) * L, base - h + math.sin(a) * L)
        side = (x + math.cos(a + 0.12) * L * 0.25, base - h + math.sin(a + 0.12) * L * 0.25)
        d.polygon([(x, base - h), side, tip], fill=col)
    ell(d, x, base - h, 4, 4, col)


def world(t, mode):
    """Le grand paysage. mode : 'nuc' (centrales), 'mix' (transition), 'enr' (renouvelables)."""
    img = pano_sky('dusk', DUSK)
    d = ImageDraw.Draw(img)
    ell(d, 560, 395, 46, 46, (255, 235, 190))
    ell(d, 560, 395, 36, 36, (255, 248, 220))
    rng = random.Random(1)
    for _ in range(90):
        x, y = rng.randrange(PW), rng.randrange(0, 200)
        img.putpixel((x, y), (255, 240, 230) if rng.random() < 0.7 else (200, 190, 255))
    # montagnes lointaines
    for k, (col, base, amp, f) in enumerate((((150, 70, 110), 400, 28, 0.008), ((110, 50, 95), 425, 22, 0.013))):
        pts = [(0, H)] + [(x, base + math.sin(x * f + k) * amp + math.sin(x * f * 2.7) * amp * 0.3)
                          for x in range(0, PW + 8, 8)] + [(PW, H)]
        d.polygon(pts, fill=col)
    # mer à droite, rivière au milieu
    d.rectangle([760, 430, PW, H], fill=(60, 50, 100))
    for k in range(12):
        y = 438 + k * 14
        off = int(math.sin(t * 1.2 + k) * 14)
        d.line([780 + off, y, PW - 20 + off, y], fill=(250, 170, 120) if k < 5 else (100, 90, 150), width=2)
    nuc_a = {'nuc': 1.0, 'mix': 0.55, 'enr': 0.0}[mode]
    enr_a = {'nuc': 0.25, 'mix': 0.7, 'enr': 1.0}[mode]
    # centrales (gauche)
    if nuc_a > 0:
        for k, (x, h, w) in enumerate(((120, 150, 92), (240, 175, 104), (360, 140, 86))):
            col = tuple(int(c * (0.4 + 0.6 * nuc_a)) for c in (90, 80, 105))
            tower(d, x, 470, h, w, col, (200, 150, 150))
            if nuc_a > 0.3:
                steam(img, x + 4, 470 - h, t + k * 2.3, 0.55, nuc_a)
        d.rectangle([150, 440, 330, 470], fill=(70, 60, 85))
    # éoliennes (droite) et panneaux solaires
    nturb = int(3 + 9 * enr_a)
    for k in range(nturb):
        x = 520 + k * 46
        base = 470 if x < 760 else 450 + (k % 2) * 6
        turbine(img, x, base, 110 - (k % 3) * 14, t, speed=1.0, phase=k * 0.7)
    for k in range(int(10 * enr_a)):
        x = 420 + k * 30
        d.polygon([(x, 488), (x + 24, 488), (x + 30, 500), (x + 6, 500)], fill=(40, 70, 130))
        d.line([x + 2, 490, x + 26, 490], fill=(140, 200, 255))
    # sol
    d.rectangle([0, 470, 760, H], fill=(40, 25, 50))
    return img


def pan(img_world, x0):
    x0 = int(min(max(x0, 0), PW - W))
    return img_world.crop((x0, 0, x0 + W, H))


# ================================================================ personnages et objets
def sceptic(img, x, y, s=1.0, t=0.0, talking=False):
    """Le Sceptique, version fine : bras croisés, sourcil levé."""
    d = ImageDraw.Draw(img)
    skin, hair, coat = (205, 160, 125), (90, 60, 40), (110, 115, 140)
    bob = math.sin(t * 3) * 1.5
    y = y + bob
    d.rounded_rectangle([x - 26 * s, y - 10 * s, x + 26 * s, y + 70 * s], radius=int(12 * s), fill=coat)
    d.rounded_rectangle([x - 30 * s, y + 10 * s, x + 30 * s, y + 26 * s], radius=int(8 * s), fill=(100, 105, 130))
    ell(d, x - 18 * s, y + 18 * s, 7 * s, 7 * s, skin)
    ell(d, x + 18 * s, y + 18 * s, 7 * s, 7 * s, skin)
    d.rectangle([x - 18 * s, y + 70 * s, x - 6 * s, y + 96 * s], fill=(50, 50, 80))
    d.rectangle([x + 6 * s, y + 70 * s, x + 18 * s, y + 96 * s], fill=(50, 50, 80))
    ell(d, x, y - 34 * s, 22 * s, 24 * s, skin)
    d.chord([x - 23 * s, y - 62 * s, x + 23 * s, y - 24 * s], 180, 360, fill=hair)
    for sx in (-1, 1):
        ell(d, x + sx * 8 * s, y - 34 * s, 3 * s, 3.5 * s, INKC)
    d.line([x - 14 * s, y - 44 * s, x - 3 * s, y - 42 * s], fill=hair, width=int(3 * s))
    d.line([x + 3 * s, y - 46 * s, x + 14 * s, y - 49 * s], fill=hair, width=int(3 * s))
    mo = (3 + 3 * abs(math.sin(t * 14))) * s if talking else 1.5 * s
    d.ellipse([x - 7 * s, y - 22 * s - mo / 2, x + 7 * s, y - 22 * s + mo / 2], fill=(140, 60, 70))


def bubble(img, x0, y0, w, txt, scale=2):
    img = fe.UI['layer']
    d = ImageDraw.Draw(img)
    lines = len(layout_lines(txt, (w - 16) // scale))
    h = lines * 12 * scale + 16
    d.rounded_rectangle([x0 + 3, y0 + 3, x0 + w + 3, y0 + h + 3], radius=12, fill=(10, 8, 20))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=12, fill=(250, 248, 240))
    d.polygon([(x0 + w - 60, y0 + h), (x0 + w - 36, y0 + h), (x0 + w - 30, y0 + h + 18)], fill=(250, 248, 240))
    draw_text(img, txt, x0 + w // 2, y0 + 8, INKC, scale=scale, maxw=w - 16, shadow=None, hl_color=STAMP)
    return h


def layout_lines(txt, maxw):
    return fe.layout(txt.upper(), maxw)


def stamp(img, label, cx, cy, t, t0, col=STAMP, scale=3, angle=-7):
    if t < t0:
        return
    sc = scale + 1 if t - t0 < 0.12 else scale
    w = max(wd for _, wd in fe.layout(label.upper(), 600)) * sc + 18
    h = 12 * sc + 10
    layer = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle([2, 2, w + 5, h + 5], outline=col + (255,), width=3)
    tmp = Image.new('RGB', (w + 8, h + 8))
    draw_text(tmp, label, (w + 8) // 2, 7, (255, 255, 255), scale=sc, maxw=900, shadow=None)
    layer.paste(col + (255,), (0, 0), tmp.convert('L').point(lambda v: 255 if v > 128 else 0))
    layer = layer.rotate(angle, resample=Image.NEAREST, expand=True)
    fe.UI['layer'].alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def tag(img):
    text(img, "UTOPISTE ? · LE NUCLÉAIRE", 78, CYAN, scale=2)


def panel(img, y0, y1, x0=18, x1=W - 18, a=200):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(12, 8, 26, a))
    fe.UI['layer'].alpha_composite(layer)


# ================================================================ scènes
def sc_flam(img, t):
    a = start('flam')
    # travelling avant lent sur la centrale de Flamanville au bord de la mer
    w = world(t, 'nuc')
    img.paste(pan(w, 60 + (t - a) * 6))
    pop_word(img, "FLAMANVILLE", t, a, TOP, CREAM, scale=4)
    b1, b2, b3 = at('flam', "Budget"), at('flam', "Facture"), at('flam', "Et douze")
    if t >= b1:
        panel(img, 400, 520)
        text(img, "PRÉVU (EUROS)", 412, (200, 200, 230), scale=2, cx=96, maxw=150)
        pop_word(img, "3 MDS", t, b1 + 0.4, 434, GREEN, scale=4, cx=96, maxw=150)
    if t >= b2:
        text(img, "FACTURE", 412, (255, 200, 200), scale=2, cx=262)
        p = clamp((t - b2 - 0.3) / 1.2)
        text(img, f"{3 + 20.7 * ease_io(p):.1f} MDS".replace('.', ','), 434, RED, scale=4, cx=262, maxw=170)
    if t >= b3:
        pop_word(img, "+ 12 ANS DE RETARD", t, b3, 486, GOLD, scale=2)
        text(img, "COUR DES COMPTES, 2025", 538, (170, 170, 200), scale=1)


def sc_scep1(img, t):
    img.paste(pan(world(t, 'nuc'), 200))
    veil = Image.new('RGB', (W, H), (10, 8, 25))
    img.paste(Image.blend(img, veil, 0.55))
    sceptic(img, 250, 360, 1.5, t, talking=True)
    bubble(img, 22, 120, 316, "C'EST BIEN BEAU... MAIS SANS NUCLÉAIRE, *ON S'ÉCLAIRE À LA BOUGIE* !")
    d = ImageDraw.Draw(img)
    fl = 1 + math.sin(t * 9) * 0.15
    d.rectangle([84, 430, 100, 480], fill=(245, 240, 225))
    ell(d, 92, 420, 6, 11 * fl, (255, 200, 90))
    text(img, "LE SCEPTIQUE", 520, (180, 185, 210), scale=2, cx=250)


def sc_intro(img, t):
    a = start('intro')
    img.paste(pan(world(t, 'nuc'), 240 + (t - a) * 12))
    tag(img)
    panel(img, 100, 236)
    fade_word(img, "LA PROPOSITION DE", t, a + 0.2, 116, (200, 200, 230), scale=2)
    fade_word(img, "JEAN-LUC MÉLENCHON", t, a + 0.5, 140, CREAM, scale=3)
    fade_word(img, "ET DE LA FRANCE INSOUMISE", t, a + 0.8, 172, (200, 200, 230), scale=2)
    if t >= at('intro', "sortir du"):
        pop_word(img, "SORTIR DU NUCLÉAIRE", t, at('intro', "sortir du"), 196, GOLD, scale=3)
    if t >= at('intro', "Alors on"):
        stamp(img, "ON VÉRIFIE", CX, 540, t, at('intro', "Alors on"), col=CYAN, scale=3)


def sc_plan(img, t):
    a, b = ST.ph['plan']
    # LE travelling : des centrales vers les éoliennes, pendant que la timeline avance jusqu'à 2060
    p = ease_io(clamp((t - a) / (b - a)))
    mode = 'nuc' if p < 0.33 else ('mix' if p < 0.7 else 'enr')
    img.paste(pan(world(t, mode), 40 + p * (PW - W - 40)))
    tag(img)
    items = [("Leur plan", "PAS DE NOUVEAU RÉACTEUR"), ("fermer les", "FERMER LES ANCIENS PEU À PEU"),
             ("passer à", "100 % RENOUVELABLES")]
    panel(img, 100, 100 + 34 * len([1 for k, _ in items if t >= at('plan', k)]) + 10)
    for k, (key, lab) in enumerate(items):
        if t >= at('plan', key):
            pop_word(img, "✓ " + lab, t, at('plan', key), 112 + k * 34, CREAM if k < 2 else GREEN, scale=2)
    # frise
    y = 540
    d = ImageDraw.Draw(img)
    d.line([40, y, 320, y], fill=(200, 200, 230), width=2)
    for k, yr in enumerate(("2026", "2040", "2060")):
        x = 40 + k * 140
        d.line([x, y - 6, x, y + 6], fill=(200, 200, 230), width=2)
        text(img, yr, y + 10, (200, 200, 230), scale=2, cx=x, maxw=80)
    x = 40 + 280 * p
    ell(d, x, y, 7, 7, GOLD)
    if t >= at('plan', "d'ici 2060"):
        pop_word(img, "2060 AU PLUS TARD", t, at('plan', "d'ici 2060"), 496, GOLD, scale=3)


def sc_cout(img, t):
    a = start('cout')
    img.paste(gradient([(0, (20, 14, 40)), (1, (45, 25, 50))], 'cout', steps=8))
    d = ImageDraw.Draw(img)
    tag(img)
    pop_word(img, "1 · LE COÛT", t, a, TOP + 10, GOLD, scale=4)
    # deux barres : prévu vs réel, qui monte et crève le plafond
    base = 470
    d.rectangle([70, base - 26, 140, base], fill=GREEN)
    text(img, "PRÉVU", base + 8, GREEN, scale=2, cx=105, world=True)
    p = clamp((t - at('cout', "explosent")) / 1.5) if t >= at('cout', "explosent") else 0
    h = int(26 + 200 * ease_io(p))
    d.rectangle([220, base - h, 290, base], fill=RED)
    text(img, "RÉEL", base + 8, RED, scale=2, cx=255, world=True)
    if p >= 1:
        for k in range(6):
            ang = k * 1.05 + t
            d.line([255, base - h, 255 + math.cos(ang) * 22, base - h + math.sin(ang) * 22], fill=GOLD, width=2)
    if t >= at('cout', "La Cour"):
        panel(img, 520, 560)
        text(img, "RENTABILITÉ « MÉDIOCRE »", 532, CREAM, scale=2)
        stamp(img, "COUR DES COMPTES", 110, 360, t, at('cout', "La Cour"), col=STAMP, scale=2, angle=-8)


URANIUM = [("KAZAKHSTAN", (258, 214)), ("OUZBÉKISTAN", (240, 238)), ("NIGER", (168, 290))]


def sc_uranium(img, t):
    a = start('uranium')
    img.paste(pano_sky('night', NIGHT).crop((0, 0, W, H)))
    d = ImageDraw.Draw(img)
    tag(img)
    pop_word(img, "2 · LA DÉPENDANCE", t, a, TOP + 10, GOLD, scale=3)
    # carte stylisée en points (Europe, Afrique, Asie centrale)
    rng = random.Random(8)
    blobs = [(150, 200, 40, 28), (180, 300, 46, 70), (260, 220, 70, 34)]
    for bx, by, rx, ry in blobs:
        for _ in range(260):
            ang, r = rng.uniform(0, 6.28), rng.random() ** 0.5
            x, y = bx + math.cos(ang) * rx * r, by + math.sin(ang) * ry * r
            d.rectangle([x, y, x + 1, y + 1], fill=(60, 80, 130))
    fx, fy = 132, 196
    ell(d, fx, fy, 5, 5, CYAN)
    text(img, "FRANCE", fy - 24, CYAN, scale=2, cx=fx, world=True)
    if t >= at('uranium', "La France"):
        stamp(img, "0 MINE DEPUIS 2001", CX, 410, t, at('uranium', "depuis 2001"), col=STAMP, scale=2)
    for k, (name, (x, y)) in enumerate(URANIUM):
        tk = at('uranium', name.capitalize()[:4]) if name != "OUZBÉKISTAN" else at('uranium', "l'Ouzbékistan")
        if t < tk:
            continue
        p = clamp((t - tk) / 0.8)
        mx, my = fx + (x - fx) * p, fy + (y - fy) * p
        d.line([x, y, mx, my], fill=GOLD, width=2)
        ell(d, x, y, 5, 5, GOLD)
        text(img, name, y + 10, GOLD, scale=1, cx=x, world=True, maxw=120)
        u = (t * 0.6 + k * 0.3) % 1
        ell(d, x + (fx - x) * u, y + (fy - y) * u, 2, 2, (255, 255, 200))
    if t >= at('uranium', "Tout est"):
        panel(img, 480, 524)
        text(img, "100 % IMPORTÉ", 492, CREAM, scale=3)


def sc_dechets(img, t):
    a = start('dechets')
    canicule = at('dechets', "Et les canicules")
    if t < canicule:
        img.paste(gradient([(0, (30, 25, 45)), (0.35, (70, 50, 50)), (1, (15, 10, 15))], 'sous', steps=8))
        d = ImageDraw.Draw(img)
        for y in range(240, H, 26):
            d.line([0, y + math.sin(y) * 4, W, y + 6], fill=(50, 35, 40), width=3)
        bx, by = CX, 400
        glow = 0.6 + 0.4 * math.sin(t * 3)
        ell(d, bx, by, 70, 70, tuple(int(c * glow * 0.4) for c in (120, 255, 120)))
        d.rounded_rectangle([bx - 26, by - 40, bx + 26, by + 40], radius=6, fill=(230, 200, 40))
        for yy in (by - 24, by + 24):
            d.rectangle([bx - 26, yy - 2, bx + 26, yy + 2], fill=(60, 50, 20))
        d.polygon([(bx, by - 12), (bx - 11, by + 8), (bx + 11, by + 8)], fill=INKC)
        tag(img)
        pop_word(img, "3 · LES DÉCHETS", t, a, TOP + 10, GOLD, scale=3)
        if t >= at('dechets', "pendant"):
            p = clamp((t - at('dechets', "pendant")) / 1.4)
            n = int(100 + 99900 * ease_io(p))
            panel(img, 500, 560)
            text(img, f"{n:,} ANS".replace(',', ' '), 506, (150, 255, 150), scale=3)
            text(img, "DES CENTAINES DE MILLIERS D'ANNÉES", 538, (190, 200, 210), scale=1)
        return
    # canicule : rivière qui chauffe, vapeur qui faiblit
    w = world(t, 'nuc')
    img.paste(pan(w, 200))
    heat = Image.new('RGB', (W, H), (255, 120, 60))
    img.paste(Image.blend(img, heat, 0.25))
    d = ImageDraw.Draw(img)
    tx, ty = 300, 260
    d.rounded_rectangle([tx - 10, ty - 90, tx + 10, ty + 30], radius=10, fill=(240, 240, 250))
    p = clamp((t - canicule) / 1.5)
    d.rectangle([tx - 5, ty + 20 - int(100 * p), tx + 5, ty + 25], fill=RED)
    ell(d, tx, ty + 34, 15, 15, RED)
    text(img, "RIVIÈRE TROP CHAUDE", 120, CREAM, scale=2)
    if t >= at('dechets', "certaines"):
        pop_word(img, "PRODUCTION ↓", t, at('dechets', "certaines"), 520, GOLD, scale=3)


def sc_scep2(img, t):
    img.paste(pano_sky('night', NIGHT).crop((700, 0, 700 + W, H)))
    d = ImageDraw.Draw(img)
    for k in range(4):
        turbine(img, 60 + k * 80, 470, 100, t, col=(90, 95, 120), speed=0.05, phase=k)
    d.rectangle([0, 470, W, H], fill=(15, 12, 25))
    sceptic(img, 250, 360, 1.5, t, talking=True)
    bubble(img, 22, 120, 316, "OUI MAIS QUAND IL N'Y A *NI VENT NI SOLEIL*, ON FAIT COMMENT ?")
    text(img, "LE SCEPTIQUE", 520, (180, 185, 210), scale=2, cx=250)


MIX = [("éolien en mer", "ÉOLIEN EN MER", CYAN), ("de solaire", "SOLAIRE", GOLD), ("de barrages", "BARRAGES", (120, 170, 255)),
       ("de stockage", "STOCKAGE", GREEN), ("d'échanges", "VOISINS EUROPÉENS", (200, 160, 255)),
       ("et de sobriété", "SOBRIÉTÉ", (255, 150, 180))]


def sc_reponse(img, t):
    a, b = ST.ph['reponse']
    img.paste(pan(world(t, 'enr'), 500 + (t - a) * 8))
    tag(img)
    pop_word(img, "LA VRAIE QUESTION", t, a, TOP + 10, CREAM, scale=3)
    shown = [m for m in MIX if t >= at('reponse', m[0])]
    if shown:
        panel(img, 150, 158 + 32 * len(shown))
    for k, (key, lab, col) in enumerate(shown):
        pop_word(img, "+ " + lab, t, at('reponse', key), 162 + k * 32, col, scale=2)


def sc_rte(img, t):
    a = start('rte')
    img.paste(gradient([(0, (12, 16, 40)), (1, (25, 20, 50))], 'rte', steps=8))
    d = ImageDraw.Draw(img)
    tag(img)
    pop_word(img, "RTE", t, a, TOP + 10, CYAN, scale=5)
    fade_word(img, "LE GESTIONNAIRE DU RÉSEAU", t, a + 0.4, TOP + 70, (200, 205, 230), scale=2)
    # 6 scénarios : 3 sans nouveau nucléaire, 3 avec
    if t >= at('rte', "a étudié"):
        for k in range(6):
            x = 40 + k * 50
            p = clamp((t - at('rte', "a étudié") - k * 0.12) / 0.4)
            h = int((110 + k * 18) * p)
            col = GREEN if k < 3 else (150, 140, 200)
            d.rectangle([x, 430 - h, x + 34, 430], fill=col)
        text(img, "SANS NOUVEAU", 440, GREEN, scale=1, cx=110, world=True)
        text(img, "NUCLÉAIRE", 452, GREEN, scale=1, cx=110, world=True)
        text(img, "AVEC", 440, (180, 170, 230), scale=1, cx=260, world=True)
    if t >= at('rte', "Possibles"):
        stamp(img, "POSSIBLE", 100, 492, t, at('rte', "Possibles"), col=GREEN, scale=2, angle=-6)
    if t >= at('rte', "Mais exigeants"):
        stamp(img, "PLUS CHER", 262, 492, t, at('rte', "plus chers"), col=STAMP, scale=2, angle=5)


def sc_verdict(img, t):
    a = start('verdict')
    img.paste(pan(world(t, 'mix'), 360))
    veil = Image.new('RGB', (W, H), (10, 8, 25))
    img.paste(Image.blend(img, veil, 0.45))
    tag(img)
    stamp(img, "UTOPISTE ?", CX, 190, t, a, col=STAMP, scale=4, angle=-8)
    items = [("Le cap", "CAP CLAIR"), ("les raisons", "RAISONS SÉRIEUSES"), ("le défi", "DÉFI IMMENSE")]
    for k, (key, lab) in enumerate(items):
        if t >= at('verdict', key):
            pop_word(img, lab, t, at('verdict', key), 270 + k * 34, (CREAM, GOLD, RED)[k], scale=3)
    if t >= at('verdict', "C'est :"):
        panel(img, 400, 470)
        text(img, "PRÊTS À LE PAYER", 410, CREAM, scale=3)
        text(img, "ET À LE CONSTRUIRE ?", 440, GOLD, scale=2)


def sc_cta(img, t):
    a = start('cta')
    w = world(t, 'mix')
    img.paste(pan(w, 300))
    d = ImageDraw.Draw(img)
    panel(img, 130, 260)
    text(img, "NUCLÉAIRE", 146, (220, 200, 255), scale=4)
    text(img, "OU", 186, CREAM, scale=2)
    text(img, "100 % RENOUVELABLE ?", 206, GREEN, scale=3)
    pop_word(img, "DIS-LE EN COMMENTAIRE", t, at('cta', "Dis-le"), 500, GOLD, scale=2)


SCENES = {'flam': sc_flam, 'scep1': sc_scep1, 'intro': sc_intro, 'plan': sc_plan, 'cout': sc_cout,
          'uranium': sc_uranium, 'dechets': sc_dechets, 'scep2': sc_scep2, 'reponse': sc_reponse, 'rte': sc_rte,
          'verdict': sc_verdict, 'cta': sc_cta}
CAMERA = {'flam': (1.12, 1.0, 200, 380), 'scep1': (1.0, 1.06, 250, 300), 'intro': (1.0, 1.0, CX, 320),
          'plan': (1.0, 1.0, CX, 320), 'cout': (1.0, 1.05, 255, 360), 'uranium': (1.0, 1.08, 180, 250),
          'dechets': (1.06, 1.0, CX, 400), 'scep2': (1.0, 1.06, 250, 300), 'reponse': (1.0, 1.0, CX, 320),
          'rte': (1.0, 1.04, CX, 380), 'verdict': (1.08, 1.0, CX, 300), 'cta': (1.0, 1.0, CX, 320)}


# ================================================================ post-traitement
def bloom(img, strength=0.75):
    bright = img.point(lambda v: max(0, v - 185) * 3)
    g1 = bright.filter(ImageFilter.GaussianBlur(5))
    g2 = bright.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H),
                                                                                                  Image.BILINEAR)
    return ImageChops.add(img, Image.eval(ImageChops.add(g1, g2), lambda v: int(v * strength)))


def frame(t):
    pid = ST.para(t)
    img = Image.new('RGB', (W, H))
    fe.UI['layer'] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[pid](img, t)
    a, b = ST.ph[pid]
    img = fe.camera(img, t, *CAMERA[pid], a, b)
    img = bloom(img)
    img.paste(fe.UI['layer'], (0, 0), fe.UI['layer'])
    for bd in ST.bounds():
        d = t - bd
        if -0.16 <= d <= 0.16:
            img = Image.blend(img, BLACK, 0.75 * (1 - abs(d) / 0.16))
    img.paste(BLACK, (0, 0), fe.VIGNETTE)
    if t > DUR - 0.6:
        img = Image.blend(img, BLACK, clamp((t - (DUR - 0.6)) / 0.6))
    return img


SFX.append((0.0, 'impact', None))
SFX.append((at('flam', "Facture"), 'impact', None))
SFX.append((start('scep1'), 'whoosh', None))
SFX.append((at('intro', "Alors on"), 'impact', None))
for key in ("Leur plan", "fermer les", "passer à"):
    SFX.append((at('plan', key), 'place', 12))
SFX.append((at('cout', "La Cour"), 'impact', None))
SFX.append((at('uranium', "depuis 2001"), 'impact', None))
SFX.append((start('scep2'), 'whoosh', None))
for m in MIX:
    SFX.append((at('reponse', m[0]), 'place', 14))
SFX.append((start('verdict'), 'impact', None))
SFX.append((at('cta', "Dis-le"), 'coin', None))

if __name__ == '__main__':
    render(os.path.join(HERE, 'nucleaire_tiktok.mp4'), DUR, frame,
           os.path.join(HERE, 'audio', 'narration.mp3'), ST.ph, ST.end)
