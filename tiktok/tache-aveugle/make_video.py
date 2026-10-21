"""Vidéo TikTok pixel art : la tache aveugle, à tester devant son écran.

Le spectateur ferme l'œil gauche, fixe la croix avec l'œil droit et approche
son téléphone : le rond rouge disparaît. Puis une ligne coupée paraît entière,
parce que le cerveau « bouche » le trou.

La croix et le rond restent au même endroit dans toutes les scènes de test
(l'œil doit pouvoir rester fixé), et rien ne bouge près du rond.

    python3 make_video.py                 # produit tache_aveugle_tiktok.mp4
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

# Le test : croix à gauche, rond à droite, le plus écartés possible sans
# sortir de la zone rognée sur les écrans allongés. ~5 cm d'écart sur un
# téléphone : le rond tombe dans la tache aveugle vers 15-25 cm.
ROW_Y = 112
CROSS_X, DOT_X = 22, 154

LINES = [
    ('hook', "Il y a un trou dans ta vision. Et je vais te le prouver."),
    ('com', "Fais le test, et dis-moi en commentaire si ça a marché."),
    ('oeil', "Ferme ton œil gauche. Avec ton œil droit, fixe la croix. Ne la quitte pas des yeux."),
    ('bouge', "Maintenant, approche lentement ton téléphone de ton visage… ou éloigne-le un peu."),
    ('disp', "À un moment… le rond rouge disparaît complètement."),
    ('tache', "C'est ta tache aveugle : l'endroit où le nerf optique sort de ton œil. À cet endroit, "
              "il n'y a aucun capteur de lumière."),
    ('twist', "Mais le plus fou, ce n'est pas le trou. C'est que tu ne le vois jamais."),
    ('cerveau', "Ton cerveau le bouche en permanence… en inventant ce qui devrait s'y trouver."),
    ('ligne', "La preuve : refais le test avec cette ligne. Quand le trou tombe dessus… elle paraît "
              "entière. Ton cerveau a dessiné le morceau manquant."),
    ('fin', "Alors, ça a marché ? Dis-le en commentaire."),
]
# pauses : du temps pour faire le test pendant que la voix se tait
SCENE_STARTS = {'oeil': 0.4, 'tache': 3.0, 'twist': 0.6, 'ligne': 0.6, 'fin': 3.0}
INNER_GAPS = {'bouge': 0.6, 'disp': 1.0}
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
DUR = N.V(VOICE_END) + 1.0


def sb(pid):
    return N.B(CUT[pid])


def at(pid, words):
    a, b = PH[pid]
    return N.V(a + (b - a) * TXT[pid].index(words) / len(TXT[pid]))


# ---------------------------------------------------------------- éléments du test
def cross(img):
    img.paste(WHITE, (CROSS_X - 6, ROW_Y - 1, CROSS_X + 7, ROW_Y + 2))
    img.paste(WHITE, (CROSS_X - 1, ROW_Y - 6, CROSS_X + 2, ROW_Y + 7))


def dot(img):
    ImageDraw.Draw(img).ellipse([DOT_X - 6, ROW_Y - 6, DOT_X + 6, ROW_Y + 6], fill=RED)


def calm_zone(img):
    """Fond uni autour du rond : pas d'étoile qui clignote dans la zone du test."""
    img.paste((14, 15, 40), (CROSS_X + 12, ROW_Y - 16, W, ROW_Y + 17))


def broken_line(img):
    for x in range(CROSS_X + 16, W):
        if not DOT_X - 7 <= x <= DOT_X + 7:
            img.paste(YELLOW, (x, ROW_Y - 1, x + 1, ROW_Y + 2))


def eye_icon(img, cx, cy, closed):
    if closed:
        img.paste(LGREY, (cx - 8, cy, cx + 9, cy + 2))
        for k in (-6, 0, 6):
            img.paste(LGREY, (cx + k, cy + 2, cx + k + 1, cy + 5))
        return
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 9, cy - 5, cx + 9, cy + 5], fill=WHITE)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=BLUE)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=INK)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def test_row(img, line=False):
    calm_zone(img)
    cross(img)
    if line:
        broken_line(img)
    else:
        dot(img)


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
COM_T = N.start('com')
SFX.append((COM_T, 'coin', None))


