"""Vidéo TikTok pixel art : combien de plis pour atteindre la Lune ?

Version courte (~40 s) tirée des statistiques des deux premières vidéos :
question dès la première image, pari en commentaire dans les 5 premières
secondes, réponse au sommet de la montée, fin qui boucle sur le début.

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
    ('hook', "Combien de fois tu dois plier une feuille pour atteindre la Lune ?"),
    ('pari', "Fais ton pari en commentaire. Mille ? Un million ?"),
    ('regle', "À chaque pli, son épaisseur double."),
    ('p10', "10 plis : une tasse de café."),
    ('p23', "23 plis : deux fois et demie la tour Eiffel."),
    ('p30', "30 plis : tu es dans l'espace."),
    ('p42', "Et à 42 plis… tu touches la Lune. Seulement 42 !"),
    ('p103', "Et à 103 plis, ta feuille dépasse l'univers observable."),
    ('record', "En vrai, impossible : le record, c'est 13 plis."),
    ('fin', "Alors, t'avais parié combien ?"),
]
SCENE_STARTS = {'regle': 0.4, 'p42': 0.8, 'record': 0.6, 'fin': 0.3}
INNER_GAPS = {'p23': 0.3, 'p30': 0.3, 'p103': 0.6}
# {id: (début, fin)} mesurés sur audio/narration.mp3 (silences > 0,12 s)
MEASURED = {
    'hook': (0.0, 2.88), 'pari': (3.30, 5.86), 'regle': (6.28, 8.28), 'p10': (8.67, 10.39),
    'p23': (10.72, 13.27), 'p30': (13.61, 15.46), 'p42': (15.80, 19.89), 'p103': (20.22, 23.33),
    'record': (23.81, 26.71), 'fin': (27.07, 28.6),
}


def estimate(rate=17.0, pause=0.3):
    out, t = {}, 0.05
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
VOICE_END = PH[ids[-1]][1] + 0.1
N = Narration(os.path.join(HERE, 'audio', 'narration.mp3'), PH, GAPS, VOICE_END)


def sb(pid):
    """Début de la scène qui s'ouvre sur la phrase pid."""
    return N.B(CUT[pid])


DUR = N.V(VOICE_END) + 1.2

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
LABEL_AT = {10: 1, 23: 3}

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


def draw_climb(img, n, t, label=None, warp=0.0, coltop=COLTOP):
    """Colonne de papier de n plis, à côté d'objets à la même échelle."""
    h = thick(n)
    k = (GROUND - coltop) / h  # pixels par mètre
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
    img.paste(SHADOW, (COLX + 2, coltop + 2, COLX + 10, GROUND))
    img.paste(WHITE, (COLX, coltop, COLX + 8, GROUND))
    off = int(t * 20) % 3
    for y in range(coltop + off, GROUND, 3):
        img.paste(LGREY, (COLX, y, COLX + 8, y + 1))
    img.paste(LGREY, (COLX + 7, coltop, COLX + 8, GROUND))


def counter(img, n):
    draw_text(img, f"PLIS : {int(n + 1e-6)}", CX, TOP, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    v = fmt(thick(n))
    if len(v) <= 11:
        draw_text(img, v, CX, TOP + 22, WHITE, scale=2, maxw=170)
    else:
        draw_text(img, v, CX, TOP + 24, WHITE, maxw=150)




# ================================================================ SCÈNES
def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def question(img, t):
    """Écran de la question : aussi l'image de fin, pour que la vidéo boucle."""
    draw_climb(img, 42, t, coltop=118)
    # le compteur tourne : on ne donne pas la réponse
    fake = random.Random(int(t * 12)).randint(10, 99999)
    draw_text(img, str(fake), 112, 150, WHITE, scale=2, maxw=100)
    draw_text(img, "PLIS ?", 112, 172, LGREY, maxw=100)
    draw_text(img, "COMBIEN", CX, TOP - 8, WHITE, scale=2, shadow=PURPLE, maxw=150)
    draw_text(img, "DE PLIS POUR", CX, TOP + 12, WHITE, scale=2, shadow=PURPLE, maxw=150)
    draw_text(img, "LA LUNE ?", CX, TOP + 34, YELLOW, scale=3, shadow=PURPLE, maxw=150)


# 1 ─ la question + le pari ----------------------------------------------
SFX.append((0.0, 'crash', None))
PARI_T = N.start('pari')
SFX.append((PARI_T, 'coin', None))
for i in range(int(sb('regle') * 8)):
    SFX.append((i / 8, 'blip', None))


@scene(0.0, sb('regle'))
def s1(img, t):
    question(img, t)
    if t >= PARI_T:
        p = ease_out_back((t - PARI_T) / 0.35)
        img.paste(SHADOW, (14, 206, 156, 242))
        draw_text(img, "TON PARI EN", CX, int(208 + (1 - p) * 8), WHITE, scale=2, maxw=150)
        draw_text(img, "COMMENTAIRE", CX, 226, YELLOW, scale=2, shadow=PURPLE, maxw=150)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 186)
    else:
        draw_text(img, "UNE SIMPLE FEUILLE DE PAPIER...", CX, 214, maxw=150)


