"""Vidéo TikTok « Les dernières fois » — DA fine, ambiance chaude et pellicule.

Lumière dorée, polaroïds qui se figent puis pâlissent, toise de croissance sur
un chambranle, premières fois en fête contre dernières fois en silence. Fondus
au noir entre les scènes et grain de pellicule. Pas de musique.

    python3 make_video.py                 # produit dernieres_fois_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from fine_engine import (W, H, CX, TOP, SFX, Story, gradient, mix, ell, text, fade_word, motes,  # noqa: E402
                         compose, render, clamp, ease_io, ease_out_back)

HERE = os.path.dirname(os.path.abspath(__file__))
IDS = ['bras', 'soir', 'souvenirs', 'premieres', 'maintenant', 'lesquelles', 'cesoir', 'fin']
# {id: (début, fin)} mesurés sur audio/narration.mp3 (pauses > 0,3 s, alignées sur la longueur du texte)
MEASURED = {
    'bras': (0.0, 5.18), 'soir': (5.66, 10.44), 'souvenirs': (11.05, 18.34), 'premieres': (18.93, 23.57),
    'maintenant': (24.06, 31.60), 'lesquelles': (31.97, 34.18), 'cesoir': (34.63, 40.09), 'fin': (40.48, 44.0),
}
ST = Story(IDS, os.path.join(HERE, 'texte_narration.txt'), MEASURED)
at, start = ST.at, ST.start
DUR = ST.end + 2.0

CREAM = (255, 244, 225)
WARM = (255, 214, 160)
INKC = (40, 26, 30)


# ================================================================ outils
def sepia(img, a):
    """Fait pâlir une image vers un sépia doux (a = 0..1)."""
    if a <= 0:
        return img
    g = ImageOps.grayscale(img)
    sep = ImageOps.colorize(g, (60, 40, 30), (250, 230, 200))
    return Image.blend(img, sep, clamp(a))


def polaroid(content, w, angle=0.0, pale=0.0, label=None):
    """Cadre polaroïd autour de `content` (image RGB), renvoie une image RGBA."""
    ph = content.resize((w - 16, int((w - 16) * content.height / content.width)), Image.NEAREST)
    ph = sepia(ph, pale)
    h = ph.height + 16 + 34
    card = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, w - 1, h - 1], fill=(248, 244, 236, 255))
    card.paste(ph, (8, 8))
    if label:
        from fine_engine import draw_text
        draw_text(card, label, w // 2, ph.height + 18, (70, 60, 70), scale=1, maxw=w - 12, shadow=None)
    shadow = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([6, 6, w + 5, h + 5], fill=(0, 0, 0, 110))
    shadow.alpha_composite(card, (0, 0))
    return shadow.rotate(angle, resample=Image.NEAREST, expand=True)


def paste_center(img, rgba, cx, cy):
    img.paste(rgba, (int(cx - rgba.width / 2), int(cy - rgba.height / 2)), rgba)


def person(d, cx, cy, s, col, arms=None, head_tilt=0):
    """Silhouette simple ; arms = liste de (x, y) de mains relatives aux épaules."""
    ell(d, cx + head_tilt * s, cy - 50 * s, 11 * s, 12 * s, col)
    d.rounded_rectangle([cx - 11 * s, cy - 37 * s, cx + 11 * s, cy + 2 * s], radius=int(6 * s), fill=col)
    for sgn in (-1, 1):
        d.line([cx + sgn * 6 * s, cy, cx + sgn * 8 * s, cy + 34 * s], fill=col, width=int(7 * s))
    for (hx, hy) in (arms or [(-16, 30), (16, 30)]):
        sx = cx + (-9 if hx < 0 else 9) * s
        d.line([sx, cy - 32 * s, cx + hx * s, cy - 32 * s + hy * s], fill=col, width=int(6 * s))


def child(d, cx, cy, s, col):
    ell(d, cx, cy - 26 * s, 8 * s, 8 * s, col)
    d.rounded_rectangle([cx - 8 * s, cy - 18 * s, cx + 8 * s, cy + 6 * s], radius=int(4 * s), fill=col)
    for sgn in (-1, 1):
        d.line([cx + sgn * 4 * s, cy + 4 * s, cx + sgn * 6 * s, cy + 22 * s], fill=col, width=int(5 * s))
        d.line([cx + sgn * 6 * s, cy - 14 * s, cx + sgn * 16 * s, cy - 26 * s], fill=col, width=int(4 * s))


# ================================================================ décors
def golden_room(t):
    img = gradient([(0, (120, 60, 70)), (0.45, (240, 150, 100)), (0.8, (255, 205, 150)), (1, (120, 70, 60))],
                   'room', steps=10)
    d = ImageDraw.Draw(img)
    # fenêtre et rayons
    d.rectangle([210, 110, 330, 300], fill=(255, 235, 190))
    d.rectangle([210, 110, 330, 300], outline=(110, 60, 50), width=6)
    d.line([270, 110, 270, 300], fill=(110, 60, 50), width=5)
    d.line([210, 205, 330, 205], fill=(110, 60, 50), width=5)
    for k in range(4):
        x = 215 + k * 30
        d.polygon([(x, 300), (x + 18, 300), (x - 160, 640), (x - 210, 640)], fill=None, outline=(255, 225, 170))
    d.rectangle([0, 470, W, H], fill=(150, 80, 60))
    d.rectangle([0, 470, W, 476], fill=(190, 110, 80))
    motes(img, t, 70, (255, 240, 200), seed=2, area=(40, 120, 330, 470))
    return img


def night_house(t, lit=True):
    img = gradient([(0, (10, 12, 40)), (0.7, (40, 40, 90)), (1, (25, 25, 50))], 'night', steps=8)
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(60):
        x, y = r.randrange(W), r.randrange(0, 300)
        if (int(t * 2) + x) % 5:
            img.putpixel((x, y), (230, 230, 255))
    ell(d, 285, 225, 16, 16, (245, 240, 220))
    d.polygon([(70, 300), (180, 210), (290, 300)], fill=(40, 30, 50))
    d.rectangle([90, 300, 270, 470], fill=(55, 45, 70))
    win = (255, 210, 130) if lit else (35, 30, 50)
    for x in (115, 205):
        d.rectangle([x, 330, x + 40, 380], fill=win)
        d.line([x + 20, 330, x + 20, 380], fill=(55, 45, 70), width=3)
    d.rectangle([165, 400, 195, 470], fill=(80, 55, 50))
    d.rectangle([0, 470, W, H], fill=(20, 30, 30))
    return img


def wood_table(t):
    img = gradient([(0, (110, 70, 50)), (1, (70, 45, 35))], 'wood', steps=6)
    d = ImageDraw.Draw(img)
    for y in range(0, H, 18):
        d.line([0, y + int(math.sin(y) * 3), W, y + 4], fill=(95, 60, 45), width=2)
    return img


# petites photos (contenus des polaroïds)
def photo_cachecache(t):
    im = gradient([(0, (170, 210, 240)), (1, (250, 240, 210))], 'p_sky', steps=6).resize((120, 90))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 66, 120, 90], fill=(120, 170, 90))
    d.rectangle([66, 30, 76, 72], fill=(110, 70, 40))
    ell(d, 71, 26, 22, 18, (70, 130, 70))
    ell(d, 82, 56, 4, 4, (240, 190, 150))          # enfant caché derrière l'arbre
    child(d, 30, 68, 0.9, (220, 90, 90))
    return im


def photo_histoire(t):
    im = Image.new('RGB', (120, 90), (40, 30, 50))
    d = ImageDraw.Draw(im)
    ell(d, 96, 20, 30, 30, (120, 90, 60))
    d.polygon([(90, 8), (102, 8), (108, 22), (84, 22)], fill=(255, 210, 140))
    d.rectangle([10, 56, 110, 80], fill=(90, 110, 170))
    ell(d, 30, 54, 9, 8, (240, 200, 170))
    d.rectangle([56, 40, 82, 56], fill=(250, 240, 220))
    d.line([69, 40, 69, 56], fill=(150, 120, 100))
    return im


def photo_mamie(t):
    im = Image.new('RGB', (120, 90), (230, 200, 170))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 14, 80, 80], radius=6, fill=(40, 40, 50))
    d.rectangle([44, 22, 76, 70], fill=(120, 190, 140))
    from fine_engine import draw_text
    draw_text(im, "MAMIE", 60, 30, (255, 255, 255), scale=1, maxw=40, shadow=None)
    for dx in (-4, 4):
        ell(d, 60 + dx, 52, 4, 4, (230, 70, 90))
    d.polygon([(52, 54), (68, 54), (60, 64)], fill=(230, 70, 90))
    return im


# ================================================================ scènes
def sc_bras(img, t):
    scene = golden_room(t)
    d = ImageDraw.Draw(scene)
    sway = math.sin(t * 1.2) * 3
    person(d, 150 + sway, 430, 1.6, (60, 30, 40), arms=[(4, 2), (14, 4)], head_tilt=3)
    child(d, 168 + sway, 382, 1.25, (90, 45, 55))
    freeze = at('bras', "Et aucun")
    if t < freeze:
        img.paste(scene)
    else:
        p = ease_io((t - freeze) / 1.0)
        img.paste(gradient([(0, (40, 25, 30)), (1, (70, 40, 40))], 'dark', steps=6))
        w = int(W - (W - 230) * p)
        card = polaroid(scene, max(60, w), angle=-4 * p, pale=clamp((t - freeze - 0.8) / 2.0) * 0.8)
        paste_center(img, card, CX, 330)
    fade_word(img, "UN JOUR, QUELQU'UN T'A PORTÉ", t, start('bras'), TOP, CREAM, scale=2)
    fade_word(img, "POUR LA DERNIÈRE FOIS", t, at('bras', "pour la"), TOP + 26, WARM, scale=3)
    if t >= freeze:
        fade_word(img, "ET PERSONNE NE LE SAVAIT", t, freeze + 0.3, 520, CREAM, scale=3)


def sc_soir(img, t):
    morning = at('soir', "Et le lendemain")
    if t < morning:
        off = t >= at('soir', "Juste un soir") + 1.0
        img.paste(night_house(t, lit=not off))
        fade_word(img, "PAS D'ANNONCE", t, start('soir'), TOP, CREAM, scale=3)
        fade_word(img, "JUSTE UN SOIR COMME LES AUTRES", t, at('soir', "Juste"), TOP + 32, (200, 200, 240), scale=2)
        return
    # la toise sur le chambranle
    img.paste(gradient([(0, (250, 230, 200)), (1, (220, 190, 160))], 'wall', steps=6))
    d = ImageDraw.Draw(img)
    d.rectangle([150, 60, 210, H], fill=(200, 150, 110))
    d.rectangle([150, 60, 156, H], fill=(170, 120, 85))
    lt = t - morning
    marks = [(470, "3 ANS"), (420, "5 ANS"), (370, "7 ANS"), (320, "9 ANS"), (270, "12 ANS")]
    for k, (y, lab) in enumerate(marks):
        if lt > k * 0.35:
            d.line([150, y, 226, y], fill=(70, 50, 60), width=3)
            text(img, lab, y - 6, (90, 60, 60), scale=2, cx=262, shadow=None)
    fade_word(img, "LE LENDEMAIN,", t, morning, TOP, INKC, scale=3, shadow=(255, 240, 220))
    fade_word(img, "TU AVAIS GRANDI", t, morning + 0.4, TOP + 32, (150, 70, 60), scale=3, shadow=(255, 240, 220))


SOUV = [("cache-cache", photo_cachecache, "LA DERNIÈRE PARTIE DE CACHE-CACHE", -7, (110, 250)),
        ("histoire", photo_histoire, "LA DERNIÈRE HISTOIRE DU SOIR", 5, (250, 330)),
        ("coup de fil", photo_mamie, "LE DERNIER APPEL À MAMIE", -3, (140, 410))]


def sc_souvenirs(img, t):
    img.paste(wood_table(t))
    fade_word(img, "IL Y A EU...", t, start('souvenirs'), TOP, CREAM, scale=3)
    shown = None
    for key, fn, lab, ang, (x, y) in SOUV:
        tk = at('souvenirs', key) - 0.3
        if t < tk:
            continue
        p = ease_out_back((t - tk) / 0.5)
        yy = y - (1 - min(p, 1)) * 260
        card = polaroid(fn(t), 150, angle=ang, pale=clamp((t - tk - 1.4) / 2.0) * 0.85)
        paste_center(img, card, x, yy)
        shown = lab
    if shown:
        text(img, shown, 520, CREAM, scale=3)


def sc_premieres(img, t):
    left = gradient([(0, (255, 210, 120)), (1, (255, 150, 140))], 'fest', steps=7)
    right = gradient([(0, (20, 25, 50)), (1, (40, 40, 70))], 'quiet', steps=7)
    img.paste(left.crop((0, 0, CX, H)), (0, 0))
    img.paste(right.crop((CX, 0, W, H)), (CX, 0))
    d = ImageDraw.Draw(img)
    r = random.Random(7)
    for i in range(60):
        x = r.randrange(0, CX - 6)
        y = (r.randrange(0, H) + t * r.uniform(40, 90)) % H
        c = [(255, 80, 120), (80, 180, 255), (255, 240, 90), (120, 230, 120)][i % 4]
        d.rectangle([x, y, x + 3, y + 5], fill=c)
    if int(t * 2) % 2:
        ell(d, 30, 206, 6, 6, (230, 30, 50))
    text(img, "REC", 200, (230, 30, 50), scale=2, cx=62, shadow=None)
    ell(d, 90, 300, 26, 32, (255, 90, 120))
    d.line([90, 332, 96, 420], fill=(200, 200, 200), width=2)
    # une feuille qui tombe lentement, à droite
    lt = t - start('premieres')
    fx = 270 + math.sin(lt * 1.6) * 24
    fy = 160 + lt * 40
    d.polygon([(fx, fy - 8), (fx + 9, fy), (fx, fy + 8), (fx - 9, fy)], fill=(200, 120, 60))
    fade_word(img, "PREMIÈRES", t, start('premieres'), TOP, INKC, scale=3, cx=90, maxw=170, shadow=(255, 240, 210))
    fade_word(img, "FOIS", t, start('premieres'), TOP + 28, INKC, scale=3, cx=90, maxw=170, shadow=(255, 240, 210))
    fade_word(img, "ON LES FÊTE", t, at('premieres', "on les fête"), 470, INKC, scale=2, cx=90, maxw=170,
              shadow=(255, 240, 210))
    fade_word(img, "ON LES FILME", t, at('premieres', "On les filme"), 494, INKC, scale=2, cx=90, maxw=170,
              shadow=(255, 240, 210))
    fade_word(img, "DERNIÈRES", t, at('premieres', "Les dernières"), TOP, (200, 200, 240), scale=3, cx=270, maxw=170)
    fade_word(img, "FOIS", t, at('premieres', "Les dernières"), TOP + 28, (200, 200, 240), scale=3, cx=270, maxw=170)
    fade_word(img, "SANS UN BRUIT", t, at('premieres', "sans un bruit"), 470, (200, 200, 240), scale=2, cx=270,
              maxw=170)


def hourglass(d, cx, cy, t, p):
    d.polygon([(cx - 18, cy - 30), (cx + 18, cy - 30), (cx, cy)], outline=(240, 230, 210), fill=None)
    d.polygon([(cx - 18, cy + 30), (cx + 18, cy + 30), (cx, cy)], outline=(240, 230, 210), fill=None)
    top = int(26 * (1 - p))
    if top > 0:
        d.polygon([(cx - top * 0.6, cy - top), (cx + top * 0.6, cy - top), (cx, cy - 2)], fill=(250, 210, 120))
    bot = int(26 * p)
    d.polygon([(cx - bot * 0.7, cy + 28), (cx + bot * 0.7, cy + 28), (cx, cy + 28 - bot)], fill=(250, 210, 120))
    if p < 1 and int(t * 10) % 2:
        d.line([cx, cy, cx, cy + 26], fill=(250, 210, 120))


def sc_maintenant(img, t):
    a, b = ST.ph['maintenant']
    repas = at('maintenant', "Le dernier repas")
    if t < repas:
        img.paste(night_house(t, lit=True).transpose(Image.FLIP_LEFT_RIGHT))
        d = ImageDraw.Draw(img)
        d.rectangle([90, 430, 270, 438], fill=(60, 45, 40))
        laugh = math.sin(t * 14) * 2
        person(d, 140, 430 + laugh, 1.1, (20, 15, 30), head_tilt=-2)
        person(d, 220, 430 - laugh, 1.1, (20, 15, 30), head_tilt=2)
        if t >= at('maintenant', "Le dernier fou"):
            fade_word(img, "LE DERNIER FOU RIRE", t, at('maintenant', "Le dernier fou"), 500, CREAM, scale=3)
    else:
        img.paste(gradient([(0, (60, 30, 30)), (1, (30, 15, 20))], 'dinner', steps=6))
        d = ImageDraw.Draw(img)
        d.rectangle([40, 380, 320, 400], fill=(120, 70, 50))
        for x in (110, 250):
            ell(d, x, 372, 30, 8, (240, 235, 225))
        d.rectangle([176, 330, 184, 372], fill=(245, 240, 225))
        fl = 1 + math.sin(t * 9) * 0.2
        ell(d, 180, 322, 5, 9 * fl, (255, 200, 90))
        glow = Image.new('RGB', (W, H), (255, 190, 110))
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).ellipse([60, 220, 300, 460], fill=40)
        img.paste(glow, (0, 0), m)
        fade_word(img, "LE DERNIER REPAS", t, repas, 496, CREAM, scale=3)
        fade_word(img, "AVEC QUELQU'UN QUI COMPTE", t, repas + 0.6, 530, WARM, scale=2)
    d = ImageDraw.Draw(img)
    hourglass(d, 312, 196, t, clamp((t - a) / max(1, b - a)))
    fade_word(img, "EN CE MOMENT,", t, a, TOP, CREAM, scale=3)
    fade_word(img, "IL Y EN A QUI APPROCHENT", t, at('maintenant', "il y en a"), TOP + 32, WARM, scale=2)


def sc_lesquelles(img, t):
    img.paste(gradient([(0, (25, 20, 40)), (1, (50, 35, 55))], 'float', steps=6))
    r = random.Random(9)
    blank = Image.new('RGB', (80, 60), (60, 55, 70))
    from fine_engine import draw_text
    draw_text(blank, "?", 40, 18, (200, 190, 210), scale=3, maxw=60, shadow=None)
    for k in range(9):
        x = r.uniform(40, 320) + math.sin(t * 0.5 + k) * 10
        y = (r.uniform(0, H) - t * r.uniform(8, 16)) % (H + 120) - 60
        paste_center(img, polaroid(blank, 80, angle=r.uniform(-12, 12)), x, y)
    fade_word(img, "LESQUELLES ?", t, start('lesquelles'), 280, CREAM, scale=4)
    fade_word(img, "PERSONNE NE LE SAIT", t, at('lesquelles', "Personne"), 330, WARM, scale=2)


def window_night(t):
    img = gradient([(0, (15, 15, 40)), (1, (35, 25, 55))], 'win', steps=6)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 200, 300, 440], fill=(25, 35, 80))
    r = random.Random(2)
    for _ in range(40):
        x, y = r.randrange(64, 296), r.randrange(204, 436)
        if (int(t * 2) + x) % 4:
            img.putpixel((x, y), (230, 230, 255))
    ell(d, 240, 262, 18, 18, (250, 245, 225))
    d.rectangle([60, 200, 300, 440], outline=(60, 45, 60), width=8)
    d.line([180, 200, 180, 440], fill=(60, 45, 60), width=6)
    d.rectangle([40, 440, 320, 452], fill=(80, 60, 70))
    return img


def sc_cesoir(img, t):
    img.paste(window_night(t))
    d = ImageDraw.Draw(img)
    person(d, 180, 520, 1.6, (8, 8, 15))
    call = at('cesoir', "Rappelle")
    if t >= call:
        p = clamp((t - call) / 0.4)
        d.rounded_rectangle([200, 430, 236, 492], radius=5, fill=(30, 30, 40))
        d.rectangle([203, 436, 233, 486], fill=mix((30, 30, 40), (120, 220, 150), p))
        glow = Image.new('RGB', (W, H), (120, 220, 150))
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).ellipse([150, 380, 290, 540], fill=int(60 * p))
        img.paste(glow, (0, 0), m)
    fade_word(img, "CE SOIR", t, start('cesoir'), TOP, CREAM, scale=3)
    fade_word(img, "N'ESSAIE PAS DE TOUT RETENIR", t, at('cesoir', "n'essaie"), TOP + 32, (200, 200, 240), scale=2)
    if t >= at('cesoir', "Regarde"):
        fade_word(img, "REGARDE UN PEU PLUS LONGTEMPS", t, at('cesoir', "Regarde"), TOP + 56, WARM, scale=2)
    if t >= call:
        fade_word(img, "RAPPELLE QUELQU'UN", t, call, TOP + 80, (150, 240, 180), scale=2)


def sc_fin(img, t):
    a = start('fin')
    p = ease_io((t - a) / 1.6)
    scene = window_night(t)
    person(ImageDraw.Draw(scene), 180, 520, 1.6, (8, 8, 15))
    img.paste(gradient([(0, (40, 25, 30)), (1, (70, 40, 40))], 'dark', steps=6))
    w = int(W - (W - 220) * p)
    card = polaroid(scene, max(60, w), angle=3 * p, pale=clamp((t - a - 2.0) / 2.0) * 0.6,
                    label="CE SOIR" if p > 0.9 else None)
    paste_center(img, card, CX, 320)
    fade_word(img, "UN JOUR, CE MOMENT-LÀ AUSSI", t, a + 0.6, TOP, CREAM, scale=2)
    fade_word(img, "SERA UNE DERNIÈRE FOIS", t, at('fin', "sera"), 540, WARM, scale=3)


SCENES = {'bras': sc_bras, 'soir': sc_soir, 'souvenirs': sc_souvenirs, 'premieres': sc_premieres,
          'maintenant': sc_maintenant, 'lesquelles': sc_lesquelles, 'cesoir': sc_cesoir, 'fin': sc_fin}
CAMERA = {'bras': (1.0, 1.06, 150, 360), 'soir': (1.04, 1.0, CX, 340), 'souvenirs': (1.0, 1.04, CX, 330),
          'maintenant': (1.0, 1.05, CX, 420), 'lesquelles': (1.0, 1.0, CX, 320), 'cesoir': (1.0, 1.08, 180, 330),
          'fin': (1.0, 1.0, CX, 320), 'premieres': (1.0, 1.0, CX, 320)}

for key, *_ in SOUV:
    SFX.append((at('souvenirs', key) - 0.1, 'place', 0))
SFX.append((at('bras', "Et aucun"), 'whoosh', None))
SFX.append((at('fin', "sera"), 'sparkle', None))


def frame(t):
    return compose(ST, SCENES, CAMERA, t, DUR, whip=False, film=True)


if __name__ == '__main__':
    render(os.path.join(HERE, 'dernieres_fois_tiktok.mp4'), DUR, frame,
           os.path.join(HERE, 'audio', 'narration.mp3'), ST.ph, ST.end)
