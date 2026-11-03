"""Vidéo TikTok « Ton cerveau a déjà décidé » — DA néon (lueurs, réseau neuronal).

Hook : la vidéo fait semblant de se scroller toute seule vers la suivante, puis
se rattrape sur « Attends. ». Sujet : Libet (1983), Soon et al. (2008), le véto.
Rendu 360x640 agrandi x3, avec une passe de lueur (bloom), aberration
chromatique légère et réseau de neurones animé. Pas de musique.

    python3 make_video.py                 # produit cerveau_decide_tiktok.mp4
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
                         render, clamp, ease_io, ease_out_back, BLACK)

HERE = os.path.dirname(os.path.abspath(__file__))
IDS = ['hook', 'attends', 'libet', 'electrodes', 'scanner', 'qui', 'veto', 'encore', 'fin']
# {id: (début, fin)} mesurés sur audio/narration.mp3 (pauses > 0,3 s, alignées sur la longueur du texte)
MEASURED = {
    'hook': (0.0, 4.80), 'attends': (5.11, 8.87), 'libet': (9.45, 17.94), 'electrodes': (18.36, 26.03),
    'scanner': (26.57, 37.55), 'qui': (38.07, 41.85), 'veto': (42.23, 50.38), 'encore': (50.84, 55.60),
    'fin': (55.96, 59.1),
}
ST = Story(IDS, os.path.join(HERE, 'texte_narration.txt'), MEASURED)
at, start = ST.at, ST.start
DUR = ST.end + 1.6

CYAN = (90, 230, 255)
MAG = (255, 80, 200)
VIO = (150, 110, 255)
WHITE = (240, 245, 255)
GOLD = (255, 210, 110)
RED = (255, 70, 90)

# ================================================================ réseau neuronal
_r = random.Random(42)
NODES = [(_r.uniform(10, W - 10), _r.uniform(10, H - 10), _r.uniform(0, 6.28)) for _ in range(70)]
EDGES = []
for i, (x, y, _) in enumerate(NODES):
    near = sorted(range(len(NODES)), key=lambda j: (NODES[j][0] - x) ** 2 + (NODES[j][1] - y) ** 2)[1:4]
    for j in near:
        if (j, i) not in EDGES:
            EDGES.append((i, j))


def network(img, t, col=CYAN, energy=1.0, drift=1.0):
    d = ImageDraw.Draw(img)
    pts = [(x + math.sin(t * 0.3 * drift + p) * 6, y + math.cos(t * 0.25 * drift + p) * 6) for x, y, p in NODES]
    dim = tuple(int(c * 0.25 * energy) for c in col)
    for i, j in EDGES:
        d.line([pts[i], pts[j]], fill=dim, width=1)
    for k, (i, j) in enumerate(EDGES):
        u = (t * 0.8 * drift + k * 0.137) % 1.0
        if (k + int(t * 2)) % 3 == 0:
            x = pts[i][0] + (pts[j][0] - pts[i][0]) * u
            y = pts[i][1] + (pts[j][1] - pts[i][1]) * u
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=tuple(int(c * energy) for c in col))
    for k, (x, y) in enumerate(pts):
        b = 0.5 + 0.5 * math.sin(t * 3 + NODES[k][2])
        r = 1.5 + b * 1.5
        ell(d, x, y, r, r, tuple(int(c * (0.4 + 0.6 * b) * energy) for c in col))


def brain(img, cx, cy, s, t, col=CYAN, fill=(20, 15, 50), pulse=0.0):
    """Cerveau en profil, contour néon + circonvolutions."""
    d = ImageDraw.Draw(img)
    rx, ry = 92 * s, 70 * s
    pts = []
    for k in range(64):
        a = k / 64 * 6.283
        wob = 1 + 0.06 * math.sin(a * 7) + 0.03 * math.sin(a * 13)
        pts.append((cx + math.cos(a) * rx * wob, cy + math.sin(a) * ry * wob * (0.9 if math.sin(a) > 0 else 1)))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=col, width=3)
    d.line([cx - rx * 0.02, cy - ry * 0.95, cx - rx * 0.05, cy + ry * 0.6], fill=col, width=2)
    for k in range(9):
        ox = cx - rx * 0.7 + k * rx * 0.18
        pts2 = [(ox + math.sin(j * 0.9 + k) * 8 * s, cy - ry * 0.7 + j * ry * 0.18) for j in range(8)]
        d.line(pts2, fill=tuple(int(c * 0.6) for c in col), width=2)
    # tronc cérébral
    d.polygon([(cx + rx * 0.2, cy + ry * 0.75), (cx + rx * 0.4, cy + ry * 0.75), (cx + rx * 0.35, cy + ry * 1.25),
               (cx + rx * 0.25, cy + ry * 1.25)], fill=fill, outline=col)
    if pulse > 0:
        r = (1 + pulse * 0.6)
        d.ellipse([cx - rx * r, cy - ry * r, cx + rx * r, cy + ry * r], outline=tuple(int(c * (1 - pulse)) for c in col),
                  width=2)


def thumb(img, x, y, s=1.0, col=(240, 200, 170)):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 16 * s, y, x + 16 * s, y + 90 * s], radius=int(14 * s), fill=col)
    d.rounded_rectangle([x - 10 * s, y + 6 * s, x + 10 * s, y + 28 * s], radius=int(6 * s), fill=(255, 225, 205))


def glow_ring(img, cx, cy, r, col, w=2):
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)


def bg_deep(key='deep'):
    return gradient([(0, (6, 4, 22)), (0.5, (16, 10, 45)), (1, (4, 3, 15))], key, steps=10)


# ================================================================ scènes
SCROLL_T = 3.6                                     # la vidéo « se scrolle » pendant « tu ne le sais pas encore »
SNAP_T = start('attends')                          # « Attends. »


def fake_next_video(t):
    """La « vidéo suivante » : un faux short (chat + cuisine pixel) qui arrive par le bas."""
    im = gradient([(0, (255, 180, 120)), (1, (255, 110, 140))], 'next', steps=8)
    d = ImageDraw.Draw(im)
    ell(d, CX, 360, 70, 56, (90, 70, 60))
    for sx in (-1, 1):
        d.polygon([(CX + sx * 30, 314), (CX + sx * 60, 280), (CX + sx * 62, 330)], fill=(90, 70, 60))
        ell(d, CX + sx * 24, 350, 8, 10, (255, 230, 120))
        ell(d, CX + sx * 24, 350, 3, 9, (20, 20, 20))
    d.polygon([(CX - 6, 372), (CX + 6, 372), (CX, 380)], fill=(255, 150, 160))
    text(im, "POV : TON CHAT", 150, (255, 255, 255), scale=3, world=True)
    text(im, "QUAND TU RENTRES", 180, (255, 255, 255), scale=3, world=True)
    return im


def sc_hook(img, t):
    img.paste(bg_deep())
    network(img, t, CYAN, energy=0.9)
    beat = max(0, math.sin(t * 6)) ** 6
    brain(img, CX, 310, 1.15, t, CYAN, pulse=(t * 0.9) % 1)
    # le pouce qui s'approche de l'écran
    pop_word(img, "TU VAS SCROLLER", t, 0.0, TOP, WHITE, scale=4)
    pop_word(img, "CETTE VIDÉO", t, 0.25, TOP + 42, CYAN, scale=4)
    if t >= 1.62:
        fade_word(img, "TON CERVEAU L'A DÉJÀ DÉCIDÉ", t, 1.62, 450, MAG, scale=2, dur=0.3)
    if t >= 3.38:
        fade_word(img, "TOI, TU NE LE SAIS PAS ENCORE", t, 3.38, 474, WHITE, scale=2, dur=0.3)


def sc_attends(img, t):
    img.paste(bg_deep())
    network(img, t, MAG, energy=1.0, drift=2)
    brain(img, CX, 330, 1.0, t, MAG, fill=(40, 10, 40))
    pop_word(img, "ATTENDS.", t, start('attends'), TOP, WHITE, scale=6)
    c0 = 5.80
    if t >= c0:
        n = 3 - int(min(2.99, (t - c0) / 0.7))
        pop_word(img, str(n), t, c0 + (3 - n) * 0.7, 250, GOLD, scale=8)
    if t >= at('attends', "et je te"):
        fade_word(img, "TU N'ES PAS AUX COMMANDES", t, at('attends', "et je te"), 480, CYAN, scale=2)


def sc_libet(img, t):
    img.paste(gradient([(0, (8, 12, 30)), (1, (20, 25, 60))], 'lab', steps=8))
    d = ImageDraw.Draw(img)
    # l'horloge de Libet : un point qui tourne
    cx, cy, r = CX, 270, 70
    glow_ring(img, cx, cy, r, CYAN, 3)
    for k in range(12):
        a = k / 12 * 6.283
        d.line([cx + math.cos(a) * (r - 8), cy + math.sin(a) * (r - 8), cx + math.cos(a) * r, cy + math.sin(a) * r],
               fill=CYAN, width=2)
    a = t * 2.4
    ell(d, cx + math.cos(a - 1.57) * (r - 18), cy + math.sin(a - 1.57) * (r - 18), 6, 6, GOLD)
    # main et doigt
    hx, hy = CX, 430
    skin, skin2 = (150, 95, 80), (170, 110, 92)
    d.rounded_rectangle([hx - 40, hy, hx + 40, hy + 50], radius=12, fill=skin)
    for k in range(3):
        d.rounded_rectangle([hx - 34 + k * 16, hy - 10, hx - 22 + k * 16, hy + 8], radius=5, fill=skin)
    lift = max(0, math.sin(t * 2.2)) * 10
    d.rounded_rectangle([hx + 14, hy - 34 - lift, hx + 28, hy + 4], radius=7, fill=skin2)
    pop_word(img, "1983", t, start('libet'), TOP, GOLD, scale=5)
    fade_word(img, "BENJAMIN LIBET", t, at('libet', "Benjamin"), TOP + 54, WHITE, scale=3)
    if t >= at('libet', "Et de noter"):
        fade_word(img, "« NOTE L'INSTANT OÙ TU DÉCIDES »", t, at('libet', "Et de noter"), 510, CYAN, scale=2)


def sc_electrodes(img, t):
    img.paste(bg_deep('deep2'))
    d = ImageDraw.Draw(img)
    a = start('electrodes')
    # tracé EEG : bruit puis rampe (potentiel de préparation)
    x0, x1, base = 20, 340, 330
    t_aware, t_move = 260, 300            # en pixels sur l'axe
    prog = clamp((t - a) / 2.5)
    pts = []
    rng = random.Random(3)
    for x in range(x0, int(x0 + (x1 - x0) * prog)):
        n = rng.uniform(-6, 6)
        ramp = 0 if x < 150 else -((x - 150) / (t_move - 150)) ** 1.6 * 110
        if x > t_move:
            ramp = -110 + (x - t_move) * 2
        pts.append((x, base + n + ramp))
    if len(pts) > 1:
        d.line(pts, fill=CYAN, width=2)
    d.line([x0, base + 30, x1, base + 30], fill=(60, 70, 110), width=1)
    if prog > 0.45:
        d.line([150, 160, 150, base + 40], fill=MAG, width=2)
        text(img, "CERVEAU", 380, MAG, scale=2, cx=150, world=True)
    if prog > 0.8:
        d.line([t_aware, 160, t_aware, base + 40], fill=GOLD, width=2)
        text(img, "CONSCIENCE", 380, GOLD, scale=2, cx=t_aware + 10, world=True)
    if t >= at('electrodes', "Environ"):
        d.line([150, 410, t_aware, 410], fill=WHITE, width=2)
        pop_word(img, "≈ 0,35 S AVANT", t, at('electrodes', "Environ"), 420, WHITE, scale=3)
    fade_word(img, "LES ÉLECTRODES", t, a, TOP, WHITE, scale=3)
    fade_word(img, "VOIENT LE CERVEAU PARTIR AVANT", t, a + 0.3, TOP + 32, CYAN, scale=2)


def sc_scanner(img, t):
    img.paste(bg_deep('deep3'))
    d = ImageDraw.Draw(img)
    a = start('scanner')
    brain(img, CX, 300, 1.1, t, VIO, fill=(25, 15, 60))
    # balayage du scanner
    y = 220 + ((t * 80) % 170)
    d.line([60, y, 300, y], fill=(150, 255, 200), width=2)
    for k in range(5):
        if (int(t * 4) + k) % 2:
            ell(d, CX - 40 + k * 20, 300 + math.sin(k) * 20, 7, 7, MAG)
    pop_word(img, "2008", t, a, TOP, GOLD, scale=5)
    if t >= at('scanner', "elle devine"):
        for k, (lab, x) in enumerate((("G", 110), ("D", 250))):
            pick = int(t * 1.5) % 2 == k
            d.rounded_rectangle([x - 26, 420, x + 26, 470], radius=10, outline=CYAN if pick else (80, 90, 130),
                                width=3)
            text(img, lab, 434, CYAN if pick else (120, 130, 170), scale=3, cx=x, world=True)
    if t >= at('scanner', "jusqu'à sept"):
        pop_word(img, "7 SECONDES AVANT", t, at('scanner', "jusqu'à sept"), 168, MAG, scale=3)
    if t >= at('scanner', "Mais plus"):
        fade_word(img, "PAS À TOUS LES COUPS · MAIS MIEUX QUE LE HASARD", t, at('scanner', "Pas à"), 500, WHITE,
                  scale=2, maxw=330)


def strings(img, t, x, top, bottom, col):
    d = ImageDraw.Draw(img)
    for k, dx in enumerate((-22, 0, 22)):
        sway = math.sin(t * 2 + k) * 4
        d.line([x + dx, top, x + dx + sway, bottom - k * 6], fill=col, width=1)


def sc_qui(img, t):
    img.paste(bg_deep())
    network(img, t, VIO, energy=0.6)
    brain(img, CX, 200, 0.75, t, VIO)
    strings(img, t, CX, 250, 400, (180, 160, 255))
    d = ImageDraw.Draw(img)
    sx, sy = CX, 470
    ell(d, sx, sy - 70, 14, 15, (230, 230, 245))
    d.rounded_rectangle([sx - 16, sy - 54, sx + 16, sy], radius=8, fill=(230, 230, 245))
    for dx in (-22, 22):
        d.line([sx + dx * 0.4, sy - 48, sx + dx, sy - 24 + math.sin(t * 2 + dx) * 6], fill=(230, 230, 245), width=5)
    pop_word(img, "QUI DÉCIDE ?", t, start('qui'), TOP, WHITE, scale=4)
    if t >= at('qui', "ou un"):
        fade_word(img, "TOI... OU TON CERVEAU ?", t, at('qui', "Toi"), 520, VIO, scale=3)


def sc_veto(img, t):
    img.paste(bg_deep())
    a = start('veto')
    d = ImageDraw.Draw(img)
    # flèche d'élan lancée...
    p = clamp((t - at('veto', "même quand")) / 1.2)
    d.line([40, 330, 40 + 260 * p, 330], fill=CYAN, width=6)
    if p > 0:
        x = 40 + 260 * p
        d.polygon([(x, 318), (x + 18, 330), (x, 342)], fill=CYAN)
    # ...arrêtée par une main
    vt = at('veto', "dire non")
    if t >= vt:
        q = ease_out_back((t - vt) / 0.3)
        hx, hy = 300, 330
        rr = 40 * min(q, 1.1)
        ell(d, hx, hy, rr, rr, (40, 10, 30), outline=RED, width=4)
        d.rounded_rectangle([hx - 16 * q, hy - 18 * q, hx + 16 * q, hy + 22 * q], radius=6, fill=(150, 95, 80))
    fade_word(img, "LES SCIENTIFIQUES", t, a, TOP, WHITE, scale=3)
    fade_word(img, "SE DISPUTENT ENCORE", t, a + 0.3, TOP + 32, (170, 180, 220), scale=2)
    if t >= at('veto', "Un véto"):
        pop_word(img, "VÉTO", t, at('veto', "Un véto"), 430, RED, scale=7)


def sc_encore(img, t):
    img.paste(bg_deep())
    network(img, t, GOLD, energy=0.8, drift=0.5)
    brain(img, CX, 300, 1.0, t, GOLD, fill=(40, 30, 15), pulse=(t * 0.5) % 1)
    secs = int(t)
    text(img, f"TU REGARDES DEPUIS {secs} S", 470, GOLD, scale=2)
    if t >= at('encore', "Et pourtant"):
        pop_word(img, "TU ES ENCORE LÀ", t, at('encore', "tu es encore"), TOP, WHITE, scale=4)
    else:
        fade_word(img, "TON CERVEAU T'A SOUFFLÉ DE SCROLLER", t, start('encore'), TOP, (200, 200, 230), scale=2)


def sc_fin(img, t):
    img.paste(bg_deep())
    network(img, t, CYAN, energy=1.0)
    brain(img, CX, 310, 1.15, t, CYAN, pulse=(t * 0.9) % 1)
    fade_word(img, "LA SEULE CHOSE", t, start('fin') + 0.3, TOP, WHITE, scale=4)
    fade_word(img, "QUE TU AS", t, at('fin', "que tu"), TOP + 44, WHITE, scale=4)
    if t >= at('fin', "vraiment"):
        pop_word(img, "VRAIMENT CHOISIE", t, at('fin', "vraiment"), 460, GOLD, scale=4)


SCENES = {'hook': sc_hook, 'attends': sc_attends, 'libet': sc_libet, 'electrodes': sc_electrodes,
          'scanner': sc_scanner, 'qui': sc_qui, 'veto': sc_veto, 'encore': sc_encore, 'fin': sc_fin}
CAMERA = {'hook': (1.0, 1.08, CX, 310), 'attends': (1.12, 1.0, CX, 330), 'libet': (1.0, 1.06, CX, 300),
          'electrodes': (1.0, 1.0, CX, 320), 'scanner': (1.0, 1.08, CX, 300), 'qui': (1.0, 1.06, CX, 320),
          'veto': (1.0, 1.0, CX, 330), 'encore': (1.0, 1.12, CX, 300), 'fin': (1.15, 1.0, CX, 310)}


# ================================================================ post-traitement
def bloom(img, strength=0.9):
    """Lueur néon : on floute les zones claires et on les ajoute."""
    bright = img.point(lambda v: max(0, v - 110) * 2)
    g1 = bright.filter(ImageFilter.GaussianBlur(4))
    g2 = bright.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H),
                                                                                                  Image.BILINEAR)
    glow = ImageChops.add(g1, g2)
    return ImageChops.add(img, Image.eval(glow, lambda v: int(v * strength)))


def chroma(img, amount):
    if amount < 1:
        return img
    r, g, b = img.split()
    r = ImageChops.offset(r, amount, 0)
    b = ImageChops.offset(b, -amount, 0)
    return Image.merge('RGB', (r, g, b))


def glitch(img, t, strength):
    a = np.array(img)
    rng = random.Random(int(t * 30))
    for _ in range(int(4 + 14 * strength)):
        y0 = rng.randrange(0, H - 6)
        h = rng.randrange(2, 14)
        dx = rng.randint(-int(30 * strength) - 1, int(30 * strength) + 1)
        a[y0:y0 + h] = np.roll(a[y0:y0 + h], dx, axis=1)
    return Image.fromarray(a)


def frame(t):
    pid = ST.para(t)
    img = Image.new('RGB', (W, H))
    fe.UI['layer'] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[pid](img, t)
    a, b = ST.ph[pid]
    img = fe.camera(img, t, *CAMERA[pid], a, b)
    img = bloom(img)
    img.paste(fe.UI['layer'], (0, 0), fe.UI['layer'])
    # le faux scroll du hook : l'image file vers le haut, la « vidéo suivante » arrive...
    if SCROLL_T <= t < SNAP_T + 0.15:
        p = ease_io(clamp((t - SCROLL_T) / max(0.3, SNAP_T - SCROLL_T)))
        p = min(p, 0.62)
        if t >= SNAP_T:
            p = 0.62 * (1 - clamp((t - SNAP_T) / 0.15))
        off = int(p * H)
        canvas = Image.new('RGB', (W, H))
        canvas.paste(img, (0, -off))
        canvas.paste(fake_next_video(t), (0, H - off))
        img = canvas
    # « Attends. » : rattrapage brutal + glitch
    if SNAP_T <= t < SNAP_T + 0.6:
        s = 1 - (t - SNAP_T) / 0.6
        img = chroma(glitch(img, t, s), int(6 * s))
    else:
        img = chroma(img, 1)
    # transitions courtes au noir + flash blanc sur les changements forts
    for bd in ST.bounds():
        d = t - bd
        if -0.18 <= d <= 0.18 and abs(bd - SNAP_T) > 0.5:
            img = Image.blend(img, BLACK, 0.7 * (1 - abs(d) / 0.18))
    img.paste(BLACK, (0, 0), fe.VIGNETTE)
    if t > DUR - 0.6:
        img = Image.blend(img, BLACK, clamp((t - (DUR - 0.6)) / 0.6))
    return img


SFX.append((0.0, 'impact', None))
SFX.append((SCROLL_T, 'whoosh', None))
SFX.append((SNAP_T, 'impact', None))
c0 = 5.80
for k in range(3):
    SFX.append((c0 + k * 0.7, 'place', 10 + k * 4))
SFX.append((start('libet'), 'coin', None))
SFX.append((at('electrodes', "Environ"), 'impact', None))
SFX.append((at('scanner', "jusqu'à sept"), 'impact', None))
SFX.append((at('veto', "Un véto"), 'impact', None))
SFX.append((at('fin', "vraiment"), 'sparkle', None))

if __name__ == '__main__':
    render(os.path.join(HERE, 'cerveau_decide_tiktok.mp4'), DUR, frame,
           os.path.join(HERE, 'audio', 'narration.mp3'), ST.ph, ST.end)
