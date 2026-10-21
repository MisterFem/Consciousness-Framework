"""Utopiste ? — Épisode 2/3 : qui paie ?

    python3 ep2_qui_paie.py                 # produit ep2_qui_paie.mp4
    python3 ep2_qui_paie.py preview 2 15    # images de contrôle
"""
from serie import *  # noqa: F403

LINES = [
    ('hook', "C'est bien beau… mais qui va payer ?"),
    ('intro', "Épisode deux sur trois de notre vérification du programme de LFI. Leur réponse : "
              "ceux qui possèdent énormément."),
    ('pas', "Pas celui qui a économisé 30 000 euros. Pas tes parents et leur pavillon. "
            "Les très grandes fortunes."),
    ('buffett', "Même le milliardaire Warren Buffett l'a écrit en 2011 : son taux d'impôt était plus "
                "bas que celui de chacune des vingt autres personnes de son bureau."),
    ('mes', "Alors LFI propose : un ISF renforcé, un impôt plus progressif, une taxe sur les "
            "superprofits, et plus de moyens contre la fraude."),
    ('mamie', "Et l'héritage ? Oublie le fantasme de l'État qui débarque chez mamie pour embarquer "
              "son buffet."),
    ('her', "Jusqu'à 120 000 euros par parent et par enfant : zéro impôt. Puis une taxe progressive. "
            "Et tout en haut, un plafond : 12 millions d'euros."),
    ('pas12', "Pas 12 000. Pas 120 000. 12 millions. Au-dessus, c'est prélevé."),
    ('obj', "« Oui mais les riches vont partir ! »"),
    ('univ', "C'est prévu : l'impôt universel. Monaco, la Suisse ou Dubaï ne sont plus un bouton "
             "magique « supprimer mes impôts » : tu restes imposé en tant que Français, en déduisant "
             "ce que tu paies déjà là-bas."),
    ('disc', "On peut discuter de sa faisabilité. Mais ce n'est pas « on taxe et on prie pour que "
             "personne ne parte »."),
    ('fin', "Alors, utopiste ? Le mécanisme existe. Et la retraite à 60 ans ? C'est l'épisode trois. "
            "Dis-moi en commentaire ce que t'en penses."),
]
MEASURED = None  # {id: (début, fin)} mesurés sur audio/ep2.mp3
EP = Episode(LINES, scene_starts={'intro': 0.2, 'pas': 0.5, 'buffett': 0.8, 'mes': 0.8, 'mamie': 0.8,
                                  'pas12': 0.4, 'obj': 0.8, 'univ': 0.4, 'disc': 0.6, 'fin': 0.8},
             inner_gaps={'her': 0.4},
             measured=MEASURED, audio=os.path.join(HERE, 'audio', 'ep2.mp3'))
sb, at, start, stop = EP.sb, EP.at, EP.start, EP.stop

# ---------------------------------------------------------------- sprites
PIGGY = art(["..pppp..", ".pppppp.", "ppkppppp", "pppppppr", ".pppppp.", ".p.pp.p."],
            {'p': PINK, 'k': INK, 'r': (200, 80, 120)})
HOUSE = art(["....r....", "...rrr...", "..rrrrr..", ".rrrrrrr.", "rrrrrrrrr", ".wwwwwww.",
             ".wbwwwbw.", ".wwwddww.", ".wwwddww."],
            {'r': RED, 'w': WHITE, 'b': BLUE, 'd': BROWN})
COIN = art([".yyyy.", "yyooyy", "yoyyoy", "yoyyoy", "yyooyy", ".yyyy."], {'y': YELLOW, 'o': ORANGE})
MAMIE = art(["..gggg..", ".gggggg.", "..ssss..", "..kssk..", "..ssss..", ".pppppp.", "spppppps",
             ".pppppp.", ".pppppp.", "..k..k.."],
            {'g': LGREY, 's': PEACH, 'k': INK, 'p': LAVENDER})
BUFFET = art(["bbbbbbbbbbbb", "bwwbwwbwwbwb", "bwwbwwbwwbwb", "bbbbbbbbbbbb", "bdddddddddb.",
              "bdyddddydddb", "bdddddddddb.", "bbbbbbbbbbbb", ".b........b."],
             {'b': BROWN, 'w': CYAN, 'd': (120, 60, 40), 'y': YELLOW})
