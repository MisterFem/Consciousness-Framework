"""Vidéo TikTok pixel art : trois problèmes, les réponses de LFI, concrètement.

Structure : accroche -> 3 blocs (problème -> réponse -> mécanismes) -> fin
qui boucle. Les mesures se cochent à l'écran au moment où la voix les dit.

    python3 make_video.py                 # produit lfi_programme_tiktok.mp4
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
MAXW = 144       # TikTok rogne les côtés sur les écrans allongés

# ---------------------------------------------------------------- narration
LINES = [
    ('hook', "Salaires, ultra-riches, retraite à 60 ans : voilà ce que propose la France insoumise. "
             "Pas en slogans : concrètement."),
    ('com', "Et dis-moi en commentaire quelle mesure tu veux qu'on détaille."),
    ('d1', "Problème numéro un : la vie coûte trop cher. En deux ans, les prix de l'alimentation "
           "ont grimpé de près de 20 %, et les salaires n'ont pas suivi."),
    ('r1', "La réponse de LFI : augmenter directement ce que les ménages modestes ont en poche."),
    ('m1', "Concrètement : le SMIC à 1 600 euros net. Des salaires indexés sur l'inflation : quand "
           "les prix montent, ta paie monte aussi. Et des prix bloqués sur les produits de première "
           "nécessité."),
    ('d2', "Problème numéro deux : l'argent existe, mais il est concentré. Les 500 plus grandes "
           "fortunes de France pèsent plus de 1 000 milliards d'euros. Et la fraude fiscale "
           "coûterait entre 60 et 100 milliards par an."),
    ('r2', "La réponse : faire contribuer les plus gros patrimoines."),
    ('m2', "Concrètement : le retour de l'ISF, une taxe sur les superprofits, et plus de contrôleurs "
           "contre la fraude."),
    ('h2', "Et pour l'héritage : rien à payer jusqu'à 120 000 euros par enfant, puis un impôt "
           "progressif, avec un plafond : au-delà de 12 millions, c'est prélevé."),
    ('d3', "Problème numéro trois : la retraite à 64 ans. Alors qu'un ouvrier vit en moyenne six ans "
           "de moins qu'un cadre."),
    ('r3', "La réponse : abroger la réforme, et viser la retraite à 60 ans."),
    ('m3', "Concrètement, on la finance par les cotisations : augmenter les salaires, c'est aussi "
           "augmenter les cotisations qui paient les retraites."),
    ('fin', "Trois problèmes, trois réponses, des mécanismes concrets. Alors, quelle mesure tu veux "
            "qu'on détaille ?"),
]
SCENE_STARTS = {'com': 0.2, 'd1': 0.6, 'r1': 0.6, 'd2': 1.0, 'r2': 0.6, 'd3': 1.0, 'r3': 0.6,
                'fin': 1.0}
INNER_GAPS = {'m1': 0.4, 'm2': 0.4, 'h2': 0.6, 'm3': 0.4}
MEASURED = None  # {id: (début, fin)} mesurés sur audio/narration.mp3


def estimate(rate=17.0, pause=0.3):
    out, t = {}, 0.05
    for pid, txt in LINES:
        d = len(txt) / rate
        out[pid] = (t, t + d)
        t += d + pause
    return out


PH = MEASURED or estimate()
TXT = dict(LINES)
ids = [pid for pid, _ in LINES]
CUT, GAPS = {}, []
for pid, g in {**SCENE_STARTS, **INNER_GAPS}.items():
    prev = ids[ids.index(pid) - 1]
    CUT[pid] = (PH[prev][1] + PH[pid][0]) / 2
    GAPS.append((CUT[pid], g))
GAPS.sort()
VOICE_END = PH[ids[-1]][1] + 0.1
N = Narration(os.path.join(HERE, 'audio', 'narration.mp3'), PH, GAPS, VOICE_END)


def sb(pid):
    """Début de la scène qui s'ouvre sur la phrase pid."""
    return N.B(CUT[pid])