# 2 ─ la règle + la montée ---------------------------------------------
FOLD0 = N.start('regle') + 0.2
FOLD_DT = 0.45
for k in range(3):
    SFX.append((FOLD0 + k * FOLD_DT, 'place', k * 8))
MILES = [('p10', 10), ('p23', 23), ('p30', 30), ('p42', 42), ('p103', 103)]
CLIMB0 = N.start('p10') - 0.4
NKEYS = [(CLIMB0, 3.0)]
for pid, n in MILES:
    t0 = N.start(pid)
    dur = 3.0 if n == 103 else (2.0 if n == 42 else 1.0)
    NKEYS += [(t0 - 0.3, NKEYS[-1][1]), (t0 - 0.3 + dur, float(n))]
    if n in (42, 103):
        impact(t0 - 0.3 + dur, 4)
        SFX.append((t0 - 0.2 + dur, 'sparkle', None))
    else:
        SFX.append((t0 - 0.3 + dur, 'coin', None))
REVEAL42 = N.start('p42') - 0.3 + 2.0
CAPS = {
    'p10': "UNE TASSE", 'p23': "2,5 TOURS EIFFEL", 'p30': "L'ESPACE !",
    'p42': "LA LUNE !", 'p103': "L'UNIVERS !",
}
CAP_T = [(N.start(pid), T(txt, N.start(pid) + 0.4, 214, cps=18, scale=2, color=YELLOW, shadow=PURPLE))
         for pid, txt in CAPS.items()]


def n_at(t):
    for (ta, na), (tb, nb) in zip(NKEYS, NKEYS[1:]):
        if t < tb:
            if tb - ta < 1e-6:
                return nb
            p = clamp((t - ta) / (tb - ta))
            return na + (nb - na) * (p ** 2 if nb - na > 40 else ease_io(p))
    return NKEYS[-1][1]


@scene(sb('regle'), sb('record'))
def s2(img, t):
    if t < CLIMB0:
        # deux plis rapides : 1 -> 2 -> 4 -> 8 couches
        k = int(clamp((t - FOLD0) / FOLD_DT + 1, 0, 3)) if t >= FOLD0 else 0
        layers = 2 ** k
        w = int(70 / 2 ** k)
        img.paste(SHADOW, (CX - 35 + 3, 113, CX - 35 + w + 3, 163))
        img.paste(WHITE, (CX - 35, 110, CX - 35 + w, 160))
        for i in range(layers):
            img.paste(WHITE if i % 2 == 0 else LGREY, (CX - 30, 190 - i * 3, CX + 30, 192 - i * 3))
        draw_text(img, "ÉPAISSEUR", CX, TOP, WHITE, scale=2, maxw=170)
        draw_text(img, "× 2", CX, TOP + 20, YELLOW, scale=3, shadow=PURPLE)
        draw_text(img, f"{layers} COUCHE" + ("S" if layers > 1 else ""), CX, 198, LGREY)
        return
    n = n_at(t)
    warp = clamp((n - 45) / 10) * clamp((103 - n) / 6 + 0.2)
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
        img.paste(SHADOW, (14, 208, 156, 240))
        cur.draw(img, t, CX)
    if REVEAL42 <= t < N.start('p103'):
        p = ease_out_back((t - REVEAL42) / 0.4)
        draw_text(img, "SEULEMENT 42 !", 118, int(150 + (1 - p) * 10), WHITE, maxw=100)


# 3 ─ la réalité, puis retour à la question ------------------------------
REC_T = N.V(25.1)  # « ...c'est 13 plis » vers 25,7 s
impact(REC_T + 0.6, 2)
S3_T = N.text("EN VRAI : IMPOSSIBLE", 'record', 200)


@scene(sb('record'), sb('fin'))
def s3(img, t):
    lt = t - sb('record')
    b = scaled(BALL, 48)
    img.paste(b, (CX - b.width // 2, 110 + int(math.sin(lt * 3) * 3)), b)
    if t >= REC_T + 0.6:
        p = ease_out_back((t - REC_T - 0.6) / 0.4)
        draw_text(img, "RECORD", CX, TOP, WHITE, scale=2)
        draw_text(img, "13 PLIS", CX, int(TOP + 22 + (1 - p) * 10), YELLOW, scale=3, shadow=PURPLE)
    S3_T.draw(img, t, CX)


@scene(sb('fin'), DUR)
def s4(img, t):
    question(img, t)
    img.paste(SHADOW, (14, 206, 156, 242))
    draw_text(img, "T'AVAIS PARIÉ", CX, 208, WHITE, scale=2, maxw=170)
    draw_text(img, "COMBIEN ?", CX, 226, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    arrow(img, 138 + abs(math.sin(t * 5)) * 5, 186)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'feuille_lune_tiktok.mp4'), DUR, N, loop=True,
                 music=dict(bpm=118,
                            chords=[[64, 67, 71, 76], [60, 64, 67, 72], [67, 71, 74, 79], [62, 66, 69, 74]],
                            roots=[40, 36, 43, 38], climax=N.start('p42')))
