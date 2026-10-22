"""Vidéo TikTok pixel art : le voile d'ignorance (Rawls, 1971), avec un ticket.

Le spectateur choisit un ticket de couleur au début, écrit trois règles de
société (A ou B) sans savoir quelle vie se cache derrière, puis les tickets
sont retournés : chacun découvre SA vie et ce que ses règles y changent.
Pas de musique (ajoutée au montage).

    python3 make_video.py                 # produit voile_ignorance_tiktok.mp4
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
CHOOSE = 2.8       # temps laissé pour choisir

LINES = [
    ('hook', "Choisis un ticket. Vite. Il va décider de toute ta vie."),
    ('retiens', "Rouge, bleu, jaune ou vert. Retiens bien ta couleur."),
    ('regle', "Demain, tu renais. Mais avant, c'est toi qui écris les règles de la société… sans "
              "savoir quelle vie se cache derrière ton ticket."),
    ('r1', "Première règle : la santé. A : chacun paie ses soins, et les impôts sont bas. B : les "
           "soins sont gratuits pour tous, et les impôts plus élevés."),
    ('r2', "Deuxième règle : le travail. A : si tu perds ton emploi, tu te débrouilles, mais tu "
           "gardes plus d'argent. B : une aide est prévue pour tous, financée par tous."),
    ('r3', "Troisième règle : l'héritage. A : on transmet tout à ses enfants. B : les très gros "
           "héritages sont limités, et redistribués."),
    ('tirage', "Tes règles sont écrites. Maintenant… on retourne les tickets."),
    ('rouge', "Rouge : tu nais dans une famille très riche. Avec les règles A, tout va bien pour toi."),
    ('bleu', "Bleu : tu nais dans une famille modeste. Si tu as choisi B pour l'héritage, tu démarres "
             "avec une vraie chance."),
    ('jaune', "Jaune : tu nais avec une maladie chronique. Si tu as choisi A pour la santé… tes soins "
              "vont te coûter très cher."),
    ('vert', "Vert : à quarante ans, tu perds ton emploi. Avec la règle A pour le travail, tu n'as "
             "plus rien."),
    ('rawls', "C'est le voile d'ignorance, imaginé par le philosophe John Rawls en 1971. Son idée : "
              "une société juste, c'est celle que tu choisirais sans savoir qui tu seras."),
    ('cta', "Alors : ta couleur, et tes règles t'ont sauvé ? Dis-le en commentaire."),
]
SCENE_STARTS = {'retiens': 0.3, 'regle': CHOOSE, 'r1': 0.6, 'r2': CHOOSE, 'r3': CHOOSE,
                'tirage': CHOOSE, 'rouge': 0.6, 'bleu': 0.6, 'jaune': 0.6, 'vert': 0.6,
                'rawls': 0.8, 'cta': 0.6}
INNER_GAPS = {}
# {id: (début, fin)} mesurés sur audio/narration.mp3 (silences > 0,12 s)
MEASURED = {
    'hook': (0.0, 3.23), 'retiens': (3.69, 7.45), 'regle': (7.80, 14.63), 'r1': (15.30, 23.88),
    'r2': (24.50, 34.19), 'r3': (34.79, 42.87), 'tirage': (43.53, 46.73), 'rouge': (47.37, 52.23),
    'bleu': (52.82, 58.96), 'jaune': (59.53, 66.17), 'vert': (66.79, 72.39), 'rawls': (73.00, 82.49),
    'cta': (82.94, 86.7),
}


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


def nxt(pid):
    return sb(ids[ids.index(pid) + 1])


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


TICKETS = [("ROUGE", RED), ("BLEU", BLUE), ("JAUNE", YELLOW), ("VERT", GREEN)]


def ticket(img, cx, cy, name, col, face_up=True, flip=1.0, scale=1.0):
    """Ticket à bords perforés ; flip < 1 l'écrase horizontalement (retournement)."""
    w, h = int(56 * scale * max(0.06, flip)), int(30 * scale)
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    img.paste(SHADOW, (x0 + 3, y0 + 3, x0 + w + 3, y0 + h + 3))
    body = col if face_up else (70, 60, 110)
    img.paste(body, (x0, y0, x0 + w, y0 + h))
    for y in range(y0 + 3, y0 + h - 2, 5):
        img.paste((14, 15, 40), (x0, y, x0 + 2, y + 2))
        img.paste((14, 15, 40), (x0 + w - 2, y, x0 + w, y + 2))
    if flip > 0.5:
        if face_up:
            draw_text(img, "TICKET", cx, y0 + 4, INK, shadow=None)
            draw_text(img, name, cx, y0 + 16, WHITE if col != YELLOW else INK, shadow=None)
        else:
            draw_text(img, "?", cx, y0 + 4, LAVENDER, scale=2, shadow=None)


