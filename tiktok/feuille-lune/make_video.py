"""Vidéo TikTok pixel art : plier une feuille 42 fois pour atteindre la Lune.

    python3 make_video.py                 # produit feuille_lune_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle

Sans audio/narration.mp3, les phrases sont calées sur une durée estimée. Une
fois la voix enregistrée, remplacer MEASURED par les temps mesurés.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 84          # centre des textes, décalé à gauche des boutons TikTok
TOP = 48         # sous la barre de recherche TikTok

# ---------------------------------------------------------------- narration
LINES = [
    ('hook', "Si tu plies une feuille de papier 42 fois… elle atteint la Lune."),
    ('feuille', "Oui, une simple feuille. Elle fait un dixième de millimètre d'épaisseur."),
    ('double', "Et chaque fois que tu la plies, son épaisseur double."),
    ('p7', "7 plis : la hauteur d'un morceau de sucre."),
    ('p10', "10 plis : une tasse de café."),
    ('p17', "17 plis : un immeuble de quatre étages."),
    ('p23', "23 plis : deux fois et demie la tour Eiffel !"),
    ('p27', "27 plis : plus haut que l'Everest."),
    ('p30', "30 plis : tu sors de l'atmosphère. Tu es dans l'espace."),
    ('p42', "42 plis… tu touches la Lune."),
    ('p51', "51 plis : tu dépasses le Soleil."),
    ('p103', "Et à 103 plis… ta feuille est plus grande que l'univers observable."),
    ('secret', "Le secret ? Doubler, encore et encore. Rien ne grandit plus vite."),
    ('record', "Bon, en vrai, c'est impossible : le record du monde, c'est 13 plis… "
               "avec une bande de papier de plus d'un kilomètre !"),
    ('cta', "Et toi, tu arrives à plier une feuille combien de fois ? Dis-le en commentaire !"),
    ('abo', "Abonne-toi pour plus d'anecdotes qui donnent le vertige !"),
]
SCENE_STARTS = {'feuille': 0.8, 'p7': 0.8, 'secret': 1.0, 'record': 1.0, 'cta': 1.0}
INNER_GAPS = {'double': 0.3, 'p10': 0.5, 'p17': 0.5, 'p23': 0.5, 'p27': 0.5, 'p30': 0.5,
              'p42': 0.9, 'p51': 0.6, 'p103': 0.9, 'abo': 0.3}
MEASURED = None  # {id: (début, fin)} mesurés sur audio/narration.mp3


def estimate(rate=17.0, pause=0.4):
    out, t = {}, 0.1
    for pid, txt in LINES:
        d = len(txt) / rate
        out[pid] = (t, t + d)
        t += d + pause
    return out


PH = MEASURED or estimate()
ids = [pid for pid, _ in LINES]
CUT, GAPS = {}, []
for pid, g in {**SCENE_STARTS, **INNER_GAPS}.items():
    prev = ids[ids.index(pid) - 1]
    CUT[pid] = (PH[prev][1] + PH[pid][0]) / 2
    GAPS.append((CUT[pid], g))
GAPS.sort()
VOICE_END = PH[ids[-1]][1] + 0.2
N = Narration(os.path.join(HERE, 'audio', 'narration.mp3'), PH, GAPS, VOICE_END)


def sb(pid):
    """Début de la scène qui s'ouvre sur la phrase pid."""
    return N.B(CUT[pid])


DUR = N.V(VOICE_END) + 2.0


# ---------------------------------------------------------------- outils
def fmt(m):
    """Épaisseur lisible : MM, CM, M, KM puis années-lumière."""
    def fr(v, d=0):
        return f"{v:,.{d}f}".replace(',', ' ').replace('.', ',')
    if m < 0.01:
        return fr(m * 1000, 1) + " MM"
    if m < 1:
        return fr(m * 100, 1) + " CM"
    if m < 1000:
        return fr(m, 1 if m < 10 else 0) + " M"
    if m < 1e15:
        return fr(m / 1000) + " KM"
    ly = m / 9.461e15
    if ly < 1e6:
        return fr(ly, 1 if ly < 10 else 0) + " ANNÉES-LUMIÈRE"
    if ly < 1e9:
        return fr(ly / 1e6) + " MILLIONS D'ANNÉES-LUMIÈRE"
    return fr(ly / 1e9) + " MILLIARDS D'ANNÉES-LUMIÈRE"


def thick(n):
    return 1e-4 * 2 ** n


def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


