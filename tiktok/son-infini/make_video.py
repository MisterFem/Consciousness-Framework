"""Vidéo TikTok pixel art : le son qui monte à l'infini (son de Shepard).

La bande son est une glissade de Shepard-Risset fabriquée ici : 8 sinusoïdes à
une octave d'écart qui montent ensemble, avec un volume en cloche (fort au
milieu, nul aux extrémités). Le spectre redevient identique toutes les
1/RATE secondes : le son paraît monter sans fin sans jamais aller nulle part.

    python3 make_video.py                 # produit son_infini_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 84          # centre des textes, décalé à gauche des boutons TikTok
TOP = 48         # sous la barre de recherche TikTok
MAXW = 144

RATE = 1 / 7.5   # octaves par seconde : même son toutes les 7,5 s
F0, OCT = 40.0, 8

LINES = [
    ('hook', "Monte le son. Ce son ne fait que monter."),
    ('com', "Dis-moi en commentaire si, pour toi, il monte vraiment."),
    ('encore', "Écoute… il monte encore. Et encore. Et encore."),
    ('piege', "Et pourtant, il ne va nulle part. Toutes les sept secondes et demie, il redevient "
              "exactement le même son."),
    ('notes', "C'est un son de Shepard. En réalité, ce sont plusieurs notes, à une octave d'écart, "
              "qui montent toutes ensemble."),
    ('fondu', "Les plus aiguës s'effacent tout doucement en haut… pendant que de nouvelles "
              "apparaissent en bas, sans que tu les remarques."),
    ('cerveau', "Ton cerveau, lui, ne suit que la montée. Alors il entend un son qui grimpe à "
                "l'infini."),
    ('escalier', "C'est l'équivalent sonore d'un escalier impossible."),
    ('cinema', "Et le cinéma s'en sert pour créer une tension qui ne retombe jamais : Christopher "
               "Nolan l'a utilisé dans Dunkerque."),
    ('fin', "Alors, t'avais entendu le piège avant l'explication ? Dis-le en commentaire."),
]
# du temps sans voix pour écouter le son
SCENE_STARTS = {'piege': 1.0, 'notes': 0.8, 'escalier': 0.6, 'cinema': 0.6, 'fin': 0.8}
INNER_GAPS = {'encore': 2.5, 'fondu': 0.5, 'cerveau': 0.4}
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
DUR = N.V(VOICE_END) + 1.5


def sb(pid):
    return N.B(CUT[pid])


def at(pid, words):
    a, b = PH[pid]
    return N.V(a + (b - a) * TXT[pid].index(words) / len(TXT[pid]))


# ---------------------------------------------------------------- le son
def voices(t):
    """Position (en octaves, 0..OCT) et volume de chaque note au temps t."""
    out = []
    for k in range(OCT):
        pos = (k + RATE * t) % OCT
        out.append((pos, math.exp(-0.5 * ((pos - OCT / 2) / 1.4) ** 2)))
    return out


def shepard(n, dur):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(OCT):
        pos = (k + RATE * t) % OCT
        f = F0 * 2 ** pos
        amp = np.exp(-0.5 * ((pos - OCT / 2) / 1.4) ** 2)
        out += amp * np.sin(2 * np.pi * np.cumsum(f) / SR)
    # léger fondu d'entrée pour éviter un clic, puis volume constant
    out[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    return out * 0.5


# ---------------------------------------------------------------- dessins
CLIMBER = [
    ["..hh..", "..ss..", ".bbbb.", "s.bb.s", "..bb..", ".b..b.", ".k...k"],
    ["..hh..", "..ss..", ".bbbb.", ".sbbs.", "..bb..", "..bb..", "..kk.."],
]
CL_COL = {'h': ORANGE, 's': PEACH, 'b': BLUE, 'k': INK}


def sprite(img, rows, cmap, x, y, scale):
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                img.paste(cmap[ch], (int(x + c * scale), int(y + r * scale),
                                     int(x + (c + 1) * scale), int(y + (r + 1) * scale)))


STEP_W, STEP_H = 14, 9


def endless_stairs(img, t, speed=1.0):
    """Escalier qui défile sans fin : le grimpeur reste au centre et monte toujours."""
    off = (t * speed * 1.4) % 1
    y_min, y_max = 104, 192
    for k in range(-8, 10):
        u = k - off
        x = int(CX - 7 + u * STEP_W)
        y = int(156 - u * STEP_H)
        if y >= y_max:
            continue
        shade = (78, 86, 190) if k % 2 else (52, 60, 140)
        img.paste(shade, (x, max(y, y_min), x + STEP_W, y_max))
        if y >= y_min:
            img.paste((140, 150, 240), (x, y, x + STEP_W, y + 2))
    img.paste((14, 15, 40), (0, y_max, W, y_max + 2))
    frame = int(t * 6) % 2
    sprite(img, CLIMBER[frame], CL_COL, CX - 9, 156 - 21 - frame, 3)


def spectrum(img, t, y0=72, y1=196, x=60, labels=True):
    """Les notes de Shepard : points qui montent, s'effacent en haut, naissent en bas."""
    img.paste(LGREY, (x - 1, y0, x, y1 + 1))
    if labels:
        draw_text(img, "AIGU", x, y0 - 12, LGREY)
        draw_text(img, "GRAVE", x, y1 + 4, LGREY)
    for pos, amp in voices(t):
        y = y1 - (y1 - y0) * pos / OCT
        c = int(40 + 215 * amp)
        col = (c, int(c * 0.95), min(255, c + 30))
        w = int(4 + 40 * amp)
        img.paste(col, (x + 4, int(y) - 1, x + 4 + w, int(y) + 2))
        img.paste(col, (x - 4, int(y) - 1, x - 1, int(y) + 2))


