"""Vidéo TikTok pixel art : la machine à expériences (Nozick, 1974).

Dilemme posé dès la première image, réponse en un emoji (🔌 ou 🌍), puis le
retournement : « et si ta vie était déjà dans la machine ? » (De Brigard,
2010 : beaucoup choisissent alors de rester, biais du statu quo). La fin
revient sur la question de départ : la vidéo boucle. Pas de musique.

    python3 make_video.py                 # produit machine_experiences_tiktok.mp4
    python3 make_video.py preview 2 15    # images de contrôle
"""
import math
import os
import random
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 90
TOP = 48
MAXW = 144

LINES = [
    ('hook', "Une machine te fait vivre la vie parfaite. Tu ne sauras jamais que c'est faux. "
             "Tu te branches ?"),
    ('com', "Réponds en commentaire : la prise, ou la Terre."),
    ('nozick', "Ce dilemme, c'est le philosophe Robert Nozick qui l'a imaginé, en 1974. Et la plupart "
               "des gens refusent : on veut une vie vraie, pas juste agréable."),
    ('twist', "Maintenant, à l'envers. Tu apprends que ta vie actuelle… est déjà dans la machine."),
    ('debr', "Tu te débranches, pour retrouver la vraie ?"),
    ('res', "Quand on pose la question comme ça, beaucoup de gens choisissent… de rester."),
    ('biais', "Peut-être que ce qu'on défend, ce n'est pas le réel. C'est juste… de ne rien changer."),
    ('fin', "Alors, tu changes ta réponse ? La prise, ou la Terre ?"),
]
SCENE_STARTS = {'nozick': 0.6, 'twist': 0.8, 'debr': 0.4, 'res': 0.8, 'biais': 0.5, 'fin': 0.8}
INNER_GAPS = {'com': 0.2}
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
DUR = N.V(VOICE_END) + 1.2


def sb(pid):
    return N.B(CUT[pid])


def at(pid, words):
    a, b = PH[pid]
    return N.V(a + (b - a) * TXT[pid].index(words) / len(TXT[pid]))


# ---------------------------------------------------------------- dessins
def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def put(img, spr, cx, cy, scale):
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


PLUG = art(["..g...g..", "..g...g..", "ggggggggg", "gwwwwwwwg", "gwwwwwwwg", ".gwwwwwg.",
            "..gwwwg..", "...gwg...", "....k....", "....k...."],
           {'g': DGREY, 'w': WHITE, 'k': INK})
EARTH = art(["...bbbb...", ".bbggbbbb.", ".bgggbbgb.", "bbggbbbggb", "bbbbbbggbb", "bgbbbbbbbb",
             "bggbbbbgbb", ".bggbbbgb.", ".bbbbbbbb.", "...bbbb..."],
            {'b': BLUE, 'g': GREEN})
SLEEPER = art(["..cccc..", ".cyyyyc.", ".ssssss.", ".sk..ks.", ".ssssss.", "..ssss.."],
              {'c': LGREY, 'y': YELLOW, 's': PEACH, 'k': INK})
COUCH = art(["rr........rr", "rrrrrrrrrrrr", "rrrrrrrrrrrr", "r.r......r.r"], {'r': PURPLE})
PERSON = art(["..ss..", "..ss..", ".bbbb.", "sbbbbs", ".bbbb.", ".b..b."], {'s': PEACH, 'b': BLUE})


