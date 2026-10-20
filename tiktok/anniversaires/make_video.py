"""Vidéo TikTok pixel art : le paradoxe des anniversaires.

    python3 make_video.py                 # produit anniversaires_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle

Sans audio/narration.mp3, les phrases sont calées sur une durée estimée. Une
fois la voix enregistrée, remplacer MEASURED par les temps mesurés.
"""
import math
import os
import random
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 84          # centre des textes, décalé à gauche des boutons TikTok
TOP = 48         # sous la barre de recherche TikTok

# ---------------------------------------------------------------- narration
LINES = [
    ('hook', "Dans une classe de 23 élèves, il y a plus d'une chance sur deux que deux "
             "d'entre eux aient le même anniversaire."),
    ('imp', "Ça paraît impossible : il y a 365 jours dans l'année !"),
    ('para', "Et pourtant, ce sont des maths. C'est le paradoxe des anniversaires."),
    ('piege', "Le piège, c'est de penser à ton propre anniversaire."),
    ('paire', "Mais on ne cherche pas quelqu'un né le même jour que toi : on cherche "
              "n'importe quelle paire de personnes."),
    ('253', "Et avec 23 personnes, il y a déjà 253 paires possibles !"),
    ('calc', "Calculons la chance que personne ne partage son anniversaire."),
    ('frac', "Le deuxième doit éviter un jour : 364 sur 365. Le troisième, 363 sur 365. "
             "Et ainsi de suite."),
    ('mult', "On multiplie tout… et à 23 personnes, on tombe sous les 50 %."),
    ('donc', "Donc, plus d'une chance sur deux d'avoir un anniversaire en commun !"),
    ('graph', "Avec 50 personnes, on monte à 97 %. Et avec 70 personnes : 99,9 % !"),
    ('test', "Alors fais le test : écris ta date d'anniversaire en commentaire…"),
    ('meme', "…et regarde si quelqu'un a la même que toi !"),
    ('abo', "Abonne-toi pour plus d'anecdotes de maths !"),
]
SCENE_STARTS = {'imp': 0.8, 'para': 0.8, 'piege': 1.0, 'calc': 1.0, 'graph': 1.0, 'test': 1.0,
                'paire': 0.4, 'mult': 0.4, 'abo': 0.3}
# {id: (début, fin)} mesurés sur audio/narration.mp3 (silences > 0,12 s)
MEASURED = {
    'hook': (0.0, 5.51), 'imp': (5.96, 9.44), 'para': (9.83, 13.51), 'piege': (14.02, 16.39),
    'paire': (16.74, 21.45), '253': (21.72, 25.61), 'calc': (26.04, 28.74), 'frac': (29.17, 37.84),
    'mult': (38.16, 42.24), 'donc': (42.60, 45.57), 'graph': (45.96, 52.93), 'test': (53.36, 56.27),
    'meme': (56.57, 58.54), 'abo': (58.95, 60.85),
}


def estimate(rate=14.5, pause=0.4):
    out, t = {}, 0.1
    for pid, txt in LINES:
        d = len(txt) / rate
        out[pid] = (t, t + d)
        t += d + pause
    return out


PH = MEASURED or estimate()
ids = [pid for pid, _ in LINES]
GAPS = []
for pid, g in SCENE_STARTS.items():
    prev = ids[ids.index(pid) - 1]
    GAPS.append(((PH[prev][1] + PH[pid][0]) / 2, g))
GAPS.sort()
VOICE_END = PH[ids[-1]][1] + 0.2
N = Narration(os.path.join(HERE, 'audio', 'narration.mp3'), PH, GAPS, VOICE_END)
CUT = {pid: c for (c, _), pid in zip(GAPS, sorted(SCENE_STARTS, key=lambda k: PH[k][0]))}


def sb(pid):
    """Début de la scène qui s'ouvre sur la phrase pid."""
    return N.B(CUT[pid])


DUR = N.V(VOICE_END) + 2.0

# ---------------------------------------------------------------- sprites
SKINS = [PEACH, (230, 170, 120), BROWN, (120, 70, 40)]
SHIRTS = [RED, BLUE, GREEN, ORANGE, PINK, LAVENDER, YELLOW]
HAIRS = [INK, BROWN, ORANGE, (90, 60, 30), YELLOW]
_r = random.Random(23)
CROWD = [(_r.choice(SKINS), _r.choice(SHIRTS), _r.choice(HAIRS)) for _ in range(23)]