GRID = [(54, 124), (126, 124), (54, 166), (126, 166)]


def ticket_grid(img, t, face_up=True, shuffle=0.0, flips=None):
    for k, (name, col) in enumerate(TICKETS):
        x, y = GRID[k]
        if shuffle > 0:
            # les tickets tournent autour du centre (mélange)
            a = shuffle * 2 * math.pi + k * math.pi / 2
            x = CX + math.cos(a) * 40
            y = 145 + math.sin(a) * 24
        f = 1.0 if flips is None else flips[k]
        up = face_up if flips is None else f >= 0
        bob = math.sin(t * 3 + k) * 1.5
        ticket(img, x, y + bob, name, col, face_up=up, flip=abs(f) if flips else 1.0)


def countdown(img, t, t0, label="CHOISIS !"):
    if t < t0:
        return
    p = clamp((t - t0) / CHOOSE)
    img.paste(SHADOW, (28, 226, 152, 240))
    img.paste(YELLOW, (30, 228, int(30 + 120 * (1 - p)), 238))
    draw_text(img, label, CX, 228, INK, shadow=None)


def arrow(img, x, y, col=YELLOW):
    rows = ["......#...", "......##..", "#########.", "##########", "#########.",
            "......##..", "......#..."]
    m = mask_img(rows_to_mask(rows), 2)
    img.paste(SHADOW, (int(x) + 2, int(y) + 2), m)
    img.paste(col, (int(x), int(y)), m)


# icônes des vies et des règles
CROSS = art(["..rr..", "..rr..", "rrrrrr", "rrrrrr", "..rr..", "..rr.."], {'r': RED})
COINS = art([".yyyy.", "yyooyy", "yoyyoy", "yyooyy", ".yyyy."], {'y': YELLOW, 'o': ORANGE})
BRIEF = art([".bbbb.", "bbbbbb", "bkbbkb", "bbbbbb", "bbbbbb"], {'b': BROWN, 'k': INK})
HOUSE = art(["...r...", "..rrr..", ".rrrrr.", "rrrrrrr", ".wwwww.", ".wbwdw.", ".wwwdw."],
            {'r': RED, 'w': WHITE, 'b': BLUE, 'd': BROWN})
MANSION = art(["....y....", "...yyy...", "..yyyyy..", ".yyyyyyy.", "wwwwwwwww", "wbwbwbwbw",
               "wwwwdwwww", "wbwwdwwbw"], {'y': YELLOW, 'w': WHITE, 'b': BLUE, 'd': BROWN})
PILL = art([".rrww.", "rrrwww", "rrrwww", ".rrww."], {'r': RED, 'w': WHITE})
BOX = art(["bbbbbbb", "b.....b", "b.ppp.b", "bbbbbbb"], {'b': BROWN, 'p': LGREY})
CRADLE = art(["..ppppp..", ".pssssp..", "pwwwwwwwp", "pwwwwwwwp", ".ppppppp.", "p.......p"],
             {'p': PINK, 's': PEACH, 'w': WHITE})
VEIL = [(80, 70, 130), (60, 50, 110)]