AGENT = art(["..kkkk..", ".kkkkkk.", "..ssss..", "..ssss..", ".nnnnnn.", "snnwnnns", ".nnnnnn.",
             ".nn..nn.", ".kk..kk."],
            {'k': INK, 's': PEACH, 'n': NAVY, 'w': WHITE})
PLANE = art(["....w.......", "....ww......", "wwwwwwwwwwr.", ".wbwbwbwwwww", "wwwwwwwwwwr.",
             "....ww......", "....w......."], {'w': WHITE, 'b': BLUE, 'r': RED})


def coin_tower(img, x, base, n):
    for k in range(n):
        big_sprite(img, COIN, x, base - k * 5, 2)


# ================================================================ SCÈNES
SFX.append((0.0, 'impact', None))
EP_T = start('intro')
TARGET_T = at('intro', "Leur réponse")


@scene(0.0, sb('pas'))
def s_hook(img, t):
    episode_tag(img, 2, t)
    if t < EP_T:
        for k, line in enumerate(("« C'EST BIEN", "BEAU... MAIS")):
            draw_text(img, line, CX, TOP + 14 + k * 22, WHITE, scale=2, maxw=MAXW + 6)
        rubber_stamp(img, "QUI PAIE ? »", CX, TOP + 82, t, -1)
        big_sprite(img, SCEPTIC, 136, 196, 3)
        draw_text(img, "LE SCEPTIQUE", 136, 222, LGREY)
        draw_text(img, "LE PROGRAMME LFI, VÉRIFIÉ EN 3 ÉPISODES", 62, 186, CYAN, maxw=90)
        return
    p = pop(t, EP_T)
    draw_text(img, "ÉPISODE 2", CX, int(TOP + 20 + (1 - p) * 10), CYAN, scale=2)
    draw_text(img, "QUI PAIE ?", CX, TOP + 44, YELLOW, scale=3, shadow=PURPLE, maxw=170)
    if t >= TARGET_T:
        coin_tower(img, CX, 200, int(clamp((t - TARGET_T) / 1.0) * 12))
        draw_text(img, "CEUX QUI POSSÈDENT *ÉNORMÉMENT*", CX, 214, WHITE, maxw=MAXW)


# pas toi -----------------------------------------------------------------
PAS_T = [at('pas', "Pas celui"), at('pas', "Pas tes"), at('pas', "Les très")]
for ti in PAS_T:
    SFX.append((ti, 'place', 10))


@scene(sb('pas'), sb('buffett'))
def s_pas(img, t):
    episode_tag(img, 2, t)
    draw_text(img, "QUI EST CONCERNÉ ?", CX, TOP + 14, CYAN)
    if t >= PAS_T[0]:
        big_sprite(img, PIGGY, 40, 100, 3)
        draw_text(img, "30 000 €", 40, 118, WHITE)
        draw_text(img, "PAS TOI ✓", 40, 132, GREEN)
    if t >= PAS_T[1]:
        big_sprite(img, HOUSE, 120, 98, 3)
        draw_text(img, "LE PAVILLON", 120, 118, WHITE)
        draw_text(img, "PAS EUX ✓", 120, 132, GREEN)
    if t >= PAS_T[2]:
        n = int(clamp((t - PAS_T[2]) / 1.0) * 10)
        for j in range(4):
            coin_tower(img, 48 + j * 24, 226, n + (j % 2) * 2)
        if n >= 10:
            rubber_stamp(img, "CIBLE", CX, 166, t, PAS_T[2] + 1.0, angle=-6)
        draw_text(img, "TRÈS GRANDES FORTUNES", CX, 232, YELLOW)


# Warren Buffett -----------------------------------------------------------
Q_T = at('buffett', "Warren")
BARS_T = at('buffett', "son taux")
SFX.append((Q_T, 'coin', None))