def at(pid, words):
    """Moment (vidéo) où la voix prononce `words` dans la phrase pid."""
    a, b = PH[pid]
    i = TXT[pid].index(words)
    return N.V(a + (b - a) * i / len(TXT[pid]))


DUR = N.V(VOICE_END) + 1.2


# ---------------------------------------------------------------- outils
def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def big_sprite(img, spr, cx, cy, scale):
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


def pop(t, t0, dur=0.35):
    return ease_out_back((t - t0) / dur)


def box(img, y0, y1):
    img.paste(SHADOW, (14, y0, 156, y1))


def checklist(img, t, items, y0, dy=16):
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
        draw_text(img, txt, x + 13 + layout_w(txt) // 2, y + 1, WHITE, maxw=140)


def layout_w(txt):
    return max(w for _, w in layout(txt, 140))


def header(img, label, col, t, t0):
    p = pop(t, t0)
    w = layout_w(label) + 10
    y = int(TOP - 8 - (1 - p) * 12)
    img.paste(col, (CX - w // 2, y, CX + w // 2, y + 13))
    draw_text(img, label, CX, y + 1, WHITE, shadow=None)


CART = art(["c.........",
            "cccccccccc",
            ".cwwwwwwc.",
            ".cwwwwwwc.",
            "..cccccc..",
            "..c....c..",
            "..k....k.."],
           {'c': LGREY, 'w': ORANGE, 'k': INK})
COIN = art([".yyyy.", "yyooyy", "yoyyoy", "yoyyoy", "yyooyy", ".yyyy."],
           {'y': YELLOW, 'o': ORANGE})
WORKER = art(["..oo..", "..oo..", "..ss..", ".bbbb.", "sbbbbs", ".bbbb.", ".b..b.", ".k..k."],
             {'o': ORANGE, 's': PEACH, 'b': BLUE, 'k': INK})
SUIT = art(["..kk..", "..kk..", "..ss..", ".dwwd.", "sdwwds", ".dddd.", ".d..d.", ".k..k."],
           {'k': INK, 's': PEACH, 'd': DGREY, 'w': WHITE})


def stars_burst(img, t, t0, cx, cy, n=24):
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


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


# ================================================================ SCÈNES
# 0 ─ accroche (lisible dès la première image) + commentaire ------------
SFX.append((0.0, 'crash', None))
HOOK_ITEMS = [("SALAIRES", RED), ("ULTRA-RICHES", YELLOW), ("RETRAITE", GREEN)]
COM_T = N.start('com')
SFX.append((COM_T, 'coin', None))


def hook_screen(img, t, bottom):
    for k, (txt, col) in enumerate(HOOK_ITEMS):
        y = TOP + 6 + k * 30
        wob = int(math.sin(t * 4 + k) * 1.5)
        draw_text(img, txt, CX, y + wob, col, scale=2, shadow=PURPLE, maxw=MAXW + 6)
    draw_text(img, "LE PROGRAMME DE LFI", CX, 150, WHITE, maxw=MAXW)
    draw_text(img, "*CONCRÈTEMENT*, SANS SLOGANS", CX, 164, WHITE, maxw=MAXW)
    if bottom:
        box(img, 200, 238)
        draw_text(img, bottom[0], CX, 202, WHITE, scale=2, maxw=MAXW + 6)
        draw_text(img, bottom[1], CX, 220, YELLOW, scale=2, shadow=PURPLE, maxw=MAXW + 6)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 182)


@scene(0.0, sb('d1'))
def s0(img, t):
    hook_screen(img, t, ("QUELLE MESURE", "ON DÉTAILLE ?") if t >= COM_T else None)


# 1 ─ la vie coûte trop cher --------------------------------------------
B1_FOOD = at('d1', "les prix")
B1_SAL = at('d1', "et les salaires")
impact(B1_FOOD + 0.6, 2)


@scene(sb('d1'), sb('r1'))
def s1(img, t):
    header(img, "PROBLÈME N°1", RED, t, sb('d1'))
    draw_text(img, "LA VIE COÛTE", CX, TOP + 12, WHITE, scale=2, maxw=MAXW + 6)
    draw_text(img, "TROP CHER", CX, TOP + 30, YELLOW, scale=2, shadow=PURPLE, maxw=MAXW + 6)
    base = 196
    if t >= B1_FOOD:
        hp = 66 * ease_io((t - B1_FOOD) / 0.8)
        img.paste(RED, (34, int(base - hp), 64, base))
        draw_text(img, "+20 %", 49, int(base - hp) - 22, RED, scale=2, shadow=SHADOW)
        big_sprite(img, CART, 49, base + 14, 2)
        draw_text(img, "ALIMENTATION", 49, int(base - hp) - 8, WHITE, maxw=80, shadow=SHADOW)
    if t >= B1_SAL:
        hs = 18 * ease_io((t - B1_SAL) / 0.8)
        img.paste(LAVENDER, (98, int(base - hs), 128, base))
        draw_text(img, "SALAIRES", 113, int(base - hs) - 12, WHITE)
        draw_text(img, "?", 113, int(base - hs) - 26, LGREY, scale=2)
    img.paste(LGREY, (24, base, 140, base + 1))
    draw_text(img, "EN DEUX ANS", CX, 230, LGREY)


# réponse + mécanismes ---------------------------------------------------
M1 = [(at('m1', "le SMIC"), "SMIC À *1 600 € NET*"),
      (at('m1', "Des salaires"), "SALAIRES *INDEXÉS SUR L'INFLATION*"),
      (at('m1', "Et des prix"), "*PRIX BLOQUÉS* SUR L'ESSENTIEL")]


def response(img, t, start, text, items, extra=None):
    header(img, "LA RÉPONSE LFI", BLUE, t, start)
    draw_text(img, text, CX, TOP + 12, WHITE, maxw=MAXW)
    first = items[0][0] if items else 1e9
    if t >= first - 0.5:
        p = pop(t, first - 0.5)
        draw_text(img, "CONCRÈTEMENT :", CX, int(TOP + 52 + (1 - p) * 6), YELLOW, scale=2,
                  shadow=PURPLE, maxw=MAXW + 6)
    checklist(img, t, items, TOP + 78, dy=30)
    if extra:
        extra(img, t)


for ti, _ in M1:
    SFX.append((ti, 'place', 12))


def wage_meter(img, t):
    # « quand les prix montent, ta paie monte aussi »
    t0 = at('m1', "quand")
    t1 = at('m1', "Et des prix")
    if not t0 <= t < t1 + 0.3:
        return
    p = clamp((t - t0) / (t1 - t0))
    for k, (lab, col) in enumerate((("PRIX", RED), ("PAIE", GREEN))):
        x = 120 + k * 22
        hgt = int(8 + 30 * ease_io(p))
        img.paste(col, (x, 236 - hgt, x + 14, 236))
        draw_text(img, lab, x + 7, 238 - hgt - 12, col)


@scene(sb('r1'), sb('d2'))
def s1b(img, t):
    response(img, t, sb('r1'), "AUGMENTER CE QUE LES MÉNAGES MODESTES ONT *EN POCHE*", M1, wage_meter)


# 2 ─ l'argent existe, mais il est concentré -----------------------------
B2_500 = at('d2', "Les 500")
B2_1000 = at('d2', "plus de 1 000")
B2_FRAUD = at('d2', "Et la fraude")
impact(B2_1000 + 0.3, 3)
SFX.append((B2_FRAUD, 'coin', None))


@scene(sb('d2'), sb('r2'))
def s2(img, t):
    header(img, "PROBLÈME N°2", RED, t, sb('d2'))
    draw_text(img, "L'ARGENT", CX, TOP + 12, WHITE, scale=2, maxw=MAXW + 6)
    draw_text(img, "EXISTE...", CX, TOP + 30, WHITE, scale=2, maxw=MAXW + 6)
    draw_text(img, "MAIS IL EST *CONCENTRÉ*", CX, TOP + 56, WHITE, maxw=MAXW)
    if t >= B2_500:
        # piles de pièces qui montent
        n = int(clamp((t - B2_500) / 1.4) * 7)
        for k in range(n):
            for j in range(3):
                big_sprite(img, COIN, 40 + j * 18, 156 - k * 5, 2)
        draw_text(img, "500 FORTUNES", 58, 168, WHITE)
    if t >= B2_1000 + 0.3:
        p = pop(t, B2_1000 + 0.3)
        draw_text(img, "+ DE", 124, int(124 + (1 - p) * 8), WHITE)
        draw_text(img, "1 000", 124, 136, YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "MILLIARDS €", 124, 156, YELLOW)
        stars_burst(img, t, B2_1000 + 0.3, 124, 144)
    if t >= B2_FRAUD:
        box(img, 190, 238)
        draw_text(img, "FRAUDE FISCALE :", CX, 192, WHITE)
        draw_text(img, "60 À 100 MDS € / AN", CX, 206, RED, scale=1, maxw=MAXW)
        draw_text(img, "(ESTIMATIONS)", CX, 222, LGREY)


M2 = [(at('m2', "le retour"), "RETOUR DE *L'ISF*"),
      (at('m2', "une taxe"), "TAXE SUR LES *SUPERPROFITS*"),
      (at('m2', "et plus de"), "+ DE *CONTRÔLEURS FISCAUX*")]
for ti, _ in M2:
    SFX.append((ti, 'place', 12))
H_ZERO, H_PROG, H_CAP = at('h2', "rien à payer"), at('h2', "puis un impôt"), at('h2', "au-delà")
impact(H_CAP + 0.4, 3)


def heritage(img, t):
    """Jauge de l'héritage : 0 € jusqu'à 120 000 €, progressif, plafond 12 M€."""
    if t < N.start('h2'):
        return
    y = 200
    x0, x1, x2, x3 = 18, 52, 132, 152
    draw_text(img, "HÉRITAGE (PAR ENFANT)", CX, y - 38, WHITE)
    if t >= H_ZERO:
        img.paste(GREEN, (x0, y, x1, y + 10))
        draw_text(img, "0 €", (x0 + x1) // 2, y + 12, GREEN)
        draw_text(img, "120 000 €", x1, y - 13, LGREY)
    if t >= H_PROG:
        p = clamp((t - H_PROG) / 1.0)
        for x in range(x1, int(x1 + (x2 - x1) * p)):
            u = (x - x1) / (x2 - x1)
            col = YELLOW if u < 0.33 else (ORANGE if u < 0.66 else RED)
            img.paste(col, (x, y + 10 - int(2 + 8 * u), x + 1, y + 10))
        draw_text(img, "PROGRESSIF", (x1 + x2) // 2, y + 12, ORANGE)
    if t >= H_CAP:
        img.paste(WHITE, (x2, y - 14, x2 + 1, y + 12))
        img.paste(PURPLE, (x2 + 1, y, x3, y + 10))
        if t >= H_CAP + 0.4:
            draw_text(img, "12 M€", x2, y - 13, YELLOW)
            draw_text(img, "PLAFOND", x2 - 6, y - 25, YELLOW)


@scene(sb('r2'), sb('d3'))
def s2b(img, t):
    items = M2 if t < N.start('h2') else []
    response(img, t, sb('r2'), "FAIRE CONTRIBUER LES *PLUS GROS PATRIMOINES*", items, heritage)
    if t >= N.start('h2'):
        draw_text(img, "CONCRÈTEMENT :", CX, TOP + 52, YELLOW, scale=2, shadow=PURPLE, maxw=MAXW + 6)
        draw_text(img, "✓ ISF  ✓ SUPERPROFITS  ✓ FRAUDE", CX, TOP + 76, LGREY, maxw=MAXW + 10)


# 3 ─ la retraite -------------------------------------------------------
B3_AGE = sb('d3') + 0.5
B3_LIFE = at('d3', "Alors qu'un")
SFX.append((B3_AGE + 0.6, 'impact', None))


@scene(sb('d3'), sb('r3'))
def s3(img, t):
    header(img, "PROBLÈME N°3", RED, t, sb('d3'))
    age = 62 + int(2 * clamp((t - B3_AGE) / 0.6)) if t >= B3_AGE else 62
    draw_text(img, "RETRAITE", CX, TOP + 12, WHITE, scale=2)
    draw_text(img, f"{age} ANS", CX, TOP + 30, RED if age == 64 else WHITE, scale=3, shadow=PURPLE)
    if t >= B3_LIFE:
        p = clamp((t - B3_LIFE) / 1.2)
        for k, (spr, lab, years, col) in enumerate(((SUIT, "CADRE", 1.0, BLUE),
                                                     (WORKER, "OUVRIER", 0.92, ORANGE))):
            y = 140 + k * 34
            big_sprite(img, spr, 26, y + 6, 2)
            ln = int(110 * years * ease_io(p))
            img.paste(col, (40, y, 40 + ln, y + 10))
            draw_text(img, lab, 40 + ln // 2, y + 12, col)
        if p >= 1:
            img.paste(RED, (142, 174, 150, 184))
            draw_text(img, "-6 ANS", 132, 194, RED, scale=2, shadow=PURPLE)
        draw_text(img, "ESPÉRANCE DE VIE", CX, 124, LGREY)


M3 = [(at('m3', "Concrètement"), "*FINANCÉ PAR LES COTISATIONS*"),
      (at('m3', "augmenter les salaires"), "+ DE SALAIRE = + DE *COTISATIONS*"),
      (at('m3', "qui paient"), "= DES *RETRAITES FINANCÉES*")]
for ti, _ in M3:
    SFX.append((ti, 'place', 12))
R3_AGE = at('r3', "et viser")
SFX.append((R3_AGE + 0.5, 'sparkle', None))


@scene(sb('r3'), sb('fin'))
def s3b(img, t):
    if t < M3[0][0] - 0.5:
        header(img, "LA RÉPONSE LFI", BLUE, t, sb('r3'))
        draw_text(img, "ABROGER LA RÉFORME DES 64 ANS", CX, TOP + 14, WHITE, maxw=MAXW)
        age = 64 - int(4 * clamp((t - R3_AGE) / 0.6)) if t >= R3_AGE else 64
        draw_text(img, "OBJECTIF", CX, 110, WHITE, scale=2)
        draw_text(img, f"{age} ANS", CX, 130, GREEN if age == 60 else RED, scale=3, shadow=PURPLE)
        if age == 60:
            stars_burst(img, t, R3_AGE + 0.6, CX, 150)
        return
    response(img, t, sb('r3'), "RETRAITE À 60 ANS, ET VOICI COMMENT ON LA PAIE", M3)


# fin ─ récap + retour à l'accroche -------------------------------------
@scene(sb('fin'), DUR)
def s4(img, t):
    hook_screen(img, t, ("QUELLE MESURE", "ON DÉTAILLE ?"))
    lt = t - sb('fin')
    for k in range(3):
        if lt > 0.3 + k * 0.5:
            stamp(img, FONT['✓'], 150, TOP + 9 + k * 30, GREEN)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'lfi_programme_tiktok.mp4'), DUR, N, loop=True,
                 music=dict(bpm=112,
                            chords=[[62, 65, 69, 74], [58, 62, 65, 70], [60, 64, 67, 72], [57, 61, 64, 69]],
                            roots=[38, 34, 36, 33], climax=None))