def machine(img, t, cx=CX, cy=128, dream=True):
    """La capsule : vitre avec un rêve en couleurs, câbles, voyants."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - 44, cy - 34, cx + 44, cy + 34], radius=14, fill=(70, 74, 110),
                        outline=LGREY, width=2)
    # vitre : le rêve (arc-en-ciel, soleil, collines) ou la réalité grise
    win = [cx - 34, cy - 24, cx + 34, cy + 14]
    d.rounded_rectangle(win, radius=8, fill=(110, 190, 255) if dream else (60, 60, 70))
    if dream:
        for k, col in enumerate(RAINBOW):
            r = 26 - k * 3
            d.arc([cx - r, cy + 6 - r, cx + r, cy + 6 + r], 200, 340, fill=col, width=2)
        d.ellipse([cx + 16, cy - 20, cx + 26, cy - 10], fill=YELLOW)
        d.ellipse([cx - 38, cy + 2, cx + 6, cy + 30], fill=GREEN)
        d.ellipse([cx - 6, cy + 4, cx + 38, cy + 30], fill=(0, 180, 70))
        d.rectangle([cx - 34, cy + 14, cx + 34, cy + 16], fill=(70, 74, 110))
    put(img, SLEEPER, cx, cy + 24, 3)
    # voyants qui clignotent
    for k in range(4):
        on = int(t * 4 + k) % 3 != 0
        img.paste(GREEN if on else DGREY, (cx - 30 + k * 8, cy + 30, cx - 26 + k * 8, cy + 32))
    # câbles
    for side in (-1, 1):
        x0 = cx + side * 44
        for k in range(14):
            x = x0 + side * k * 2
            y = cy - 10 + int(math.sin(k * 0.7 + t * 2) * 3) + k
            img.paste(YELLOW if side < 0 else ORANGE, (x, y, x + 2, y + 2))


def choice_buttons(img, t, y=176, labels=("OUI", "NON")):
    """Les deux réponses : 🔌 (se brancher / rester) et 🌍 (la vraie vie)."""
    for k, (spr, lab, col) in enumerate(((PLUG, labels[0], (60, 60, 120)), (EARTH, labels[1], (30, 90, 70)))):
        x0 = 24 + k * 68
        bob = int(math.sin(t * 3 + k * 1.5) * 1.5)
        img.paste(SHADOW, (x0 + 3, y + 3 + bob, x0 + 63, y + 41 + bob))
        img.paste(col, (x0, y + bob, x0 + 60, y + 38 + bob))
        img.paste(WHITE, (x0, y + bob, x0 + 60, y + 2 + bob))
        put(img, spr, x0 + 16, y + 19 + bob, 2)
        draw_text(img, lab, x0 + 42, y + 13 + bob, WHITE, maxw=40)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


def glitch(img, t, strength):
    """Bandes décalées + séparation des couleurs : la réalité « bugue »."""
    if strength <= 0:
        return img
    a = np.array(img)
    rng = random.Random(int(t * 24))
    for _ in range(int(3 + 10 * strength)):
        y0 = rng.randrange(0, H - 4)
        h = rng.randrange(2, 10)
        dx = rng.randint(-int(12 * strength) - 1, int(12 * strength) + 1)
        a[y0:y0 + h] = np.roll(a[y0:y0 + h], dx, axis=1)
    s = int(2 * strength) + 1
    a[..., 0] = np.roll(a[..., 0], s, axis=1)
    a[..., 2] = np.roll(a[..., 2], -s, axis=1)
    img.paste(Image.fromarray(a))
    return img


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
COM_T = N.start('com')
SFX.append((COM_T, 'coin', None))


def question_screen(img, t, title=("TU TE", "BRANCHES ?"), cta=False, labels=("OUI", "NON")):
    for k, line in enumerate(title):
        draw_text(img, line, CX, TOP - 6 + k * 22, YELLOW if k else WHITE, scale=2, shadow=PURPLE,
                  maxw=170)
    draw_text(img, "VIE PARFAITE, MAIS FAUSSE", CX, TOP + 42, LGREY, maxw=150)
    machine(img, t, cy=138)
    choice_buttons(img, t, y=182, labels=labels)
    if cta:
        img.paste(SHADOW, (20, 226, 160, 242))
        draw_text(img, "RÉPONDS EN COMMENTAIRE", CX, 230, WHITE, maxw=150)


@scene(0.0, sb('nozick'))
def s_hook(img, t):
    question_screen(img, t, cta=t >= COM_T)
    if t >= COM_T:
        arrow(img, 140 + abs(math.sin(t * 5)) * 5, 108)


# Nozick ------------------------------------------------------------------
NOZ_T = at('nozick', "Robert")
REFUSE_T = at('nozick', "Et la plupart")
SFX.append((NOZ_T, 'place', 14))
SFX.append((REFUSE_T, 'coin', None))


@scene(sb('nozick'), sb('twist'))
def s_nozick(img, t):
    draw_text(img, "LE DILEMME DE", CX, TOP - 2, WHITE, scale=1)
    if t >= NOZ_T:
        p = ease_out_back((t - NOZ_T) / 0.4)
        draw_text(img, "ROBERT NOZICK", CX, int(TOP + 12 + (1 - p) * 6), YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "PHILOSOPHE · 1974", CX, TOP + 36, LGREY)
    machine(img, t, cy=130)
    if t >= REFUSE_T:
        img.paste(SHADOW, (20, 170, 160, 240))
        draw_text(img, "LA PLUPART", CX, 174, WHITE, scale=2)
        put(img, EARTH, 38, 206, 2)
        draw_text(img, "REFUSENT", CX + 10, 198, GREEN, scale=2)
        draw_text(img, "ON VEUT DU *VRAI*", CX, 226, WHITE, maxw=150)


# le retournement ---------------------------------------------------------------
DEJA_T = at('twist', "est déjà")
SFX.append((DEJA_T, 'impact', None))
SHAKES.append((DEJA_T, 3))


@scene(sb('twist'), sb('debr'))
def s_twist(img, t):
    draw_text(img, "MAINTENANT,", CX, TOP - 2, WHITE, scale=2)
    draw_text(img, "À L'ENVERS", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE)
    if t >= at('twist', "Tu apprends"):
        draw_text(img, "TA VIE", CX, 100, WHITE, scale=2, maxw=170)
        draw_text(img, "ACTUELLE...", CX, 122, WHITE, scale=2, maxw=170)
    if t >= DEJA_T:
        draw_text(img, "EST DÉJÀ DANS", CX, 156, RED, scale=2, maxw=170)
        draw_text(img, "LA MACHINE", CX, 178, RED, scale=2, maxw=170)
        glitch(img, t, clamp(1 - (t - DEJA_T) / 1.5) * 1.0 + 0.15)


@scene(sb('debr'), sb('res'))
def s_debr(img, t):
    glitch(img, t, 0.1)
    # ici, 🔌 = rester branché, 🌍 = retrouver la vraie vie
    question_screen(img, t, title=("TU TE", "DÉBRANCHES ?"), labels=("RESTER", "SORTIR"))


# le résultat ------------------------------------------------------------------
STAY_T = at('res', "de rester")
SFX.append((STAY_T, 'impact', None))


@scene(sb('res'), sb('biais'))
def s_res(img, t):
    draw_text(img, "QUAND ON POSE", CX, TOP - 2, WHITE, scale=1)
    draw_text(img, "LA QUESTION À L'ENVERS", CX, TOP + 10, WHITE, scale=1, maxw=150)
    machine(img, t, cy=118)
    if t >= STAY_T:
        p = ease_out_back((t - STAY_T) / 0.4)
        put(img, PLUG, 30, 184, 3)
        draw_text(img, "BEAUCOUP", CX + 16, int(166 + (1 - p) * 6), WHITE, scale=2)
        draw_text(img, "RESTENT !", CX + 16, 188, YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "DE BRIGARD, 2010", CX, 214, LGREY)


# le biais ---------------------------------------------------------------------
RIEN_T = at('biais', "C'est juste")
SFX.append((RIEN_T + 0.4, 'coin', None))


@scene(sb('biais'), sb('fin'))
def s_biais(img, t):
    draw_text(img, "CE QU'ON DÉFEND...", CX, TOP - 2, WHITE, scale=2, maxw=170)
    d = ImageDraw.Draw(img)
    if t < RIEN_T:
        draw_text(img, "LE RÉEL ?", CX, 100, LGREY, scale=3)
        return
    draw_text(img, "LE RÉEL ?", CX, 92, DGREY, scale=2)
    d.line([(CX - 50, 104), (CX + 50, 96)], fill=RED, width=2)
    put(img, COUCH, CX, 150, 5)
    put(img, PERSON, CX, 136 + int(math.sin(t * 2) * 1), 4)
    draw_text(img, "NE RIEN CHANGER", CX, 176, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    draw_text(img, "LE BIAIS DU STATU QUO", CX, 202, WHITE, maxw=150)


# fin : retour à la question (la vidéo boucle) -------------------------------------
@scene(sb('fin'), DUR)
def s_fin(img, t):
    question_screen(img, t, title=("ALORS,", "TU CHANGES ?"), cta=True)
    arrow(img, 140 + abs(math.sin(t * 5)) * 5, 108)


if __name__ == '__main__':
    with open(os.path.join(HERE, 'texte_narration.txt'), 'w') as f:
        f.write('\n\n'.join(t for _, t in LINES) + '\n')
    render_video(os.path.join(HERE, 'machine_experiences_tiktok.mp4'), DUR, N, loop=True,
                 music=lambda n, dur: np.zeros(n))