# ---------------------------------------------------------------- sprites
SUGAR = art(["wwwwww", "wwwwwl", "wwwwwl", "wwwwwl", "wwwwwl", "llllll"],
            {'w': WHITE, 'l': LGREY})
MUG = art([".rrrrrr...", ".rwwwwr...", ".rrrrrrrr.", ".rrrrrr..r", ".rrrrrr..r",
           ".rrrrrrrr.", ".rrrrrr...", ".rrrrrr...", "..rrrr...."],
          {'r': RED, 'w': BROWN})


def make_building():
    rows = []
    for floor in range(4):
        rows += ["gggggggggggg", "gyygyygyygyg" if floor % 2 else "gygyyggyygyg",
                 "gyygyygyygyg", "gggggggggggg"]
    rows[-3] = "ggggbbbbgggg"
    rows[-2] = "ggggbbbbgggg"
    return art(["dddddddddddd"] + rows, {'g': LAVENDER, 'y': YELLOW, 'b': BROWN, 'd': DGREY})


def make_eiffel():
    w, h = 15, 30
    rows = [['.'] * w for _ in range(h)]
    for r in range(h):
        hw = int(0.5 + 7 * (r / (h - 1)) ** 2.3)
        for c in (7 - hw, 7 + hw):
            rows[r][c] = 'o'
        if r in (11, 20):
            for c in range(7 - hw, 7 + hw + 1):
                rows[r][c] = 'o'
    rows[0][7] = 'y'
    return art([''.join(r) for r in rows], {'o': ORANGE, 'y': YELLOW})


def make_mountain():
    w, h = 44, 20
    rows = []
    for r in range(h):
        hw = r * (w / 2) / h
        row = ''
        for c in range(w):
            d = abs(c - w / 2 + 0.5)
            if d <= hw:
                row += 's' if r < 5 or (r < 7 and c % 3 == 0) else ('m' if c < w / 2 else 'k')
            else:
                row += '.'
        rows.append(row)
    return art(rows, {'s': WHITE, 'm': LAVENDER, 'k': DGREY})


BUILDING, EIFFEL, MOUNTAIN = make_building(), make_eiffel(), make_mountain()
BALL = art(["....wwwww....", "..wwlwwwlww..", ".wlwwwlwwwlw.", ".wwwlwwwlwww.",
            "wwlwwwwlwwwlw", "wwwlwwlwwwwww", "wlwwwlwwwlwlw", "wwwwlwwwlwwww",
            ".wwlwwwwwwlw.", ".wwwwlwwlwww.", "..wlwwwwwww..", "....wwlww...."],
           {'w': WHITE, 'l': LGREY})

# objets de comparaison : (hauteur réelle en m, sprite, nom)
OBJECTS = [(0.0125, SUGAR, "SUCRE"), (0.095, MUG, "TASSE"), (13, BUILDING, "IMMEUBLE"),
           (330, EIFFEL, "TOUR EIFFEL"), (8849, MOUNTAIN, "EVEREST")]
LABEL_AT = {7: 0, 10: 1, 17: 2, 23: 3, 27: 4}

# ---------------------------------------------------------------- la montée
GROUND, COLTOP, COLX = 200, 95, 52
COLH = GROUND - COLTOP
_sr = random.Random(5)
WARP = [(_sr.random() * 6.28, _sr.random(), _sr.choice([WHITE, LAVENDER, BLUE, PINK])) for _ in range(80)]
GALAXIES = [(_sr.random() * 6.28, _sr.random() ** 0.5, _sr.choice([PINK, BLUE, YELLOW, LAVENDER]))
            for _ in range(26)]


def scaled(spr, hpx):
    sc = hpx / spr.height
    return spr.resize((max(1, int(round(spr.width * sc))), max(1, int(round(hpx)))), Image.NEAREST)