def cycle_ring(img, t, cx, cy, r=14):
    """Anneau qui se remplit en 7,5 s et repart : le son redevient le même."""
    p = (t * RATE) % 1
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DGREY, width=3)
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * p, fill=YELLOW, width=3)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def speaker(img, x, y, t):
    img.paste(WHITE, (x, y + 4, x + 5, y + 10))
    for k in range(5):
        img.paste(WHITE, (x + 5 + k, y + 4 - k, x + 6 + k, y + 10 + k))
    for k, rr in enumerate((6, 10, 14)):
        if int(t * 4 + k) % 3:
            ImageDraw.Draw(img).arc([x + 8 - rr, y + 7 - rr, x + 8 + rr, y + 7 + rr], -45, 45,
                                    fill=YELLOW, width=1)


# ================================================================ SCÈNES
COM_T = N.start('com')
SFX.append((COM_T, 'coin', None))


def hook_screen(img, t, cta):
    endless_stairs(img, t)
    draw_text(img, "CE SON NE FAIT", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE, maxw=170)
    draw_text(img, "QUE MONTER", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    speaker(img, CX - 46, TOP + 44, t)
    draw_text(img, "MONTE LE SON", CX + 10, TOP + 48, WHITE)
    if cta:
        img.paste(SHADOW, (14, 200, 156, 238))
        draw_text(img, "IL MONTE ?", CX, 202, WHITE, scale=2, maxw=150)
        draw_text(img, "COMMENTE !", CX, 220, YELLOW, scale=2, shadow=PURPLE, maxw=150)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 182)


@scene(0.0, sb('piege'))
def s_hook(img, t):
    hook_screen(img, t, COM_T <= t < N.start('encore'))
    if t >= N.start('encore'):
        k = sum(1 for w in ("Écoute", "Et encore. Et", "Et encore.") if t >= at('encore', w))
        img.paste(SHADOW, (14, 200, 156, 238))
        draw_text(img, "ET ENCORE" + " ↑" * k, CX, 212, WHITE, maxw=150)


# le piège -------------------------------------------------------------------
SAME_T = at('piege', "Toutes")
impact(N.start('piege') + 0.2, 3)


@scene(sb('piege'), sb('notes'))
def s_piege(img, t):
    draw_text(img, "ET POURTANT...", CX, TOP - 2, WHITE, scale=2)
    rubber = "IL NE VA NULLE PART"
    p = ease_out_back((t - N.start('piege') - 0.2) / 0.4)
    if t >= N.start('piege') + 0.2:
        draw_text(img, rubber, CX, int(TOP + 26 + (1 - p) * 8), RED, scale=2, maxw=150)
    if t >= SAME_T:
        cycle_ring(img, t, CX, 136, 22)
        draw_text(img, "7,5 S", CX, 131, WHITE)
        draw_text(img, "TOUTES LES 7,5 SECONDES :", CX, 170, WHITE, maxw=MAXW)
        draw_text(img, "LE *MÊME* SON", CX, 184, WHITE, scale=2, maxw=170)


# l'explication ----------------------------------------------------------------
TOPFADE_T, BOTTOM_T = at('fondu', "Les plus"), at('fondu', "pendant que")
BRAIN_T = N.start('cerveau')