def hook_screen(img, t, cta):
    draw_text(img, "IL Y A UN TROU", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE, maxw=170)
    draw_text(img, "DANS TA VISION", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    test_row(img)
    draw_text(img, "JE TE LE PROUVE", CX, 140, WHITE, scale=2, maxw=170)
    draw_text(img, "EN 10 SECONDES", CX, 162, LGREY)
    if cta:
        img.paste(SHADOW, (14, 200, 156, 238))
        draw_text(img, "ÇA A MARCHÉ ?", CX, 202, WHITE, scale=2, maxw=150)
        draw_text(img, "COMMENTE !", CX, 220, YELLOW, scale=2, shadow=PURPLE, maxw=150)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 182)


@scene(0.0, sb('oeil'))
def s_hook(img, t):
    hook_screen(img, t, t >= COM_T)


# le test ------------------------------------------------------------------
STEPS = [(N.start('oeil'), "1. FERME L'ŒIL *GAUCHE*"),
         (at('oeil', "Avec"), "2. FIXE LA *CROIX*"),
         (N.start('bouge'), "3. APPROCHE OU ÉLOIGNE *LENTEMENT*")]
for ti, _ in STEPS:
    SFX.append((ti, 'place', 10))
DISP_T = N.start('disp')


@scene(sb('oeil'), sb('tache'))
def s_test(img, t):
    draw_text(img, "LE TEST", CX, TOP - 2, YELLOW, scale=2, shadow=PURPLE)
    eye_icon(img, CX - 18, TOP + 28, closed=t >= STEPS[0][0])
    eye_icon(img, CX + 18, TOP + 28, closed=False)
    draw_text(img, "G", CX - 18, TOP + 36, LGREY)
    draw_text(img, "D", CX + 18, TOP + 36, LGREY)
    test_row(img)
    for k, (ti, txt) in enumerate(STEPS):
        if t >= ti:
            draw_text(img, txt, CX, 140 + k * 16, WHITE, maxw=MAXW)
    if t >= DISP_T:
        img.paste(SHADOW, (14, 196, 156, 230))
        draw_text(img, "LE ROND ROUGE", CX, 198, WHITE, maxw=MAXW)
        draw_text(img, "*DISPARAÎT* ?", CX, 212, WHITE, scale=1, maxw=MAXW)


# l'explication ----------------------------------------------------------------
NERF_T = at('tache', "l'endroit")
ZERO_T = at('tache', "À cet endroit")
SFX.append((NERF_T, 'coin', None))


def eye_diagram(img, t):
    """Coupe de l'œil : le cristallin à gauche, le nerf optique qui sort à droite."""
    d = ImageDraw.Draw(img)
    cx, cy, r = 74, 120, 40
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=(250, 210, 200))
    # rétine : arc rose sur le fond de l'œil
    for a in range(-70, 71, 3):
        x = cx + (r - 4) * math.cos(math.radians(a))
        y = cy + (r - 4) * math.sin(math.radians(a))
        img.paste(PINK, (int(x) - 1, int(y) - 1, int(x) + 1, int(y) + 1))
    # cristallin
    d.ellipse([cx - r - 2, cy - 12, cx - r + 8, cy + 12], fill=(120, 200, 255))
    # nerf optique
    if t >= NERF_T:
        d.rectangle([cx + r - 6, cy + 4, cx + r + 30, cy + 14], fill=ORANGE)
        img.paste((250, 210, 200), (cx + r - 6, cy + 4, cx + r - 2, cy + 14))
        draw_text(img, "NERF", 138, cy + 18, ORANGE)
        draw_text(img, "OPTIQUE", 138, cy + 30, ORANGE)
    # rayons lumineux
    k = (t * 1.5) % 1
    for dy in (-8, 0, 8):
        x = int(cx - r - 26 + k * 20)
        img.paste(YELLOW, (x, cy + dy, x + 4, cy + dy + 1))


@scene(sb('tache'), sb('twist'))
def s_tache(img, t):
    draw_text(img, "TA TACHE", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "AVEUGLE", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE)
    eye_diagram(img, t)
    if t >= ZERO_T:
        p = clamp((t - ZERO_T) / 0.3)
        x, y = 74 + 40 - 4, 129
        d = ImageDraw.Draw(img)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=RED, width=2)
        if p >= 1:
            img.paste(SHADOW, (14, 186, 156, 220))
            draw_text(img, "ICI : *0 CAPTEUR*", CX, 188, WHITE, maxw=MAXW)
            draw_text(img, "DE LUMIÈRE", CX, 202, WHITE, maxw=MAXW)