def person(img, x, y, look, hl=False, t=0.0):
    skin, shirt, hair = look
    x, y = int(x) - 3, int(y) - 6
    if hl:
        c = YELLOW if int(t * 6) % 2 else ORANGE
        img.paste(c, (x - 2, y - 2, x + 9, y + 14))
        img.paste(SHADOW, (x - 1, y - 1, x + 8, y + 13))
    img.paste(hair, (x + 2, y, x + 5, y + 1))
    img.paste(skin, (x + 2, y + 1, x + 5, y + 4))
    img.paste(INK, (x + 2, y + 2, x + 3, y + 3))
    img.paste(INK, (x + 4, y + 2, x + 5, y + 3))
    img.paste(shirt, (x + 1, y + 4, x + 6, y + 9))
    img.paste(skin, (x, y + 5, x + 1, y + 8))
    img.paste(skin, (x + 6, y + 5, x + 7, y + 8))
    img.paste(INK, (x + 2, y + 9, x + 3, y + 12))
    img.paste(INK, (x + 4, y + 9, x + 5, y + 12))


CAKE = [
    "....r..r..r....",
    "....y..y..y....",
    "....w..w..w....",
    "....w..w..w....",
    "..ppppppppppp..",
    ".pwwpwwwpwwwpw.",
    ".ppppppppppppp.",
    ".bbbbbbbbbbbbb.",
    ".bbbbbbbbbbbbb.",
    ".yyyyyyyyyyyyy.",
    ".bbbbbbbbbbbbb.",
    ".bbbbbbbbbbbbb.",
    "lllllllllllllll",
]
CAKE_COL = {'p': PINK, 'w': WHITE, 'b': BROWN, 'y': YELLOW, 'l': LGREY, 'r': ORANGE}


def cake(img, cx, cy, scale, t):
    h, w = len(CAKE), len(CAKE[0])
    x0, y0 = int(cx - w * scale / 2), int(cy - h * scale / 2)
    for r, row in enumerate(CAKE):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            col = CAKE_COL[ch]
            if ch == 'r':      # flammes qui vacillent
                col = (ORANGE, YELLOW, RED)[int(t * 10 + c) % 3]
            if ch == 'y' and r == 1:
                col = YELLOW if int(t * 8 + c) % 2 else WHITE
            img.paste(col, (x0 + c * scale, y0 + r * scale, x0 + (c + 1) * scale, y0 + (r + 1) * scale))


MONTHS = ["JANV", "FÉVR", "MARS", "AVR", "MAI", "JUIN", "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"]


def calendar(img, cx, cy, day, month):
    x0, y0 = cx - 30, cy - 30
    img.paste(SHADOW, (x0 + 3, y0 + 3, x0 + 63, y0 + 63))
    img.paste(WHITE, (x0, y0, x0 + 60, y0 + 60))
    img.paste(LGREY, (x0, y0 + 57, x0 + 60, y0 + 60))
    img.paste(RED, (x0, y0, x0 + 60, y0 + 16))
    for bx in (12, 44):
        img.paste(DGREY, (x0 + bx, y0 - 4, x0 + bx + 3, y0 + 4))
    draw_text(img, MONTHS[month], cx, y0 + 3, WHITE, shadow=None, maxw=60)
    draw_text(img, str(day), cx, y0 + 18, INK, scale=3, shadow=None, maxw=60)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def p_match(n):
    q = 1.0
    for k in range(n):
        q *= (365 - k) / 365
    return 1 - q


def pct(v, dec=1):
    return f"{v * 100:.{dec}f}".replace('.', ',') + " %"