def draw_climb(img, n, t, label=None, warp=0.0):
    """Colonne de papier de n plis, à côté d'objets à la même échelle."""
    h = thick(n)
    k = COLH / h  # pixels par mètre
    d = ImageDraw.Draw(img)
    # étoiles en mode « hyperespace »
    if warp > 0:
        for a, r0, col in WARP:
            r = ((r0 + t * 1.5) % 1) * 120
            ln = 4 + 30 * warp * (r / 120)
            x0, y0 = CX + math.cos(a) * r, 140 + math.sin(a) * r
            d.line([(x0, y0), (x0 + math.cos(a) * ln, y0 + math.sin(a) * ln)], fill=col)
    # Terre : sol plat, puis planète qui rapetisse
    R = k * 6.371e6
    if R > 4000:
        img.paste((22, 60, 40), (0, GROUND, W, GROUND + 3))
        img.paste((14, 22, 30), (0, GROUND + 3, W, H))
    elif R >= 0.5:
        rr = max(R, 1.5)
        d.ellipse([COLX + 4 - rr, GROUND + 1, COLX + 4 + rr, GROUND + 1 + 2 * rr], fill=BLUE,
                  outline=(120, 200, 255))
        if rr > 6:
            d.ellipse([COLX + 4 - rr * 0.5, GROUND + rr * 0.4, COLX + 4 + rr * 0.1, GROUND + rr],
                      fill=GREEN)
    # objets posés au sol
    for i, (oh, spr, name) in enumerate(OBJECTS):
        hpx = oh * k
        if 2 <= hpx <= 400 and R > 4000:
            s = scaled(spr, hpx)
            img.paste(s, (118 - s.width // 2, GROUND - s.height), s)
            if label == i:
                draw_text(img, name, 118, max(TOP + 40, GROUND - s.height - 13), YELLOW, maxw=120)
    # limite de l'espace (100 km)
    ys = GROUND - k * 1e5
    if 30 < ys < GROUND - 4:
        for x in range(0, W, 4):
            img.paste(BLUE, (x, int(ys), x + 2, int(ys) + 1))
        draw_text(img, "ESPACE", 118, int(ys) - 12, BLUE)
    # Lune et Soleil à leur vraie distance
    for dist, rad, col, name in ((3.844e8, 1.737e6, LGREY, "LUNE"), (1.496e11, 6.96e8, YELLOW, "SOLEIL")):
        y = GROUND - k * dist
        if -10 < y < GROUND - 2:
            r = max(4 if name == "LUNE" else 4.5, k * rad)
            x = COLX + 18 if name == "LUNE" else COLX + 24
            if name == "SOLEIL":
                d.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2], fill=ORANGE)
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
            draw_text(img, name, int(x + r) + 24, int(y) - 6, col)
    # univers observable (rayon 4,4e26 m) centré sur la Terre
    ru = k * 4.4e26
    if 3 < ru < 300:
        for i in range(120):
            a = i / 120 * 2 * math.pi
            if i % 2:
                img.putpixel((int(COLX + 4 + math.cos(a) * ru) % W, int(GROUND + math.sin(a) * ru) % H),
                             LAVENDER)
        px = img.load()
        for a, r, col in GALAXIES:
            x, y = COLX + 4 + math.cos(a + t * 0.2) * r * ru * 0.9, GROUND + math.sin(a + t * 0.2) * r * ru * 0.9
            if 1 <= x < W - 1 and 1 <= y < H - 1:
                px[int(x), int(y)] = col
                px[int(x) + 1, int(y)] = col
        draw_text(img, "UNIVERS", int(COLX + 4 + ru * 0.6) + 20, int(GROUND - ru * 0.75) - 8, LAVENDER)
    # la colonne de papier
    img.paste(SHADOW, (COLX + 2, COLTOP + 2, COLX + 10, GROUND))
    img.paste(WHITE, (COLX, COLTOP, COLX + 8, GROUND))
    off = int(t * 20) % 3
    for y in range(COLTOP + off, GROUND, 3):
        img.paste(LGREY, (COLX, y, COLX + 8, y + 1))
    img.paste(LGREY, (COLX + 7, COLTOP, COLX + 8, GROUND))