# le retournement ----------------------------------------------------------------
BRAIN = [
    "....pppppp....",
    "..pppkpppkpp..",
    ".ppkpppppkppp.",
    "pppppkpppppkpp",
    "pkppppkpppkppp",
    "ppppkppppkpppp",
    ".pppppkppppkp.",
    "..ppppppppppp.",
    "....pppppp....",
    "......pp......",
]
JAMAIS_T = at('twist', "C'est que")
INVENT_T = at('cerveau', "en inventant")
SFX.append((JAMAIS_T, 'impact', None))
SFX.append((INVENT_T, 'sparkle', None))


@scene(sb('twist'), sb('ligne'))
def s_twist(img, t):
    if t < N.start('cerveau'):
        draw_text(img, "LE PLUS FOU ?", CX, TOP + 10, WHITE, scale=2)
        if t >= JAMAIS_T:
            p = ease_out_back((t - JAMAIS_T) / 0.4)
            draw_text(img, "TU NE LE VOIS", CX, int(110 + (1 - p) * 10), WHITE, scale=2)
            draw_text(img, "JAMAIS", CX, 134, YELLOW, scale=3, shadow=PURPLE)
        return
    m = mask_img(rows_to_mask([r.replace('k', '.') for r in BRAIN]), 6)
    k = mask_img(rows_to_mask([r.replace('p', '.').replace('k', '#') for r in BRAIN]), 6)
    x0, y0 = CX - m.width // 2, 70 + int(math.sin(t * 3) * 2)
    img.paste(SHADOW, (x0 + 3, y0 + 3), m)
    img.paste(PINK, (x0, y0), m)
    img.paste((200, 70, 120), (x0, y0), k)
    draw_text(img, "TON CERVEAU", CX, 140, WHITE, scale=2)
    draw_text(img, "BOUCHE LE TROU", CX, 162, WHITE, scale=2, maxw=170)
    if t >= INVENT_T:
        draw_text(img, "EN *INVENTANT* L'IMAGE", CX, 190, WHITE, maxw=MAXW)
        burst = [(math.cos(i * 0.785 + t), math.sin(i * 0.785 + t)) for i in range(8)]
        for i, (cx_, cy_) in enumerate(burst):
            x, y = int(CX + cx_ * 50), int(98 + cy_ * 34)
            img.paste(RAINBOW[i % 6], (x, y, x + 2, y + 2))


# la preuve : la ligne ---------------------------------------------------------
LINE_T = at('ligne', "refais")
ENTIERE_T = at('ligne', "elle paraît")
SFX.append((LINE_T, 'place', 14))


@scene(sb('ligne'), sb('fin'))
def s_ligne(img, t):
    draw_text(img, "LA PREUVE", CX, TOP - 2, YELLOW, scale=2, shadow=PURPLE)
    draw_text(img, "MÊME TEST, AVEC UNE LIGNE COUPÉE", CX, TOP + 22, WHITE, maxw=MAXW)
    test_row(img, line=t >= LINE_T)
    if t >= LINE_T:
        draw_text(img, "ŒIL GAUCHE FERMÉ,", CX, 140, LGREY, maxw=MAXW)
        draw_text(img, "FIXE LA CROIX", CX, 154, LGREY, maxw=MAXW)
    if t >= ENTIERE_T:
        img.paste(SHADOW, (14, 186, 156, 236))
        draw_text(img, "LA LIGNE", CX, 190, WHITE, scale=2)
        draw_text(img, "PARAÎT *ENTIÈRE*", CX, 212, WHITE, scale=2, maxw=170)


# fin : retour à l'écran d'accroche (la vidéo boucle) -----------------------------
@scene(sb('fin'), DUR)
def s_fin(img, t):
    hook_screen(img, t, True)


if __name__ == '__main__':
    with open(os.path.join(HERE, 'texte_narration.txt'), 'w') as f:
        f.write('\n\n'.join(t for _, t in LINES) + '\n')
    render_video(os.path.join(HERE, 'tache_aveugle_tiktok.mp4'), DUR, N, loop=True,
                 music=dict(bpm=96,
                            chords=[[64, 67, 71, 76], [60, 64, 67, 72], [62, 65, 69, 74], [59, 62, 66, 71]],
                            roots=[40, 36, 38, 35], climax=None))