def veil(img, t, y0=88, y1=190):
    """Le voile : rideau qui ondule devant les tickets."""
    for x in range(20, 160, 6):
        sway = int(math.sin(t * 2 + x * 0.15) * 2)
        img.paste(VEIL[(x // 6) % 2], (x + sway, y0, x + 6 + sway, y1))
    img.paste(LAVENDER, (18, y0 - 3, 162, y0))


# ================================================================ SCÈNES
SFX.append((0.0, 'crash', None))
PICK_T = N.stop('retiens')
for k in range(3):
    SFX.append((PICK_T + k * CHOOSE / 3, 'place', 6 - k * 2))


@scene(0.0, sb('regle'))
def s_hook(img, t):
    draw_text(img, "CHOISIS", CX, TOP - 6, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "UN TICKET", CX, TOP + 16, YELLOW, scale=2, shadow=PURPLE)
    draw_text(img, "IL VA DÉCIDER DE TA VIE", CX, TOP + 40, WHITE, maxw=150)
    if t < PICK_T + CHOOSE * 0.7:
        ticket_grid(img, t)
    else:
        # les tickets se retournent puis se mélangent
        p = clamp((t - PICK_T - CHOOSE * 0.7) / 0.6)
        ticket_grid(img, t, face_up=False, shuffle=p * 0.75)
    if t >= N.start('retiens'):
        img.paste(SHADOW, (24, 196, 156, 220))
        draw_text(img, "RETIENS TA *COULEUR*", CX, 202, WHITE, maxw=150)
    countdown(img, t, PICK_T)


# le principe ------------------------------------------------------------------
RENAIS_T, REGLES_T, SANS_T = at('regle', "Demain"), at('regle', "c'est toi"), at('regle', "sans")


@scene(sb('regle'), sb('r1'))
def s_regle(img, t):
    draw_text(img, "DEMAIN,", CX, TOP - 6, WHITE, scale=2)
    draw_text(img, "TU RENAIS", CX, TOP + 16, YELLOW, scale=2, shadow=PURPLE)
    put(img, CRADLE, CX, 104 + int(math.sin(t * 4) * 1), 4)
    if t >= REGLES_T:
        draw_text(img, "MAIS AVANT, TU ÉCRIS", CX, 134, WHITE, maxw=150)
        draw_text(img, "*LES RÈGLES*", CX, 148, WHITE, scale=2, maxw=170)
    if t >= SANS_T:
        img.paste(SHADOW, (18, 180, 162, 230))
        for k in range(4):
            ticket(img, 36 + k * 36, 196, "", (70, 60, 110), face_up=False, scale=0.55)
        draw_text(img, "SANS SAVOIR QUELLE VIE", CX, 208, WHITE, maxw=150)
        draw_text(img, "EST DERRIÈRE TON TICKET", CX, 218, LGREY, maxw=150)


# les trois règles --------------------------------------------------------------
RULES = [
    ('r1', 1, "LA SANTÉ", ("CHACUN PAIE SES SOINS", "IMPÔTS BAS", COINS),
     ("SOINS GRATUITS", "IMPÔTS PLUS HAUTS", CROSS)),
    ('r2', 2, "LE TRAVAIL", ("PAS D'AIDE AU CHÔMAGE", "PLUS D'ARGENT EN POCHE", COINS),
     ("AIDE SI TU PERDS TON EMPLOI", "FINANCÉE PAR TOUS", BRIEF)),
    ('r3', 3, "L'HÉRITAGE", ("ON TRANSMET TOUT", "À SES ENFANTS", MANSION),
     ("GROS HÉRITAGES LIMITÉS", "ET REDISTRIBUÉS", HOUSE)),
]


def option_card(img, y, letter, line1, line2, icon, col, t, show):
    if not show:
        return
    img.paste(SHADOW, (20, y + 2, 162, y + 48))
    img.paste((30, 34, 70), (18, y, 160, y + 46))
    img.paste(col, (18, y, 22, y + 46))
    draw_text(img, letter, 32, y + 6, col, scale=2)
    put(img, icon, 32, y + 34, 2)
    draw_text(img, line1, 98, y + 5, WHITE, maxw=112)
    draw_text(img, line2, 98, y + 31, LGREY, maxw=112)


def rule_scene(pid, n, title, opt_a, opt_b):
    a_t, b_t, end_t = at(pid, "A :"), at(pid, "B :"), N.stop(pid)
    SFX.append((N.start(pid), 'whoosh', None))
    SFX.append((a_t, 'place', 10))
    SFX.append((b_t, 'place', 14))
    for k in range(3):
        SFX.append((end_t + k * CHOOSE / 3, 'place', 6 - k * 2))

    @scene(sb(pid), nxt(pid))
    def _s(img, t):
        draw_text(img, f"RÈGLE {n}/3", CX, TOP - 6, LGREY)
        draw_text(img, title, CX, TOP + 6, YELLOW, scale=2, shadow=PURPLE, maxw=170)
        option_card(img, 86, "A", *opt_a, ORANGE, t, t >= a_t)
        option_card(img, 140, "B", *opt_b, BLUE, t, t >= b_t)
        if t >= end_t:
            draw_text(img, "A OU B ? RETIENS !", CX, 200, WHITE, scale=1, maxw=150)
        countdown(img, t, end_t)


for spec in RULES:
    rule_scene(*spec)


# le tirage --------------------------------------------------------------------
FLIP_T = at('tirage', "on retourne")
SFX.append((FLIP_T, 'impact', None))


@scene(sb('tirage'), sb('rouge'))
def s_tirage(img, t):
    draw_text(img, "TES RÈGLES", CX, TOP - 6, WHITE, scale=2)
    draw_text(img, "SONT ÉCRITES", CX, TOP + 16, WHITE, scale=2)
    if t < FLIP_T:
        ticket_grid(img, t, face_up=False)
        veil(img, t, 92, 178)
        draw_text(img, "LE TIRAGE...", CX, 196, YELLOW, scale=2, shadow=PURPLE)
        return
    # le voile se lève, les tickets se retournent un par un
    flips = []
    for k in range(4):
        p = clamp((t - FLIP_T - k * 0.35) / 0.4)
        flips.append(-(1 - 2 * p) if p < 0.5 else 2 * p - 1)
    ticket_grid(img, t, flips=flips)
    lift = clamp((t - FLIP_T) / 0.5)
    veil(img, t, 92, int(178 - 86 * lift))
    draw_text(img, "TA VIE EST...", CX, 196, YELLOW, scale=2, shadow=PURPLE)


# les quatre vies -----------------------------------------------------------------
LIVES = [
    ('rouge', 0, MANSION, "FAMILLE TRÈS RICHE",
     [("RÈGLES A", "TOUT VA BIEN", GREEN), ("RÈGLES B", "TU PAIES PLUS", ORANGE)]),
    ('bleu', 1, HOUSE, "FAMILLE MODESTE",
     [("HÉRITAGE B", "UNE VRAIE CHANCE", GREEN), ("HÉRITAGE A", "TU PARS DE ZÉRO", RED)]),
    ('jaune', 2, PILL, "MALADIE CHRONIQUE",
     [("SANTÉ A", "SOINS TRÈS CHERS", RED), ("SANTÉ B", "SOIGNÉ GRATUITEMENT", GREEN)]),
    ('vert', 3, BOX, "EMPLOI PERDU À 40 ANS",
     [("TRAVAIL A", "TU N'AS PLUS RIEN", RED), ("TRAVAIL B", "UNE AIDE TE RATTRAPE", GREEN)]),
]


def life_scene(pid, k, icon, life, verdicts):
    name, col = TICKETS[k]
    SFX.append((N.start(pid), 'coin', None))
    a, b = N.start(pid), N.stop(pid)
    v_times = [a + (b - a) * (0.35 + 0.3 * i / max(1, len(verdicts) - 1)) for i in range(len(verdicts))]

    @scene(sb(pid), nxt(pid))
    def _s(img, t):
        lt = t - sb(pid)
        p = ease_out_back(lt / 0.4)
        ticket(img, CX, TOP + 14, name, col, face_up=True, scale=1.3 * min(1.0, 0.4 + 0.6 * p))
        put(img, icon, CX, 112, 5)
        draw_text(img, life, CX, 142, WHITE, scale=1, maxw=150)
        for i, (rule, text, vcol) in enumerate(verdicts):
            if t >= v_times[i]:
                y = 162 + i * 28
                img.paste(SHADOW, (18, y, 162, y + 24))
                img.paste(vcol, (18, y, 21, y + 24))
                draw_text(img, rule, CX, y + 1, LGREY, maxw=140)
                draw_text(img, text, CX, y + 12, vcol, maxw=140)
    return _s


for spec in LIVES:
    life_scene(*spec)


# Rawls ------------------------------------------------------------------------
RAWLS_T, IDEE_T = at('rawls', "John"), at('rawls', "Son idée")
SFX.append((RAWLS_T, 'place', 14))


@scene(sb('rawls'), sb('cta'))
def s_rawls(img, t):
    draw_text(img, "LE VOILE", CX, TOP - 6, WHITE, scale=2)
    draw_text(img, "D'IGNORANCE", CX, TOP + 16, YELLOW, scale=2, shadow=PURPLE)
    veil(img, t, 92, 140)
    if t >= RAWLS_T:
        draw_text(img, "JOHN RAWLS · 1971", CX, 112, WHITE)
    if t >= IDEE_T:
        img.paste(SHADOW, (18, 152, 162, 224))
        draw_text(img, "UNE SOCIÉTÉ JUSTE :", CX, 158, WHITE, maxw=150)
        draw_text(img, "CELLE QUE TU CHOISIRAIS", CX, 174, YELLOW, maxw=150)
        draw_text(img, "SANS SAVOIR", CX, 188, YELLOW, maxw=150)
        draw_text(img, "QUI TU SERAS", CX, 202, YELLOW, maxw=150)


# fin : retour aux tickets (la vidéo boucle) --------------------------------------
SFX.append((N.start('cta'), 'coin', None))


@scene(sb('cta'), DUR)
def s_cta(img, t):
    draw_text(img, "TA COULEUR ?", CX, TOP - 6, WHITE, scale=2, shadow=PURPLE)
    draw_text(img, "TES RÈGLES T'ONT SAUVÉ ?", CX, TOP + 18, YELLOW, maxw=150)
    ticket_grid(img, t)
    img.paste(SHADOW, (24, 204, 156, 228))
    draw_text(img, "DIS-LE EN COMMENTAIRE", CX, 210, WHITE, maxw=150)
    arrow(img, 140 + abs(math.sin(t * 5)) * 5, 186)


if __name__ == '__main__':
    with open(os.path.join(HERE, 'texte_narration.txt'), 'w') as f:
        f.write('\n\n'.join(t for _, t in LINES) + '\n')
    render_video(os.path.join(HERE, 'voile_ignorance_tiktok.mp4'), DUR, N, loop=True,
                 music=lambda n, dur: np.zeros(n))