def counter(img, n):
    draw_text(img, f"PLIS : {int(n + 1e-6)}", CX, TOP, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    v = fmt(thick(n))
    if len(v) <= 11:
        draw_text(img, v, CX, TOP + 22, WHITE, scale=2, maxw=170)
    else:
        draw_text(img, v, CX, TOP + 24, WHITE, maxw=150)


# ================================================================ SCÈNES
# 1 ─ accroche : lisible dès la première image ---------------------------
SFX.append((0.0, 'crash', None))


@scene(0.0, sb('feuille'))
def s1(img, t):
    draw_climb(img, 42, t)
    draw_text(img, "42 PLIS", CX, TOP - 2, YELLOW, scale=3, shadow=PURPLE, maxw=170)
    draw_text(img, "UNE FEUILLE PLIÉE 42 FOIS ATTEINDRAIT LA *LUNE* !", CX, 210, maxw=140)


# 2 ─ la feuille et le pli ----------------------------------------------
S2_T1 = N.text("UNE SIMPLE FEUILLE : *0,1 MM* D'ÉPAISSEUR", 'feuille', 200)
S2_T2 = N.text("CHAQUE PLI : ÉPAISSEUR *× 2*", 'double', 200)
FOLD0 = N.start('double') + 0.6
FOLD_DT = 0.7
for k in range(4):
    SFX.append((FOLD0 + k * FOLD_DT, 'place', k * 6))


@scene(sb('feuille'), sb('p7'))
def s2(img, t):
    k = int(clamp((t - FOLD0) / FOLD_DT + 1, 0, 4)) if t >= FOLD0 else 0
    p = clamp((t - FOLD0 - (k - 1) * FOLD_DT) / 0.25) if k else 1
    # vue de dessus : la feuille rétrécit
    wv = 70 / (2 ** max(0, k - 1)) * (1 - 0.5 * ease_io(p)) if k else 70
    x0 = CX - 35
    img.paste(SHADOW, (x0 + 3, 63, int(x0 + wv) + 3, 123))
    img.paste(WHITE, (x0, 60, int(x0 + wv), 120))
    for y in range(66, 116, 6):
        img.paste((150, 190, 230), (x0 + 3, y, int(x0 + wv) - 3, y + 1))
    # vue de côté : les couches s'empilent
    layers = 2 ** k
    for i in range(layers):
        img.paste(WHITE if i % 2 == 0 else LGREY, (CX - 30, 160 - i * 2, CX + 30, 161 - i * 2))
    draw_text(img, f"{layers} COUCHE" + ("S" if layers > 1 else ""), CX, 166, LGREY)
    if k:
        draw_text(img, "× 2", CX + 46, 140, YELLOW, scale=2, shadow=PURPLE)
    (S2_T1 if t < S2_T2.t0 else S2_T2).draw(img, t, CX)


# 3 ─ la grande montée --------------------------------------------------
MILES = [('p7', 7), ('p10', 10), ('p17', 17), ('p23', 23), ('p27', 27), ('p30', 30),
         ('p42', 42), ('p51', 51), ('p103', 103)]
NKEYS = [(sb('p7'), 0.0)]
for pid, n in MILES:
    t0 = N.start(pid)
    dur = 3.0 if n == 103 else (1.6 if n in (42, 51) else 0.9)
    NKEYS += [(t0 - 0.2, NKEYS[-1][1]), (t0 - 0.2 + dur, float(n))]
    SFX.append((t0 - 0.2 + dur, 'impact' if n in (42, 103) else 'coin', None))
    if n in (42, 103):
        SHAKES.append((t0 - 0.2 + dur, 3))
CAPS = {
    'p7': "7 PLIS : UN *MORCEAU DE SUCRE*",
    'p10': "10 PLIS : UNE *TASSE DE CAFÉ*",
    'p17': "17 PLIS : UN *IMMEUBLE* DE 4 ÉTAGES",
    'p23': "23 PLIS : *2,5 × LA TOUR EIFFEL* !",
    'p27': "27 PLIS : PLUS HAUT QUE *L'EVEREST*",
    'p30': "30 PLIS : TU ES DANS *L'ESPACE*",
    'p42': "42 PLIS : TU TOUCHES *LA LUNE* !",
    'p51': "51 PLIS : TU DÉPASSES *LE SOLEIL*",
    'p103': "103 PLIS : PLUS GRANDE QUE *L'UNIVERS OBSERVABLE* !",
}
CAP_T = [(N.start(pid), N.text(txt, pid, 212)) for pid, txt in CAPS.items()]


def n_at(t):
    for (ta, na), (tb, nb) in zip(NKEYS, NKEYS[1:]):
        if t < tb:
            if tb - ta < 1e-6:
                return nb
            p = clamp((t - ta) / (tb - ta))
            return na + (nb - na) * (p ** 2 if nb - na > 40 else ease_io(p))
    return NKEYS[-1][1]


@scene(sb('p7'), sb('secret'))
def s3(img, t):
    n = n_at(t)
    warp = clamp((n - 51) / 10) * clamp((103 - n) / 6 + 0.2)
    lab = None
    for m, i in LABEL_AT.items():
        if abs(n - m) < 0.6:
            lab = i
    draw_climb(img, n, t, lab, warp)
    counter(img, n)
    cur = None
    for t0, tx in CAP_T:
        if t >= t0:
            cur = tx
    if cur:
        img.paste(SHADOW, (6, 207, 162, 240))
        cur.draw(img, t, CX)


# 4 ─ le secret : doubler -----------------------------------------------
POW0 = N.start('secret') + 0.3
POW_DT = 0.16
for i in range(16):
    SFX.append((POW0 + i * POW_DT, 'place', i * 2))
BIGPOW = N.stop('secret') - 0.6
impact(BIGPOW, 3)
S4_T = N.text("LE SECRET ? *DOUBLER*, ENCORE ET ENCORE.", 'secret', 205)


@scene(sb('secret'), sb('record'))
def s4(img, t):
    shown = int(clamp((t - POW0) / POW_DT + 1, 0, 16)) if t >= POW0 else 0
    for i in range(shown):
        x = CX - 60 + (i % 4) * 40
        y = TOP + (i // 4) * 16
        draw_text(img, str(2 ** i), x, y, WHITE if i < 15 else YELLOW, maxw=60)
    if shown >= 16:
        draw_text(img, "...", CX, TOP + 64, LGREY)
    if t >= BIGPOW:
        p = ease_out_back((t - BIGPOW) / 0.4)
        draw_text(img, "À 42 PLIS :", CX, int(140 + (1 - p) * 10), WHITE)
        draw_text(img, "4 398 MILLIARDS", CX, 154, YELLOW, scale=2, shadow=PURPLE, maxw=170)
        draw_text(img, "DE COUCHES DE PAPIER", CX, 178, WHITE)
    S4_T.draw(img, t, CX)


# 5 ─ la réalité --------------------------------------------------------
REC_T = N.start('record') + 1.5
impact(REC_T, 2)
S5_T = N.text("EN VRAI : IMPOSSIBLE. LE RECORD, C'EST *13 PLIS*... AVEC UNE BANDE DE PAPIER DE "
              "*PLUS D'1 KM* !", 'record', 196)


@scene(sb('record'), sb('cta'))
def s5(img, t):
    lt = t - sb('record')
    b = scaled(BALL, 48)
    img.paste(b, (CX - b.width // 2, 92 + int(math.sin(lt * 3) * 3)), b)
    if t >= REC_T:
        p = ease_out_back((t - REC_T) / 0.4)
        draw_text(img, "RECORD DU MONDE", CX, TOP, WHITE)
        draw_text(img, "13 PLIS", CX, int(TOP + 14 + (1 - p) * 10), YELLOW, scale=2, shadow=PURPLE)
    S5_T.draw(img, t, CX)


# 6 ─ à toi ! -----------------------------------------------------------
_C0, _C1 = N.start('cta'), N.stop('cta')
_CM = _C0 + (_C1 - _C0) * 0.68  # « Dis-le en commentaire » ~ dernier tiers
S6_T1 = T("ET TOI, TU ARRIVES À LA PLIER *COMBIEN DE FOIS* ?", _C0, 140, cps=48 / (_CM - _C0))
S6_T2 = T("DIS-LE EN COMMENTAIRE !", _CM, 204, cps=23 / (_C1 - _CM))
ABO_T = N.start('abo')
SFX.append((ABO_T, 'coin', None))


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


@scene(sb('cta'), DUR)
def s6(img, t):
    lt = t - sb('cta')
    k = int(lt / 0.6) % 4
    w = int(60 / (2 ** k))
    img.paste(SHADOW, (CX - 30 + 3, 73, CX - 30 + w + 3, 123))
    img.paste(WHITE, (CX - 30, 70, CX - 30 + w, 120))
    for y in range(76, 116, 6):
        img.paste((150, 190, 230), (CX - 27, y, CX - 30 + w - 3, y + 1))
    S6_T1.draw(img, t, CX)
    if t >= S6_T2.t0:
        S6_T2.draw(img, t, CX)
        arrow(img, 128 + abs(math.sin(lt * 5)) * 6, 179)
    if t >= ABO_T:
        p = ease_out_back((t - ABO_T) / 0.4)
        y = int(TOP - 6 - (1 - p) * 20)
        img.paste(RED, (CX - 40, y, CX + 40, y + 16))
        img.paste(PINK, (CX - 40, y, CX + 40, y + 2))
        draw_text(img, "+ ABONNE-TOI", CX, y + 1, WHITE, shadow=PURPLE)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'feuille_lune_tiktok.mp4'), DUR, N,
                 music=dict(bpm=118,
                            chords=[[64, 67, 71, 76], [60, 64, 67, 72], [67, 71, 74, 79], [62, 66, 69, 74]],
                            roots=[40, 36, 43, 38], climax=N.start('p42')))
