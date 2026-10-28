"""Vidéo TikTok pixel art : le culte de la star, « mesurer le mètre ».

Un supporter filme un joueur assis à un mètre de lui. Toute la vidéo mesure
cette distance autrement : en années de SMIC, puis en règles que quelqu'un a
écrites (naturalisation, doxa), et montre que ce décor se modifie (50+1,
plafonds salariaux). Personnages fictifs. Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit culte_star_tiktok.mp4
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
MAXW = 150

LINES = [(pid, txt) for pid, txt in zip(
    ['hook', 'pourquoi', 'metre', 'place', 'etrange', 'natur', 'doxa', 'inversion', 'choix', 'aimer', 'rappel'],
    open(os.path.join(HERE, 'texte_narration.txt')).read().strip().split('\n\n'))]
TXT = dict(LINES)
# paragraphes repérés dans audio/narration.mp3 (pauses > 0,3 s, alignées sur la longueur du texte)
MEASURED = {
    'hook': (0.0, 11.45), 'pourquoi': (11.88, 13.42), 'metre': (13.99, 21.94), 'place': (22.44, 33.13),
    'etrange': (33.64, 36.99), 'natur': (37.51, 53.48), 'doxa': (53.89, 67.24), 'inversion': (67.69, 75.35),
    'choix': (75.90, 90.92), 'aimer': (91.42, 100.81), 'rappel': (101.34, 105.3),
}
END = 105.48
N = Narration(os.path.join(HERE, 'audio', 'narration.mp3'), MEASURED, [], END)
DUR = END + 1.5


def start(pid):
    return MEASURED[pid][0]


def at(pid, words):
    """Moment où la voix prononce `words` (interpolé sur la longueur du texte)."""
    a, b = MEASURED[pid]
    i = TXT[pid].index(words)
    return a + (b - a) * i / len(TXT[pid])


# ---------------------------------------------------------------- dessins
def art(rows, cmap):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                a[r, c] = (*cmap[ch], 255)
    return Image.fromarray(a, 'RGBA')


def put(img, spr, cx, cy, scale, flip=False):
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    if flip:
        s = s.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


def person(hair, skin, shirt, pants=(40, 40, 70), extra=None):
    rows = ["..hhhh..",
            ".hhhhhh.",
            ".hssssh.",
            "..sksk..",
            "..ssss..",
            ".cccccc.",
            "sccccccs",
            "sccccccs",
            ".cccccc.",
            ".pp..pp.",
            ".pp..pp.",
            ".kk..kk."]
    cmap = {'h': hair, 's': skin, 'k': INK, 'c': shirt, 'p': pants}
    a = art(rows, cmap).copy()
    if extra:
        extra(a)
    return a


def jersey_number(a):
    px = a.load()
    for x, y in ((3, 6), (4, 6), (4, 7), (4, 8)):
        px[x, y] = (*WHITE, 255)


def scarf(a):
    px = a.load()
    for x in range(1, 7):
        px[x, 5] = (*RED, 255) if x % 2 else (*WHITE, 255)


PLAYER = person((30, 20, 15), (150, 100, 70), (30, 50, 120), extra=jersey_number)
FAN = person((120, 70, 30), PEACH, (90, 90, 100), extra=scarf)
CROWD_COLS = [(PEACH, BLUE), ((150, 100, 70), RED), ((230, 170, 120), GREEN), (PEACH, ORANGE),
              ((120, 70, 40), LAVENDER), ((230, 170, 120), YELLOW)]
CROWD = [person(HAIR, skin, shirt) for HAIR, (skin, shirt) in
         zip([INK, BROWN, (90, 60, 30), ORANGE, INK, (60, 40, 30)], CROWD_COLS)]
CROWD_BACK = [art(["..hhhh..", ".hhhhhh.", ".hhhhhh.", "..hhhh..", "..ssss..", ".cccccc.", "sccccccs",
                   "sccccccs", ".cccccc.", ".pp..pp.", ".pp..pp.", ".kk..kk."],
                  {'h': h, 's': s, 'c': c, 'p': (40, 40, 70), 'k': INK})
              for h, (s, c) in zip([INK, BROWN, (90, 60, 30), ORANGE, INK, (60, 40, 30)], CROWD_COLS)]
PHONE = art(["kkkk", "kbbk", "kbbk", "kbbk", "kkkk"], {'k': INK, 'b': BLUE})
APPLE = art(["...g.", "..g..", ".rrr.", "rrrrr", "rrrrr", ".rrr."], {'g': GREEN, 'r': RED})
TICKET = art(["yyyyyyyy", "y.yyyy.y", "yyyyyyyy"], {'y': YELLOW})
COIN = art([".yyyy.", "yyooyy", "yoyyoy", "yyooyy", ".yyyy."], {'y': YELLOW, 'o': ORANGE})


def bench(img, y):
    img.paste((60, 70, 110), (14, y, 166, y + 4))
    img.paste((40, 46, 80), (20, y + 4, 24, y + 14))
    img.paste((40, 46, 80), (156, y + 4, 160, y + 14))


def ruler(img, x0, x1, y, label, col=YELLOW):
    """Règle graduée entre deux points."""
    x0, x1 = int(x0), int(x1)
    img.paste(SHADOW, (x0 + 1, y + 1, x1 + 1, y + 7))
    img.paste(col, (x0, y, x1, y + 6))
    for x in range(x0, x1, 4):
        img.paste(INK, (x, y, x + 1, y + (4 if (x - x0) % 16 == 0 else 2)))
    draw_text(img, label, (x0 + min(x1, W) ) // 2, y + 8, col, maxw=160)


def bubble(img, x0, y0, w, text, fg=INK, bg=WHITE, tail=True):
    lines = len(layout(text.upper(), w - 8))
    h = lines * 12 + 6
    img.paste(SHADOW, (x0 + 2, y0 + 2, x0 + w + 2, y0 + h + 2))
    img.paste(bg, (x0, y0, x0 + w, y0 + h))
    if tail:
        for k in range(4):
            img.paste(bg, (x0 + 10 + k, y0 + h + k, x0 + 14, y0 + h + k + 1))
    draw_text(img, text, x0 + w // 2, y0 + 3, fg, maxw=w - 8, shadow=None, hl_color=RED)
    return h


def caption(img, text, y=206, col=WHITE):
    lines = len(layout(text.upper(), MAXW))
    img.paste(SHADOW, (14, y - 3, 166, y + lines * 12 + 2))
    draw_text(img, text, CX, y, col, maxw=MAXW, shadow=None)


def stamp(img, text, cx, cy, t, t0, col=RED, scale=2, angle=-6):
    if t < t0:
        return
    sc = scale if t - t0 > 0.15 else scale + 1
    w = max(wid for _, wid in layout(text.upper(), 300)) * sc + 12
    h = 12 * sc + 6
    layer = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([2, 2, w + 5, h + 5], outline=col + (255,), width=2)
    tmp = Image.new('RGB', (w + 8, h + 8), (0, 0, 0))
    draw_text(tmp, text, (w + 8) // 2, 5, (255, 255, 255), scale=sc, maxw=600, shadow=None)
    layer.paste(col + (255,), (0, 0), tmp.convert('L').point(lambda v: 255 if v > 128 else 0))
    layer = layer.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)


def scene_bench(img, t, y=150, insults=0.0):
    bench(img, y + 22)
    put(img, FAN, 52, y + 6, 3)
    put(img, PHONE, 70, y + 2, 2)
    put(img, PLAYER, 128, y + 6, 3)


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
COMMENT_T = at('hook', "« Il")
INSULT_T = at('hook', "Il s'est fait")
VRAI_T = at('hook', "Pourtant")
SFX.append((COMMENT_T, 'place', 10))
for k in range(5):
    SFX.append((INSULT_T + k * 0.15, 'blip', None))
INSULTS = [("AIGRI", 20, 72), ("JALOUX VA", 96, 70), ("T'ES QUI TOI ?", 24, 96), ("RABAT-JOIE", 100, 94),
           ("LAISSE LES GENS KIFFER", 30, 118)]


@scene(0.0, MEASURED['pourquoi'][0] - 0.2)
def s_hook(img, t):
    scene_bench(img, t)
    ruler(img, 64, 116, 188, "1 MÈTRE")
    if t < COMMENT_T:
        draw_text(img, "À UN MÈTRE", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE)
        draw_text(img, "D'UNE STAR", CX, TOP + 20, YELLOW, scale=2, shadow=PURPLE)
    if t >= COMMENT_T:
        bubble(img, 16, TOP - 6, 148, "« IL ÉTAIT À CÔTÉ D'UN HUMAIN QUI CHIE COMME NOUS. »")
    if t >= INSULT_T:
        for k, (txt, x, y) in enumerate(INSULTS):
            if t >= INSULT_T + k * 0.25 and t < VRAI_T + 0.4:
                w = min(140, max(wid for _, wid in layout(txt, 300)) + 10)
                bubble(img, x, y + 16, w, txt, fg=WHITE, bg=RED, tail=False)
    if t >= VRAI_T:
        caption(img, "IL N'A RIEN DIT DE FAUX", 214, YELLOW)


@scene(MEASURED['pourquoi'][0] - 0.2, MEASURED['metre'][0] - 0.2)
def s_pourquoi(img, t):
    scene_bench(img, t)
    ruler(img, 64, 116, 188, "1 MÈTRE")
    draw_text(img, "POURQUOI", CX, TOP + 4, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "ÇA DÉRANGE ?", CX, TOP + 26, YELLOW, scale=2, shadow=PURPLE)


SAL_T = at('metre', "Prenons")
SMIC_T = at('metre', "Au SMIC")
SFX.append((SAL_T, 'coin', None))
SFX.append((SMIC_T, 'impact', None))


@scene(MEASURED['metre'][0] - 0.2, MEASURED['place'][0] - 0.2)
def s_metre(img, t):
    draw_text(img, "MESURONS CE MÈTRE", CX, TOP - 4, WHITE, maxw=MAXW)
    draw_text(img, "AUTREMENT", CX, TOP + 8, YELLOW, maxw=MAXW)
    put(img, FAN, 30, 120, 3)
    put(img, PLAYER, 150, 120, 3)
    if t >= SAL_T:
        bubble(img, 104, 70, 72, "500 000 € / MOIS", fg=INK, bg=YELLOW, tail=False)
    stretch = clamp((t - SMIC_T) / 2.5) if t >= SMIC_T else 0
    x1 = 120 + stretch * 900
    ruler(img, 40, min(x1, W + 40), 150, "")
    if t >= SMIC_T:
        years = int(30 * clamp((t - SMIC_T) / 2.5))
        draw_text(img, f"{years} ANS", CX, 166, YELLOW, scale=3, shadow=PURPLE)
        caption(img, "AU SMIC POUR GAGNER *1 MOIS* DE SON SALAIRE", 202)


TICK_T = at('place', "a peut-être")
PAIE_T = at('place', "Il paie")
PREUVE_T = at('place', "Et il repartira")
SFX.append((TICK_T, 'place', 8))
SFX.append((PREUVE_T, 'coin', None))


@scene(MEASURED['place'][0] - 0.2, MEASURED['etrange'][0] - 0.2)
def s_place(img, t):
    draw_text(img, "SA PLACE", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE)
    # le billet « mange » la barre de salaire
    x0, x1, y = 26, 154, 92
    eaten = clamp((t - TICK_T) / 1.5) * 0.35 if t >= TICK_T else 0
    img.paste(SHADOW, (x0 + 2, y + 2, x1 + 2, y + 18))
    img.paste(GREEN, (x0, y, int(x1 - (x1 - x0) * eaten), y + 16))
    img.paste((60, 30, 40), (int(x1 - (x1 - x0) * eaten), y, x1, y + 16))
    draw_text(img, "SON SALAIRE DU MOIS", CX, y + 20, LGREY, maxw=MAXW)
    if t >= TICK_T:
        put(img, TICKET, x1 - (x1 - x0) * eaten / 2, y + 8, 3)
    if t >= PAIE_T:
        put(img, FAN, 46, 162, 3)
        put(img, PLAYER, 134, 162, 3)
        for k in range(4):
            u = ((t * 0.8 + k / 4) % 1)
            put(img, COIN, 60 + u * 60, 150 - math.sin(u * 3.14) * 14, 1)
        draw_text(img, "IL PAIE POUR APPROCHER", CX, 186, WHITE, maxw=MAXW)
        draw_text(img, "QUELQU'UN QU'IL FINANCE", CX, 198, YELLOW, maxw=MAXW)
    if t >= PREUVE_T:
        caption(img, "UNE VIDÉO, COMME *LA PREUVE D'UN PRIVILÈGE*", 214)


DECOR_T = at('etrange', "C'est qu'on")


@scene(MEASURED['etrange'][0] - 0.2, MEASURED['natur'][0] - 0.2)
def s_etrange(img, t):
    fade = clamp((t - DECOR_T) / 1.6) if t >= DECOR_T else 0
    # la scène se fond dans le décor
    scene_bench(img, t)
    ruler(img, 64, 116, 188, "30 ANS", col=YELLOW)
    if fade > 0:
        veil = Image.new('RGB', (W, H), (14, 15, 40))
        img.paste(Image.blend(img, veil, fade * 0.75))
    draw_text(img, "LE PLUS ÉTRANGE,", CX, TOP - 2, WHITE, scale=2, maxw=176, shadow=PURPLE)
    draw_text(img, "CE N'EST PAS L'ÉCART", CX, TOP + 22, WHITE, maxw=MAXW)
    if t >= DECOR_T:
        draw_text(img, "C'EST QU'ON", CX, 200, YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "NE LE VOIT PLUS", CX, 222, YELLOW, scale=2, shadow=PURPLE, maxw=176)


GRAV_T = at('natur', "Comme la gravité")
PERS_T = at('natur', "Sauf que")
DECIDE_T = at('natur', "Un salaire")
NAT_T = at('natur', "la naturalisation")
SFX.append((GRAV_T, 'place', 4))
SFX.append((DECIDE_T, 'place', 12))
SFX.append((NAT_T, 'impact', None))


@scene(MEASURED['natur'][0] - 0.2, MEASURED['doxa'][0] - 0.2)
def s_natur(img, t):
    if t < GRAV_T:
        draw_text(img, "AVANT TA NAISSANCE,", CX, TOP + 4, WHITE, maxw=MAXW)
        draw_text(img, "ÇA RESSEMBLE AU DÉCOR", CX, TOP + 18, YELLOW, maxw=MAXW)
        # un berceau sous un ciel déjà rempli de règles
        for k, word in enumerate(("SALAIRES", "BILLETS", "STARS", "TRIBUNES")):
            draw_text(img, word, 40 + (k % 2) * 100, 96 + (k // 2) * 22, LAVENDER)
        img.paste(PINK, (70, 150, 110, 160))
        img.paste(WHITE, (74, 146, 106, 150))
        return
    # gauche : la gravité / droite : le contrat
    img.paste((40, 44, 80), (89, 66, 91, 190))
    y = 80 + min(1, (t - GRAV_T) / 0.8) ** 2 * 70
    put(img, APPLE, 46, y, 3)
    img.paste((60, 120, 70), (14, 168, 86, 172))
    draw_text(img, "LA GRAVITÉ", 46, 66, WHITE)
    if t >= PERS_T:
        draw_text(img, "PERSONNE", 46, 176, LGREY)
        draw_text(img, "NE L'A ÉCRITE", 46, 188, LGREY)
    if t >= DECIDE_T:
        img.paste(WHITE, (108, 86, 160, 150))
        for k in range(6):
            img.paste(LGREY, (114, 94 + k * 8, 154, 96 + k * 8))
        p = clamp((t - DECIDE_T) / 1.2)
        img.paste(BLUE, (116, 140, 116 + int(34 * p), 142))
        draw_text(img, "UN CONTRAT", 134, 66, WHITE)
        draw_text(img, "QUELQU'UN", 134, 176, YELLOW)
        draw_text(img, "L'A DÉCIDÉ", 134, 188, YELLOW)
    if t >= NAT_T:
        img.paste(SHADOW, (6, 204, 174, 236))
        draw_text(img, "NATURALISATION", CX, 208, RED, scale=2, maxw=176, shadow=None)
        draw_text(img, "UNE DÉCISION PRISE POUR UNE LOI", CX, 224, LGREY, maxw=170, shadow=None)


DOXA_T = at('doxa', "Le sociologue")
BACK_T = at('doxa', "Le commentaire")
SFX.append((DOXA_T, 'coin', None))


@scene(MEASURED['doxa'][0] - 0.2, MEASURED['inversion'][0] - 0.2)
def s_doxa(img, t):
    lt = t - MEASURED['doxa'][0]
    turn = lt > 1.0
    for k in range(9):
        row, col = divmod(k, 3)
        x = 40 + col * 50
        y = 104 + row * 30
        if k == 4 and turn:
            put(img, CROWD[k % 6], x, y, 3)
            for j, (dx, dy) in enumerate(((-30, -20), (30, -20), (-30, 20), (30, 20))):
                if lt > 1.4 + j * 0.15:
                    ImageDraw.Draw(img).line([(x + dx * 0.9, y + dy * 0.9), (x + dx * 0.4, y + dy * 0.4)],
                                             fill=RED, width=1)
        else:
            put(img, CROWD_BACK[k % 6], x, y, 3)
    draw_text(img, "CE QUI VA DE SOI", CX, TOP - 4, WHITE, scale=1, maxw=MAXW)
    if t >= DOXA_T:
        draw_text(img, "LA DOXA", CX, TOP + 8, YELLOW, scale=2, shadow=PURPLE)
        draw_text(img, "PIERRE BOURDIEU", CX, TOP + 28, LGREY)
    if t >= BACK_T:
        caption(img, "INSULTÉ PARCE QU'IL TOUCHAIT *À CE QUI VA DE SOI*", 200)
    elif turn:
        caption(img, "CELUI QUI QUESTIONNE *PASSE POUR LE PROBLÈME*", 200)


AUG_T = at('inversion', "réclamer")
MILL_T = at('inversion', "pour un millionnaire")
SFX.append((MILL_T, 'impact', None))


@scene(MEASURED['inversion'][0] - 0.2, MEASURED['choix'][0] - 0.2)
def s_inversion(img, t):
    put(img, FAN, 50, 150, 4)
    put(img, PLAYER, 136, 150, 4)
    if t >= AUG_T:
        img.paste(WHITE, (18, 74, 84, 100))
        img.paste(BROWN, (49, 100, 53, 128))
        draw_text(img, "AUGMENTEZ-", 51, 76, INK, shadow=None)
        draw_text(img, "LE !", 51, 87, RED, shadow=None)
    if t >= MILL_T:
        for k in range(10):
            put(img, COIN, 120 + (k % 3) * 14, 112 - (k // 3) * 6, 2)
        draw_text(img, "POUR UN", 136, 70, WHITE)
        draw_text(img, "MILLIONNAIRE", 136, 82, YELLOW)
        caption(img, "DÉFENDRE SES INTÉRÊTS *PLUS FORT QUE LES SIENS*", 200)


VOTE_T = at('choix', "En Allemagne")
CAP_T = at('choix', "En NFL")
CHOIX_T = at('choix', "c'est un choix")
SFX.append((VOTE_T, 'place', 10))
SFX.append((CAP_T, 'place', 14))
SFX.append((CHOIX_T, 'impact', None))


@scene(MEASURED['choix'][0] - 0.2, MEASURED['aimer'][0] - 0.2)
def s_choix(img, t):
    draw_text(img, "CE DÉCOR", CX, TOP - 4, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "SE MODIFIE", CX, TOP + 18, YELLOW, scale=2, shadow=PURPLE)
    if t >= VOTE_T:
        draw_text(img, "ALLEMAGNE : 50+1", 52, 112, WHITE, maxw=96)
        for k in range(6):
            x = 18 + k * 12
            up = k < 4
            hh = 12 if up and int(t * 3 + k) % 4 else 8
            img.paste(PEACH, (x, 148 - hh, x + 4, 148))
            img.paste(CROWD_COLS[k][1], (x - 2, 148, x + 6, 160))
        draw_text(img, "LES MEMBRES", 52, 166, LGREY)
        draw_text(img, "VOTENT", 52, 178, LGREY)
    if t >= CAP_T:
        draw_text(img, "NFL · RUGBY", 132, 112, WHITE, maxw=90)
        draw_text(img, "PLAFOND", 133, 124, RED)
        img.paste(RED, (110, 136, 156, 138))
        p = clamp((t - CAP_T) / 1.0)
        h = int(44 * p)
        img.paste(GREEN, (124, 182 - h, 142, 182))
        draw_text(img, "SALAIRES", 133, 186, LGREY)
    if t >= CHOIX_T:
        stamp(img, "C'EST UN CHOIX", CX, 218, t, CHOIX_T, col=GREEN, scale=2, angle=-4)


AIGREUR_T = at('aimer', "Ce n'est pas")
DECOR2_T = at('aimer', "Là, on")


@scene(MEASURED['aimer'][0] - 0.2, MEASURED['rappel'][0] - 0.2)
def s_aimer(img, t):
    lt = t - MEASURED['aimer'][0]
    for k in range(6):
        x = 22 + k * 27
        y = 150 + (2 if int(t * 4 + k) % 2 else 0)
        put(img, CROWD_BACK[k], x, y, 3)
        img.paste(RED if k % 2 else WHITE, (x - 10, y - 26, x + 10, y - 22))
    draw_text(img, "AIMER LE FOOT", CX, TOP - 2, WHITE, scale=2, shadow=PURPLE, maxw=176)
    draw_text(img, "ET TROUVER ÇA ABSURDE", CX, TOP + 20, YELLOW, maxw=MAXW)
    if t >= AIGREUR_T:
        img.paste(SHADOW, (14, 86, 166, 122))
        draw_text(img, "CRITIQUER LE SYSTÈME", CX, 90, GREEN, maxw=MAXW)
        draw_text(img, "≠ EN VOULOIR AUX GENS", CX, 104, RED, maxw=MAXW)
    if t >= DECOR2_T:
        caption(img, "ON REGARDE SEULEMENT *LE DÉCOR*", 200)


RAPPEL_T = at('rappel', "Ce n'était")
SFX.append((RAPPEL_T, 'sparkle', None))


@scene(MEASURED['rappel'][0] - 0.2, DUR)
def s_rappel(img, t):
    scene_bench(img, t)
    ruler(img, 64, 116, 188, "1 MÈTRE")
    bubble(img, 16, TOP - 6, 148, "« IL CHIE COMME NOUS. »")
    if t >= RAPPEL_T:
        caption(img, "CE N'ÉTAIT PAS UNE INSULTE. C'ÉTAIT UN *RAPPEL*.", 210)


if __name__ == '__main__':
    render_video(os.path.join(HERE, 'culte_star_tiktok.mp4'), DUR, N, loop=True,
                 music=lambda n, dur: np.zeros(n))
