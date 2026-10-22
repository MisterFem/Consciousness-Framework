"""Vidéo TikTok pixel art : le téléporteur, en test de personnalité à 4 niveaux.

Le spectateur compte ses OUI sur ses doigts : téléporteur, bug (deux toi),
remplacement des neurones, anesthésie générale. Le piège : presque tout le
monde accepte l'anesthésie. Résultat selon le nombre de OUI (0 = l'Âme,
4 = l'Information, entre les deux = le Paradoxe), à écrire en commentaire.
Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit teleporteur_tiktok.mp4
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
CHOOSE = 2.6      # secondes laissées pour choisir à chaque niveau

LINES = [
    ('hook', "Un téléporteur, quatre questions. Compte tes oui sur tes doigts : à la fin, je te dis "
             "ce que tu es vraiment."),
    ('q1', "Niveau un. Le téléporteur te détruit ici, et te reconstruit là-bas, atome par atome. "
           "Identique. Tu montes ?"),
    ('q2', "Niveau deux. Bug : ton original n'a pas été détruit. Vous êtes deux. Et l'original doit "
           "disparaître. Tu acceptes ?"),
    ('q3', "Niveau trois. On remplace tes neurones, un par un, par des neurones artificiels "
           "identiques. Tu ne sens rien. À la fin, il ne reste rien d'origine. Tu acceptes ?"),
    ('q4', "Niveau quatre. Une anesthésie générale : ta conscience s'éteint, puis se rallume. "
           "Tu acceptes ?"),
    ('piege', "Si tu as dit non au téléporteur, mais oui à l'anesthésie… qu'est-ce qui prouve que "
              "celui qui se réveille, c'est toi ?"),
    ('profil', "Zéro oui : tu crois qu'il y a quelque chose en toi qu'on ne peut pas copier. Quatre "
               "oui : pour toi, tu es une information. Entre les deux… tu es un paradoxe. Comme "
               "beaucoup de philosophes."),
    ('cta', "Écris ton nombre de oui en commentaire."),
]
SCENE_STARTS = {'q1': 0.6, 'q2': CHOOSE, 'q3': CHOOSE, 'q4': CHOOSE, 'piege': CHOOSE,
                'profil': 0.6, 'cta': 0.6}
INNER_GAPS = {}
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


HERO_ROWS = ["..hh..", ".hssh.", "..ss..", ".bbbb.", "sbbbbs", ".bbbb.", ".b..b.", ".k..k."]
HERO_COL = {'h': (90, 60, 30), 's': PEACH, 'b': BLUE, 'k': INK}
HERO = art(HERO_ROWS, HERO_COL)
GHOST = art(["..wwww..", ".wwwwww.", "wwkwwkww", "wwwwwwww", "wwwwwwww", "wwwwwwww", "w.ww.ww."],
            {'w': (220, 225, 255), 'k': INK})
BED = art(["w.........", "wwwwwwwwww", "wbbbbbbbbw", "w........w"], {'w': LGREY, 'b': BLUE})
HAND = art(["..y.y.y...", "..y.y.y.y.", "..y.y.y.y.", "y.yyyyyyy.", "yyyyyyyyy.", ".yyyyyyy..",
            "..yyyyy..."], {'y': PEACH})


def hero_pixels(img, cx, cy, scale, amount, t, seed=0):
    """Le personnage, plus ou moins désintégré (amount 0 = entier, 1 = poussière)."""
    rng = random.Random(seed)
    for r, row in enumerate(HERO_ROWS):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            k = rng.random()
            x = cx + (c - 3) * scale
            y = cy + (r - 4) * scale
            if k < amount:
                # la « poussière » s'envole vers le haut
                y -= amount * 60 * (0.5 + k)
                x += math.sin(t * 6 + k * 20) * 3 * amount
                col = (120, 230, 255)
                img.paste(col, (int(x), int(y), int(x) + max(1, scale // 2), int(y) + max(1, scale // 2)))
            else:
                img.paste(HERO_COL[ch], (int(x), int(y), int(x) + scale, int(y) + scale))


def pad(img, cx, y, glow, t):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 22, y - 5, cx + 22, y + 5], fill=DGREY)
    d.ellipse([cx - 18, y - 3, cx + 18, y + 3], fill=(120, 230, 255) if glow else (60, 70, 90))
    if glow:
        for k in range(5):
            x = cx - 16 + k * 8
            h = 40 + int(math.sin(t * 9 + k) * 6)
            img.paste((90, 200, 240), (x, y - h, x + 1, y - 3))


def buttons(img, t, y, labels=("OUI", "NON")):
    for k, (lab, col) in enumerate(zip(labels, ((0, 150, 80), (190, 40, 70)))):
        x0 = 30 + k * 64
        bob = int(math.sin(t * 3 + k * 1.5) * 1.5)
        img.paste(SHADOW, (x0 + 3, y + 3 + bob, x0 + 59, y + 27 + bob))
        img.paste(col, (x0, y + bob, x0 + 56, y + 24 + bob))
        img.paste(WHITE, (x0, y + bob, x0 + 56, y + 2 + bob))
        draw_text(img, lab, x0 + 28, y + 7 + bob, WHITE, scale=1)


def level_header(img, n):
    draw_text(img, f"NIVEAU {n}/4", CX, TOP - 6, YELLOW, scale=2, shadow=PURPLE)
    for k in range(4):
        col = YELLOW if k + 1 == n else (LGREY if k + 1 < n else DGREY)
        img.paste(col, (CX - 31 + k * 16, TOP + 18, CX - 21 + k * 16, TOP + 21))


def countdown(img, t, t0):
    """Barre « CHOISIS ! » qui se vide pendant le temps de réflexion."""
    if t < t0:
        return
    p = clamp((t - t0) / CHOOSE)
    img.paste(SHADOW, (28, 222, 152, 236))
    img.paste(YELLOW, (30, 224, int(30 + 120 * (1 - p)), 234))
    draw_text(img, "CHOISIS !", CX, 224, INK, shadow=None)


def finger_hint(img, t):
    put(img, HAND, CX, 182 + int(math.sin(t * 3) * 1), 2)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))


def hook_screen(img, t, cta=False):
    draw_text(img, "TÉLÉPORTEUR", CX, TOP - 6, WHITE, scale=2, shadow=PURPLE, maxw=170)
    draw_text(img, "4 QUESTIONS", CX, TOP + 16, YELLOW, scale=2, shadow=PURPLE)
    lt = t % 3.0
    amount = clamp(lt / 1.2) if lt < 1.5 else 0.0
    pad(img, 50, 170, lt < 1.5, t)
    pad(img, 130, 170, 1.5 <= lt < 3.0, t)
    if lt < 1.5:
        hero_pixels(img, 50, 150, 4, amount, t, seed=1)
    else:
        hero_pixels(img, 130, 150, 4, clamp(1 - (lt - 1.5) / 1.0), t, seed=2)
    if cta:
        img.paste(SHADOW, (18, 196, 162, 240))
        draw_text(img, "TON NOMBRE DE OUI ?", CX, 200, WHITE, maxw=150)
        draw_text(img, "COMMENTE !", CX, 214, YELLOW, scale=2, shadow=PURPLE)
        arrow(img, 140 + abs(math.sin(t * 5)) * 5, 178)
    else:
        img.paste(SHADOW, (18, 194, 162, 242))
        draw_text(img, "COMPTE TES", CX, 197, WHITE, scale=2, maxw=170)
        draw_text(img, "OUI", 52, 219, YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "SUR TES DOIGTS", 112, 223, WHITE, maxw=100)
        finger_hint(img, t)


@scene(0.0, sb('q1'))
def s_hook(img, t):
    hook_screen(img, t)


def level_scene(pid, n, draw_fn, question):
    end = sb(ids[ids.index(pid) + 1])
    t_choose = N.stop(pid)
    SFX.append((N.start(pid), 'whoosh', None))
    for k in range(3):
        SFX.append((t_choose + k * CHOOSE / 3, 'place', 6 - k * 2))

    @scene(sb(pid), end)
    def _s(img, t):
        level_header(img, n)
        draw_fn(img, t, t - sb(pid))
        draw_text(img, question, CX, 172, WHITE, scale=2, shadow=PURPLE, maxw=170)
        buttons(img, t, 194)
        countdown(img, t, t_choose)
    return _s


def draw_q1(img, t, lt):
    pad(img, 50, 150, True, t)
    pad(img, 130, 150, True, t)
    k = (lt % 2.4)
    hero_pixels(img, 50, 130, 4, clamp(k / 1.0), t, seed=3)
    hero_pixels(img, 130, 130, 4, clamp(1 - (k - 1.0) / 1.0) if k > 1.0 else 1.0, t, seed=4)
    draw_text(img, "DÉTRUIT", 50, 80, RED)
    draw_text(img, "RECRÉÉ", 130, 80, GREEN)


def draw_q2(img, t, lt):
    pad(img, 50, 150, False, t)
    pad(img, 130, 150, False, t)
    hero_pixels(img, 50, 130, 4, 0.0, t, seed=5)
    hero_pixels(img, 130, 130, 4, 0.0, t, seed=6)
    draw_text(img, "L'ORIGINAL", 50, 80, YELLOW)
    draw_text(img, "LA COPIE", 130, 80, LGREY)
    if t >= at('q2', "Et l'original"):
        d = ImageDraw.Draw(img)
        d.line([(34, 112), (66, 148)], fill=RED, width=2)
        d.line([(66, 112), (34, 148)], fill=RED, width=2)


BRAIN_CELLS = [(x, y) for y in range(8) for x in range(12) if (x - 5.5) ** 2 / 36 + (y - 3.5) ** 2 / 16 < 1]
_order = list(range(len(BRAIN_CELLS)))
random.Random(9).shuffle(_order)


def draw_q3(img, t, lt):
    p = clamp(lt / (N.stop('q3') - sb('q3') - 1.0))
    n = int(p * len(BRAIN_CELLS))
    swapped = set(_order[:n])
    for i, (x, y) in enumerate(BRAIN_CELLS):
        col = (90, 200, 240) if i in swapped else PINK
        img.paste(col, (CX - 42 + x * 7, 92 + y * 7, CX - 36 + x * 7, 98 + y * 7))
    draw_text(img, f"{int(p * 100)} % ARTIFICIEL", CX, 150, (90, 200, 240))


def draw_q4(img, t, lt):
    put(img, BED, CX, 140, 6)
    put(img, HERO, CX - 20, 122, 3)
    off = at('q4', "s'éteint") <= t < at('q4', "puis se rallume")
    d = ImageDraw.Draw(img)
    d.ellipse([CX + 20, 82, CX + 36, 98], fill=DGREY if off else YELLOW)
    draw_text(img, "CONSCIENCE", CX + 28, 102, LGREY if off else YELLOW)
    if off:
        img.paste((0, 0, 0), (0, 70, W, 116))
        draw_text(img, "...", CX, 86, DGREY, scale=2)


level_scene('q1', 1, draw_q1, "TU MONTES ?")
level_scene('q2', 2, draw_q2, "TU DIS OUI ?")
level_scene('q3', 3, draw_q3, "TU DIS OUI ?")
level_scene('q4', 4, draw_q4, "TU DIS OUI ?")


# le piège ---------------------------------------------------------------------
TRAP_T = at('piege', "qu'est-ce")
SFX.append((TRAP_T, 'impact', None))


@scene(sb('piege'), sb('profil'))
def s_piege(img, t):
    draw_text(img, "TÉLÉPORTEUR :", 70, TOP, WHITE)
    draw_text(img, "NON", 136, TOP - 4, RED, scale=2)
    if t >= at('piege', "mais oui"):
        draw_text(img, "ANESTHÉSIE :", 70, TOP + 24, WHITE)
        draw_text(img, "OUI", 136, TOP + 20, GREEN, scale=2)
    if t >= TRAP_T:
        p = ease_out_back((t - TRAP_T) / 0.4)
        draw_text(img, "?", CX, int(110 + (1 - p) * 10), YELLOW, scale=5, shadow=PURPLE)
        draw_text(img, "QUI SE RÉVEILLE", CX, 180, WHITE, scale=2, maxw=170)
        draw_text(img, "VRAIMENT ?", CX, 202, YELLOW, scale=2, shadow=PURPLE)


# les profils ------------------------------------------------------------------
PROFILES = [(at('profil', "Zéro"), "0 OUI", "L'ÂME", GHOST, (220, 225, 255)),
            (at('profil', "Quatre"), "4 OUI", "L'INFORMATION", None, GREEN),
            (at('profil', "Entre"), "1 À 3", "LE PARADOXE", None, YELLOW)]
for ti, *_ in PROFILES:
    SFX.append((ti, 'coin', None))


@scene(sb('profil'), sb('cta'))
def s_profil(img, t):
    draw_text(img, "TON RÉSULTAT", CX, TOP - 6, WHITE, scale=2, shadow=PURPLE)
    for k, (ti, score, name, spr, col) in enumerate(PROFILES):
        if t < ti:
            continue
        y = TOP + 26 + k * 50
        p = ease_out_back((t - ti) / 0.35)
        x = int(18 + (1 - p) * -40)
        img.paste(SHADOW, (x + 2, y + 2, x + 146, y + 44))
        img.paste((30, 34, 70), (x, y, x + 144, y + 42))
        img.paste(col, (x, y, x + 3, y + 42))
        if spr is not None:
            put(img, spr, x + 22, y + 21, 3)
        elif name == "L'INFORMATION":
            for r in range(4):
                bits = ''.join('1' if (r * 7 + c + int(t * 4)) % 3 else '0' for c in range(5))
                draw_text(img, bits, x + 22, y + 4 + r * 9, GREEN, shadow=None)
        else:
            draw_text(img, "∞", x + 22, y + 14, YELLOW, scale=2, shadow=None)
        draw_text(img, score, x + 92, y + 6, LGREY)
        draw_text(img, name, x + 92, y + 20, col, scale=1, maxw=100)


# fin : appel au commentaire puis retour à l'accroche (la vidéo boucle) ------------
SFX.append((N.start('cta'), 'coin', None))


@scene(sb('cta'), DUR)
def s_cta(img, t):
    hook_screen(img, t, cta=True)


if __name__ == '__main__':
    with open(os.path.join(HERE, 'texte_narration.txt'), 'w') as f:
        f.write('\n\n'.join(t for _, t in LINES) + '\n')
    render_video(os.path.join(HERE, 'teleporteur_tiktok.mp4'), DUR, N, loop=True,
                 music=lambda n, dur: np.zeros(n))