# ================================================================ SCÈNES
# 1 ─ accroche : tout est lisible dès la première image ------------------
GRID = [(CX - 45 + (i % 6) * 18, 84 + (i // 6) * 22) for i in range(23)]
TWINS = (8, 20)
SFX.append((0.0, 'crash', None))
SFX.append((N.start('hook') + 2.0, 'coin', None))


@scene(0.0, sb('imp'))
def s1(img, t):
    pulse = 1 if int(t * 2) % 2 else 0
    draw_text(img, "23 PERSONNES", CX, TOP - pulse, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    lit = t > N.start('hook') + 2.0
    if lit:
        (ax, ay), (bx, by) = GRID[TWINS[0]], GRID[TWINS[1]]
        d = ImageDraw.Draw(img)
        for k in range(0, 40, 2):
            u0, u1 = k / 40, (k + 1) / 40
            d.line([(ax + (bx - ax) * u0, ay + (by - ay) * u0),
                    (ax + (bx - ax) * u1, ay + (by - ay) * u1)], fill=YELLOW)
    for i, (x, y) in enumerate(GRID):
        person(img, x, y + (1 if (int(t * 4) + i) % 5 == 0 else 0), CROWD[i], lit and i in TWINS, t)
    if lit:
        for i in TWINS:
            x, y = GRID[i]
            cake(img, x, y - 13 - int(math.sin(t * 6) * 1.5), 1, t)
    draw_text(img, "= *PLUS D'1 CHANCE SUR 2* QUE 2 D'ENTRE ELLES AIENT LE *MÊME ANNIVERSAIRE*",
              CX, 182, maxw=140)


# 2 ─ 365 jours ---------------------------------------------------------
S2_T = N.text("ÇA PARAÎT IMPOSSIBLE : IL Y A *365 JOURS* DANS L'ANNÉE !", 'imp', 170)


@scene(sb('imp'), sb('para'))
def s2(img, t):
    lt = t - sb('imp')
    k = int(lt * 14)
    calendar(img, CX, 100, k % 31 + 1, (k // 9) % 12)
    S2_T.draw(img, t, CX)


for i in range(int((sb('para') - sb('imp')) * 7)):
    SFX.append((sb('imp') + i / 7, 'blip', None))

# 3 ─ le paradoxe -------------------------------------------------------
PARA_T = N.V(11.66)  # « C'est le paradoxe... »
impact(PARA_T, 3)
SFX.append((PARA_T + 0.05, 'sparkle', None))
S3_TXT = "ET POURTANT, CE SONT DES *MATHS*."
S3_T = T(S3_TXT, N.start('para'), 205, cps=len(S3_TXT) / (N.V(11.33) - N.start('para')))


@scene(sb('para'), sb('piege'))
def s3(img, t):
    cake(img, CX, 140, 4, t)
    if t >= PARA_T:
        p = ease_out_back((t - PARA_T) / 0.4)
        draw_text(img, "LE PARADOXE DES ANNIVERSAIRES", CX, int(TOP - 20 + 20 * p), YELLOW,
                  scale=2, maxw=170, shadow=PURPLE)
        lt = t - PARA_T
        px = img.load()
        for i in range(30):
            a = i * 0.9 + lt * 0.4
            d = 30 + lt * 25 + (i % 4) * 6
            x, y = CX + math.cos(a) * d, 140 + math.sin(a) * d * 0.6
            if 0 <= x < W and 0 <= y < H and (int(lt * 10) + i) % 3:
                px[int(x), int(y)] = RAINBOW[i % 6]
    S3_T.draw(img, t, CX)


# 4 ─ le piège : toutes les paires ---------------------------------------
RING_C, RING_R = (CX, 118), 50
RING = [(RING_C[0] + RING_R * math.sin(2 * math.pi * i / 23),
         RING_C[1] - RING_R * math.cos(2 * math.pi * i / 23)) for i in range(23)]
PAIRS = [(i, j) for i in range(23) for j in range(i + 1, 23)]
_r.shuffle(PAIRS)
ME_LINES0, ME_LINES1 = N.start('piege') + 0.5, N.stop('piege')
ALL0, ALL1 = N.start('paire') + 1.0, N.start('253') + 1.0
BIG253 = N.stop('253') - 1.4
impact(BIG253, 3)
SFX.append((BIG253 + 0.05, 'coin', None))
for k in range(22):
    SFX.append((ME_LINES0 + (ME_LINES1 - ME_LINES0) * k / 22, 'place', k))
S4_T1 = N.text("LE PIÈGE : PENSER À *TON* ANNIVERSAIRE", 'piege', 200)
S4_T2 = N.text("MAIS ON CHERCHE *N'IMPORTE QUELLE PAIRE* DE PERSONNES", 'paire', 200)
S4_T3 = N.text("AVEC 23 PERSONNES : *253 PAIRES* POSSIBLES !", '253', 200)


@scene(sb('piege'), sb('calc'))
def s4(img, t):
    d = ImageDraw.Draw(img)
    me = 0
    if t < N.start('paire'):
        n = int(22 * clamp((t - ME_LINES0) / (ME_LINES1 - ME_LINES0)))
        for j in range(1, n + 1):
            d.line([RING[me], RING[j]], fill=YELLOW if j == n else LAVENDER)
    else:
        n = int(253 * clamp((t - ALL0) / (ALL1 - ALL0)) ** 1.5)
        for k, (i, j) in enumerate(PAIRS[:n]):
            d.line([RING[i], RING[j]], fill=RAINBOW[k % 6] if k > n - 8 else (70, 60, 120))
        if t < BIG253:
            draw_text(img, str(n), CX, RING_C[1] - 8, WHITE, scale=2)
    for i, (x, y) in enumerate(RING):
        person(img, x, y, CROWD[i], i == me and t < N.start('paire'), t)
    if t < N.start('paire'):
        draw_text(img, "TOI", int(RING[me][0]), int(RING[me][1]) - 22, YELLOW)
    if t >= BIG253:
        p = ease_out_back((t - BIG253) / 0.4)
        img.paste(SHADOW, (CX - 44, RING_C[1] - 18, CX + 44, RING_C[1] + 18))
        draw_text(img, "253", CX, int(RING_C[1] - 16 + (1 - p) * 10), YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "PAIRES", CX, RING_C[1] + 4, WHITE)
    for tx, nxt in ((S4_T1, S4_T2), (S4_T2, S4_T3), (S4_T3, None)):
        if nxt is None or t < nxt.t0:
            tx.draw(img, t, CX)


# 5 ─ le calcul ----------------------------------------------------------
FRACS = ["1RE : 365/365", "2E : 364/365", "3E : 363/365", "...", "23E : 343/365"]
F0, F1 = N.start('frac'), N.stop('frac')
FRAC_T = [F0 + (F1 - F0) * k / len(FRACS) for k in range(len(FRACS))]
for ft in FRAC_T:
    SFX.append((ft, 'place', 10))
BAR0, BAR1 = N.start('mult'), N.stop('mult')
for k in range(23):
    SFX.append((BAR0 + (BAR1 - BAR0) * k / 23, 'place', k))
FLIP = N.start('donc')
impact(FLIP, 3)
SFX.append((FLIP + 0.05, 'sparkle', None))
S5_T1 = N.text("CALCULONS LA CHANCE QUE *PERSONNE* NE PARTAGE SON ANNIVERSAIRE", 'calc', 200)
S5_T2 = N.text("ON MULTIPLIE TOUT...", 'mult', 200)
S5_T3 = N.text("PLUS D'*1 CHANCE SUR 2* D'AVOIR UN ANNIVERSAIRE EN COMMUN !", 'donc', 200)


@scene(sb('calc'), sb('graph'))
def s5(img, t):
    for k, (txt, ft) in enumerate(zip(FRACS, FRAC_T)):
        if t >= ft:
            draw_text(img, txt, CX, TOP + k * 13, LGREY if k < 4 else WHITE)
    if t >= BAR0:
        n = 1 + int(22 * clamp((t - BAR0) / (BAR1 - BAR0)))
        q = 1 - p_match(n)
        x0, x1, y0 = 22, 146, 128
        flipped = t >= FLIP
        lab = "AU MOINS UNE PAIRE" if flipped else f"PERSONNE EN COMMUN (N = {n})"
        draw_text(img, lab, CX, y0 - 14, GREEN if flipped else WHITE, maxw=170)
        img.paste(SHADOW, (x0 - 1, y0 - 1, x1 + 1, y0 + 13))
        img.paste((40, 40, 80), (x0, y0, x1, y0 + 12))
        v = 1 - q if flipped else q
        img.paste(GREEN if flipped else RED, (x0, y0, x0 + int((x1 - x0) * v), y0 + 12))
        mid = (x0 + x1) // 2
        img.paste(WHITE, (mid, y0 - 2, mid + 1, y0 + 14))
        draw_text(img, pct(v), CX, y0 + 17, GREEN if flipped else YELLOW,
                  scale=2 if flipped else 1, shadow=PURPLE)
    if t < S5_T2.t0:
        S5_T1.draw(img, t, CX)
    elif t < S5_T3.t0:
        S5_T2.draw(img, t, CX)
    else:
        S5_T3.draw(img, t, CX)


# 6 ─ la courbe ----------------------------------------------------------
GX0, GX1, GY0, GY1, NMAX = 36, 146, 70, 170, 75
# progression de la courbe calée sur la voix : (temps voix, n)
GKEYS = [(N.start('graph') - 0.4, 0), (N.V(47.3), 50), (N.V(49.5), 70), (N.V(50.6), NMAX)]


def n_at(t):
    for (ta, na), (tb, nb) in zip(GKEYS, GKEYS[1:]):
        if t < tb:
            return na + (nb - na) * clamp((t - ta) / (tb - ta))
    return NMAX


def t_at(n):
    for (ta, na), (tb, nb) in zip(GKEYS, GKEYS[1:]):
        if n <= nb:
            return ta + (tb - ta) * (n - na) / (nb - na)
    return GKEYS[-1][0]


MARKS = [(23, "23 : 50,7 %"), (50, "50 : 97 %"), (70, "70 : 99,9 %")]
MARK_T = [t_at(m) for m, _ in MARKS]
for mt in MARK_T:
    SFX.append((mt, 'coin', None))
S6_T = N.text("*50 PERSONNES* : 97 %\n*70 PERSONNES* : 99,9 % !", 'graph', 200)


def gx(n):
    return GX0 + (GX1 - GX0) * n / NMAX


def gy(v):
    return GY1 - (GY1 - GY0) * v


@scene(sb('graph'), sb('test'))
def s6(img, t):
    draw_text(img, "ET ÇA GRIMPE VITE !", CX, TOP - 6, YELLOW)
    d = ImageDraw.Draw(img)
    d.line([(GX0, GY0 - 4), (GX0, GY1)], fill=LGREY)
    d.line([(GX0, GY1), (GX1 + 4, GY1)], fill=LGREY)
    for x in range(GX0, GX1, 4):
        img.putpixel((x, int(gy(0.5))), DGREY)
        img.putpixel((x, int(gy(1))), DGREY)
    draw_text(img, "100%", 18, GY0 - 6, LGREY, shadow=None)
    draw_text(img, "50%", 18, int(gy(0.5)) - 6, LGREY, shadow=None)
    draw_text(img, "PERSONNES", CX + 8, GY1 + 4, LGREY, shadow=None)
    n_now = n_at(t)
    pts = [(gx(n / 2), gy(p_match(int(n / 2)))) for n in range(int(n_now * 2) + 1)]
    if len(pts) > 1:
        d.line(pts, fill=GREEN, width=2)
    if pts:
        x, y = pts[-1]
        img.paste(WHITE, (int(x) - 1, int(y) - 1, int(x) + 2, int(y) + 2))
    for k, ((m, lab), mt) in enumerate(zip(MARKS, MARK_T)):
        if t >= mt:
            x, y = gx(m), gy(p_match(m))
            img.paste(YELLOW, (int(x) - 2, int(y) - 2, int(x) + 3, int(y) + 3))
            lx, ly = (int(x) + 36, int(y) - 3) if k == 0 else (116, 123 + k * 13)
            draw_text(img, lab, lx, ly, YELLOW if k == 0 else WHITE)
    S6_T.draw(img, t, CX)


# 7 ─ à toi de jouer ---------------------------------------------------
HB = [(67, .75), (67, .25), (69, 1), (67, 1), (72, 1), (71, 2),
      (67, .75), (67, .25), (69, 1), (67, 1), (74, 1), (72, 2),
      (67, .75), (67, .25), (79, 1), (76, 1), (72, 1), (71, 1), (69, 2),
      (77, .75), (77, .25), (76, 1), (72, 1), (74, 1), (72, 3)]
SFX.append((sb('test') + 0.2, 'melody', HB))
S7_T1 = N.text("ÉCRIS TA *DATE D'ANNIVERSAIRE* EN COMMENTAIRE", 'test', 132)
S7_T2 = N.text("... ET REGARDE SI QUELQU'UN A LA MÊME QUE TOI !", 'meme', 210)
ABO_T = N.start('abo')
SFX.append((ABO_T, 'coin', None))
CONF = [(_r.randrange(W), _r.random() * 300, 15 + _r.random() * 25, _r.choice(RAINBOW))
        for _ in range(40)]


@scene(sb('test'), DUR)
def s7(img, t):
    lt = t - sb('test')
    for x, y0, sp, col in CONF:
        y = (y0 + lt * sp) % 320
        img.paste(col, (int(x + math.sin(lt * 3 + y0) * 3), int(y), int(x + math.sin(lt * 3 + y0) * 3) + 2,
                        int(y) + 2))
    cake(img, CX, 95, 3, t)
    S7_T1.draw(img, t, CX)
    if t >= S7_T1.t0 + 0.5:
        arrow(img, 128 + abs(math.sin(lt * 5)) * 6, 179)
    S7_T2.draw(img, t, CX)
    if t >= ABO_T:
        p = ease_out_back((t - ABO_T) / 0.4)
        y = int(TOP - 6 - (1 - p) * 20)
        img.paste(RED, (CX - 40, y, CX + 40, y + 16))
        img.paste(PINK, (CX - 40, y, CX + 40, y + 2))
        draw_text(img, "+ ABONNE-TOI", CX, y + 1, WHITE, shadow=PURPLE)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'anniversaires_tiktok.mp4'), DUR, N,
                 music=dict(bpm=124,
                            chords=[[72, 76, 79, 84], [71, 74, 79, 83], [69, 72, 76, 81], [65, 69, 72, 77]],
                            roots=[48, 43, 45, 41], climax=sb('test')))