@scene(sb('notes'), sb('escalier'))
def s_notes(img, t):
    if t < N.start('fondu'):
        draw_text(img, "LE SON DE SHEPARD", CX, TOP - 2, YELLOW, scale=1, maxw=MAXW)
        draw_text(img, "8 NOTES, 1 OCTAVE D'ÉCART,", CX, TOP + 12, WHITE, maxw=MAXW)
        draw_text(img, "QUI MONTENT ENSEMBLE", CX, TOP + 24, WHITE, maxw=MAXW)
    elif t < BRAIN_T:
        draw_text(img, "EN HAUT : ELLES S'EFFACENT", CX, TOP - 2, WHITE, maxw=MAXW)
        if t >= BOTTOM_T:
            draw_text(img, "EN BAS : D'AUTRES NAISSENT", CX, TOP + 12, WHITE, maxw=MAXW)
    else:
        draw_text(img, "TON CERVEAU NE SUIT", CX, TOP - 2, WHITE, maxw=MAXW)
        draw_text(img, "QUE *LA MONTÉE*", CX, TOP + 12, WHITE, maxw=MAXW)
    spectrum(img, t, y0=98, y1=214, x=46)
    # flèches « s'efface » / « apparaît »
    if TOPFADE_T <= t < BRAIN_T:
        draw_text(img, "↑ FONDU", 120, 102, LGREY)
    if BOTTOM_T <= t < BRAIN_T:
        draw_text(img, "↑ NOUVELLE", 120, 196, GREEN)
    if t >= BRAIN_T:
        draw_text(img, "↑ ∞", 122, 130, YELLOW, scale=2)


# l'escalier impossible ---------------------------------------------------------
RING = 24


def ring_pos(i, cx=CX, cy=150, half=40):
    """Position de la marche i sur un carré (vue de dessus)."""
    f = (i % RING) / (RING / 4)
    side, u = int(f), f - int(f)
    pts = [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
    (x0, y0), (x1, y1) = pts[side], pts[side + 1]
    return cx + half * (x0 + (x1 - x0) * u), cy + half * (y0 + (y1 - y0) * u)


@scene(sb('escalier'), sb('cinema'))
def s_escalier(img, t):
    draw_text(img, "UN ESCALIER", CX, TOP - 2, WHITE, scale=2)
    draw_text(img, "IMPOSSIBLE", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE)
    for i in range(RING):
        x, y = ring_pos(i)
        c = 70 + i * 7
        img.paste((c // 2, c // 2, c), (int(x) - 6, int(y) - 6, int(x) + 6, int(y) + 6))
        draw_text(img, "↑", int(x), int(y) - 6, (200, 205, 255), shadow=None)
    lt = t - sb('escalier')
    x, y = ring_pos(lt * 4)
    frame = int(t * 6) % 2
    sprite(img, CLIMBER[frame], CL_COL, x - 6, y - 16, 2)
    draw_text(img, "TOUJOURS PLUS HAUT...", CX, 202, WHITE, maxw=MAXW)
    draw_text(img, "ET TOUJOURS AU MÊME ENDROIT", CX, 216, LGREY, maxw=MAXW)


# le cinéma ---------------------------------------------------------------------
NOLAN_T = at('cinema', "Christopher")
SFX.append((NOLAN_T, 'coin', None))


@scene(sb('cinema'), sb('fin'))
def s_cinema(img, t):
    draw_text(img, "AU CINÉMA", CX, TOP - 2, WHITE, scale=2)
    # écran de cinéma + spectre du son qui tourne
    img.paste(DGREY, (24, 80, 146, 160))
    img.paste((14, 15, 40), (28, 84, 142, 156))
    spectrum(img, t, y0=90, y1=150, x=60, labels=False)
    for k in range(6):
        img.paste(RED, (20 + k * 22, 164, 34 + k * 22, 172))
    draw_text(img, "TENSION ∞", CX, 178, YELLOW, scale=2, shadow=PURPLE)
    if t >= NOLAN_T:
        img.paste(SHADOW, (14, 200, 156, 236))
        draw_text(img, "DUNKERQUE (2017)", CX, 204, WHITE, maxw=MAXW)
        draw_text(img, "CHRISTOPHER NOLAN", CX, 218, LGREY, maxw=MAXW)


# fin : retour à l'escalier (la vidéo boucle) --------------------------------------
@scene(sb('fin'), DUR)
def s_fin(img, t):
    hook_screen(img, t, True)


if __name__ == '__main__':
    with open(os.path.join(HERE, 'texte_narration.txt'), 'w') as f:
        f.write('\n\n'.join(t for _, t in LINES) + '\n')
    render_video(os.path.join(HERE, 'son_infini_tiktok.mp4'), DUR, N, loop=True, music=shepard)