@scene(sb('buffett'), sb('mes'))
def s_buffett(img, t):
    episode_tag(img, 2, t)
    quote_card(img, t, Q_T, "CE QUE J'AI PAYÉ NE REPRÉSENTAIT QUE *17,4 %* DE MON REVENU "
                            "IMPOSABLE, UN TAUX PLUS BAS QUE CELUI DE CHACUNE DES *20 AUTRES "
                            "PERSONNES* DE NOTRE BUREAU.",
               "WARREN BUFFETT, MILLIARDAIRE", "NEW YORK TIMES, 14/08/2011", y=TOP + 8)
    if t >= BARS_T:
        p = ease_io((t - BARS_T) / 1.0)
        for k, (lab, val, txt, col) in enumerate((("BUFFETT", 0.174, "17,4 %", YELLOW),
                                                  ("BUREAU", 0.36, "~36 %", CYAN))):
            y = 220 + k * 13
            draw_text(img, lab, 38, y, WHITE)
            w = int(val * 160 * p)
            img.paste(col, (62, y + 1, 62 + w, y + 9))
            draw_text(img, txt, 62 + w + 4 + text_w(txt) // 2, y, col)


# les mesures ---------------------------------------------------------------
M2 = [(at('mes', "un ISF"), "*ISF* RENFORCÉ"), (at('mes', "un impôt"), "IMPÔT *PLUS PROGRESSIF*"),
      (at('mes', "une taxe"), "TAXE SUR LES *SUPERPROFITS*"),
      (at('mes', "et plus de"), "+ DE MOYENS *CONTRE LA FRAUDE*")]
for ti, _ in M2:
    SFX.append((ti, 'place', 12))


@scene(sb('mes'), sb('mamie'))
def s_mes(img, t):
    episode_tag(img, 2, t)
    draw_text(img, "CE QUE PROPOSE LFI", CX, TOP + 14, CYAN)
    checklist(img, t, M2, TOP + 38, dy=30)


# l'héritage ---------------------------------------------------------------
AGENT_T = at('mamie', "de l'État")
FANT_T = stop('mamie') - 0.3
impact(FANT_T, 2)
H_ZERO, H_PROG, H_CAP = at('her', "Jusqu'à"), at('her', "Puis"), at('her', "Et tout en haut")


def heritage(img, t, y=190):
    """Jauge : 0 € jusqu'à 120 000 €, progressif, plafond 12 M€."""
    x0, x1, x2, x3 = 18, 52, 132, 152
    draw_text(img, "PAR PARENT ET PAR ENFANT", CX, y - 38, WHITE)
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
        draw_text(img, "12 M€", x2, y - 13, YELLOW)
        draw_text(img, "PLAFOND", x2 - 6, y - 25, YELLOW)


@scene(sb('mamie'), sb('pas12'))
def s_mamie(img, t):
    episode_tag(img, 2, t)
    if t < start('her'):
        big_sprite(img, BUFFET, 110, 150, 4)
        big_sprite(img, MAMIE, 64, 150, 4)
        if t >= AGENT_T:
            x = 30 - (t - AGENT_T) * 6
            big_sprite(img, AGENT, max(-10, x) + 0, 150, 4)
        if t >= FANT_T:
            rubber_stamp(img, "FANTASME", CX, 110, t, FANT_T, angle=-10, scale=3)
        draw_text(img, "L'HÉRITAGE ?", CX, TOP + 16, WHITE, scale=2)
        return
    draw_text(img, "L'HÉRITAGE SELON LFI", CX, TOP + 16, CYAN)
    big_sprite(img, MAMIE, 40, 120, 3)
    big_sprite(img, BUFFET, 104, 120, 3)
    draw_text(img, "✓", 140, 96, GREEN, scale=2)
    heritage(img, t)


# 12 millions --------------------------------------------------------------
P12 = [at('pas12', "Pas 12 000"), at('pas12', "Pas 120"), at('pas12', "12 millions."), at('pas12', "Au-dessus")]
for ti in P12[:2]:
    SFX.append((ti, 'place', 6))
impact(P12[2], 4)


@scene(sb('pas12'), sb('obj'))
def s_12(img, t):
    episode_tag(img, 2, t)
    d = ImageDraw.Draw(img)
    for k, (ti, txt) in enumerate(((P12[0], "12 000 €"), (P12[1], "120 000 €"))):
        if t >= ti:
            y = TOP + 22 + k * 26
            draw_text(img, txt, CX, y, LGREY, scale=2)
            if t >= ti + 0.4:
                d.line([(CX - 54, y + 12), (CX + 54, y + 6)], fill=STAMP_RED, width=2)
    if t >= P12[2]:
        p = pop(t, P12[2])
        draw_text(img, "12 000 000 €", CX, int(132 + (1 - p) * 10), YELLOW, scale=2, shadow=PURPLE)
        burst(img, t, P12[2], CX, 140)
    if t >= P12[3]:
        box(img, 180, 214)
        draw_text(img, "AU-DESSUS :", CX, 184, WHITE)
        draw_text(img, "PRÉLEVÉ", CX, 196, STAMP_RED, scale=1)


# « les riches vont partir » + impôt universel --------------------------------
DEST = [(at('univ', "Monaco"), "MONACO"), (at('univ', "la Suisse"), "SUISSE"), (at('univ', "Dubaï"), "DUBAÏ")]
BTN_T = at('univ', "bouton")
OFF_T = at('univ', "tu restes")
SFX.append((OFF_T, 'impact', None))


@scene(sb('obj'), sb('disc'))
def s_univ(img, t):
    episode_tag(img, 2, t)
    if t < start('univ'):
        sceptic(img, t, start('obj'), "LES RICHES *VONT PARTIR* !", y=180)
        lt = t - start('obj')
        if lt > 0.4:
            x = -20 + (lt - 0.4) * 90
            big_sprite(img, PLANE, x, 120 - (lt - 0.4) * 12, 2)
        return
    draw_text(img, "L'IMPÔT UNIVERSEL", CX, TOP + 14, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    for k, (ti, name) in enumerate(DEST):
        if t >= ti:
            draw_text(img, name, 32 + k * 52, TOP + 62, WHITE)
    if t >= BTN_T:
        on = t < OFF_T
        y = 124
        img.paste(SHADOW, (CX - 44, y + 4, CX + 48, y + 30))
        img.paste(STAMP_RED if on else DGREY, (CX - 46, y, CX + 46, y + 26))
        img.paste((255, 90, 110) if on else LGREY, (CX - 46, y, CX + 46, y + 3))
        draw_text(img, "SUPPRIMER", CX, y + 3, WHITE, shadow=None)
        draw_text(img, "MES IMPÔTS", CX, y + 14, WHITE, shadow=None)
        if not on:
            rubber_stamp(img, "DÉSACTIVÉ", CX, y + 14, t, OFF_T, col=YELLOW, angle=-12)
    if t >= OFF_T + 0.6:
        box(img, 172, 238)
        draw_text(img, "TU RESTES IMPOSÉ", CX, 176, WHITE)
        draw_text(img, "*EN TANT QUE FRANÇAIS*", CX, 188, WHITE)
        draw_text(img, "- CE QUE TU PAIES DÉJÀ LÀ-BAS", CX, 206, LGREY, maxw=MAXW)


S_DISC = EP.N.text("FAISABILITÉ : *ÇA SE DISCUTE*", 'disc', 110)
PRIE_T = at('disc', "Mais")


@scene(sb('disc'), sb('fin'))
def s_disc(img, t):
    episode_tag(img, 2, t)
    S_DISC.draw(img, t, CX)
    if t >= PRIE_T:
        draw_text(img, "« ON TAXE ET", CX, 140, LGREY, scale=2)
        draw_text(img, "ON PRIE »", CX, 162, LGREY, scale=2)
        if t >= PRIE_T + 0.9:
            ImageDraw.Draw(img).line([(24, 176), (144, 142)], fill=STAMP_RED, width=3)
            draw_text(img, "UNE RÉPONSE EST PRÉVUE", CX, 196, GREEN)


# verdict ------------------------------------------------------------------
STAMP_T, FIX_T = at('fin', "Alors"), at('fin', "Le mécanisme")
SFX.append((STAMP_T, 'impact', None))
SFX.append((FIX_T + 0.35, 'sparkle', None))
NEXT_T, COM_T = at('fin', "Et la retraite"), at('fin', "Dis-moi")


@scene(sb('fin'), EP.dur)
def s_fin(img, t):
    episode_tag(img, 2, t)
    verdict(img, t, STAMP_T, FIX_T)
    if t >= NEXT_T:
        p = pop(t, NEXT_T)
        box(img, 180, 244)
        draw_text(img, "ÉPISODE 3", CX, int(183 + (1 - p) * 6), CYAN)
        draw_text(img, "RETRAITE", CX, 196, YELLOW, scale=2, shadow=PURPLE, maxw=170)
        draw_text(img, "À 60 ANS", CX, 218, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    if t >= COM_T:
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 176)


if __name__ == '__main__':
    EP.write_text(os.path.join(HERE, 'texte_ep2.txt'))
    render(EP, 'ep2_qui_paie.mp4', MUSIC_SERIE)
