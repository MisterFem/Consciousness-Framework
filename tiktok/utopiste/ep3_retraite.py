"""Utopiste ? — Épisode 3/3 : la retraite à 60 ans.

    python3 ep3_retraite.py                 # produit ep3_retraite.mp4
    python3 ep3_retraite.py preview 2 15    # images de contrôle
"""
from serie import *  # noqa: F403

LINES = [
    ('hook', "C'est bien beau… mais la retraite à 60 ans, c'est impossible."),
    ('intro', "Épisode trois sur trois. Et d'abord, un petit rappel."),
    ('macron', "En 2019, Emmanuel Macron disait : « Tant qu'on n'a pas réglé le problème du chômage dans "
               "notre pays, franchement, ce serait assez hypocrite de décaler l'âge légal. » En 2023, "
               "sa réforme l'a repoussé à 64 ans."),
    ('coffre', "Une retraite, ce n'est pas un coffre où l'État range ton argent pendant quarante ans. "
               "Ce sont les actifs d'aujourd'hui qui paient les retraités d'aujourd'hui."),
    ('lev1', "Donc LFI joue sur trois leviers. Un : des salaires plus hauts, donc plus de cotisations."),
    ('lev2', "Deux : plus 0,25 point de cotisation retraite par an, pendant cinq ans."),
    ('lev3', "Trois : faire cotiser ce qui y échappe aujourd'hui : dividendes, intéressement, "
             "participation."),
    ('bain', "L'idée : élargir le robinet qui remplit la baignoire, au lieu de dire aux gens d'y "
             "rester moins longtemps."),
    ('qui', "Et 60 ans pour qui ? Quarante ans sur un chantier, ce n'est pas quarante ans derrière "
            "un bureau."),
    ('prop', "La proposition : 60 ans à taux plein, avec 40 années de cotisation."),
    ('fin', "Alors, utopiste ? Promettre sans expliquer comment, ça, ce serait utopiste. Ici, chaque "
            "promesse a son mécanisme. Est-ce qu'ils marcheraient tous ? Ça, c'est le vrai débat."),
    ('cta', "Lequel tu veux qu'on démonte ? Dis-le en commentaire."),
]
MEASURED = None  # {id: (début, fin)} mesurés sur audio/ep3.mp3
EP = Episode(LINES, scene_starts={'intro': 0.2, 'macron': 0.3, 'coffre': 1.0, 'lev1': 0.8,
                                  'bain': 0.8, 'qui': 0.8, 'prop': 0.5, 'fin': 0.8},
             inner_gaps={'lev2': 0.3, 'lev3': 0.3, 'cta': 0.4},
             measured=MEASURED, audio=os.path.join(HERE, 'audio', 'ep3.mp3'))
sb, at, start, stop = EP.sb, EP.at, EP.start, EP.stop

# ---------------------------------------------------------------- sprites
VAULT = art(["gggggggggg", "gddddddddg", "gdkkkkkkdg", "gdkyykykdg", "gdkkkkkkdg", "gdkykkykdg",
             "gdkkkkkkdg", "gddddddddg", "gggggggggg", ".g......g."],
            {'g': LGREY, 'd': DGREY, 'k': INK, 'y': YELLOW})
WORKER = art(["..oo..", "..oo..", "..ss..", ".bbbb.", "sbbbbs", ".bbbb.", ".b..b.", ".k..k."],
             {'o': ORANGE, 's': PEACH, 'b': BLUE, 'k': INK})
OLD = art(["..gg...", "..ss...", "..ss...", ".pppp..", "spppps.", ".pppp.c", ".p..p.c", ".k..k.c"],
          {'g': LGREY, 's': PEACH, 'p': LAVENDER, 'k': INK, 'c': BROWN})
SUIT = art(["..kk..", "..kk..", "..ss..", ".dwwd.", "sdwwds", ".dddd.", ".d..d.", ".k..k."],
           {'k': INK, 's': PEACH, 'd': DGREY, 'w': WHITE})
DESK = art(["....mmm...", "....mmm...", "bbbbbbbbbb", "b........b", "b........b"],
           {'m': CYAN, 'b': BROWN})
BRICKS = art(["rrrr.rrrr", "rr.rrrr.r", "rrrr.rrrr", "rr.rrrr.r"], {'r': (190, 80, 50)})


def calendar_age(img, cx, y, age, col):
    img.paste(SHADOW, (cx - 27, y + 3, cx + 31, y + 41))
    img.paste(WHITE, (cx - 30, y, cx + 28, y + 38))
    img.paste(STAMP_RED, (cx - 30, y, cx + 28, y + 9))
    draw_text(img, "ÂGE LÉGAL", cx - 1, y - 1, WHITE, shadow=None, maxw=60)
    draw_text(img, str(age), cx - 1, y + 12, col, scale=2, shadow=None)


# ================================================================ SCÈNES
SFX.append((0.0, 'impact', None))
EP_T = start('intro')


@scene(0.0, sb('macron'))
def s_hook(img, t):
    episode_tag(img, 3, t)
    if t < EP_T:
        for k, line in enumerate(("« C'EST BIEN", "BEAU... MAIS", "60 ANS ?")):
            draw_text(img, line, CX, TOP + 14 + k * 22, YELLOW if k == 2 else WHITE, scale=2,
                      maxw=MAXW + 6)
        rubber_stamp(img, "IMPOSSIBLE »", CX, TOP + 100, t, -1)
        big_sprite(img, SCEPTIC, 136, 196, 3)
        draw_text(img, "LE SCEPTIQUE", 136, 222, LGREY)
        draw_text(img, "LE PROGRAMME LFI, VÉRIFIÉ EN 3 ÉPISODES", 62, 186, CYAN, maxw=90)
        return
    p = pop(t, EP_T)
    draw_text(img, "ÉPISODE 3", CX, int(TOP + 20 + (1 - p) * 10), CYAN, scale=2)
    draw_text(img, "LA RETRAITE", CX, TOP + 44, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    draw_text(img, "À 60 ANS", CX, TOP + 66, YELLOW, scale=3, shadow=PURPLE, maxw=170)
    big_sprite(img, OLD, CX, 170, 5)


# le rappel ------------------------------------------------------------------
Q_T = at('macron', "Emmanuel")
AGE_T = at('macron', "En 2023")
SFX.append((Q_T, 'coin', None))
SFX.append((AGE_T + 0.6, 'impact', None))


@scene(sb('macron'), sb('coffre'))
def s_macron(img, t):
    episode_tag(img, 3, t)
    quote_card(img, t, Q_T, "TANT QU'ON N'A PAS RÉGLÉ LE PROBLÈME DU CHÔMAGE DANS NOTRE PAYS, "
                            "FRANCHEMENT, CE SERAIT *ASSEZ HYPOCRITE DE DÉCALER L'ÂGE LÉGAL*.",
               "EMMANUEL MACRON", "CONFÉRENCE DE PRESSE, 25/04/2019", y=TOP + 8)
    if t >= AGE_T:
        age = 62 + int(2 * clamp((t - AGE_T - 0.2) / 0.5))
        calendar_age(img, 58, 186, age, STAMP_RED if age == 64 else INK)
        draw_text(img, "2023", 124, 196, WHITE, scale=2)
        draw_text(img, "RÉFORME", 124, 216, LGREY)


# pas un coffre --------------------------------------------------------------
NO_VAULT_T = at('coffre', "pendant")
FLOW_T = at('coffre', "Ce sont")


@scene(sb('coffre'), sb('lev1'))
def s_coffre(img, t):
    episode_tag(img, 3, t)
    if t < FLOW_T:
        draw_text(img, "UNE RETRAITE, C'EST...", CX, TOP + 16, WHITE)
        big_sprite(img, VAULT, CX, 130, 6)
        if t >= NO_VAULT_T:
            rubber_stamp(img, "PAS UN COFFRE", CX, 130, t, NO_VAULT_T, angle=-10)
        return
    draw_text(img, "LA RÉPARTITION", CX, TOP + 16, YELLOW, scale=2, shadow=PURPLE, maxw=170)
    lt = t - FLOW_T
    for k in range(4):
        big_sprite(img, WORKER, 28, 100 + k * 26, 2)
    for k in range(3):
        big_sprite(img, OLD, 140, 110 + k * 26, 2)
    draw_text(img, "ACTIFS", 28, 204, CYAN)
    draw_text(img, "RETRAITÉS", 136, 204, CYAN)
    for k in range(10):
        u = ((lt * 0.6 + k / 10) % 1)
        x = int(44 + u * 80)
        y = int(140 - math.sin(u * 3.14) * 16 + (k % 3) * 8)
        img.paste(YELLOW, (x, y, x + 2, y + 2))
    draw_text(img, "AUJOURD'HUI → AUJOURD'HUI", CX, 226, LGREY, maxw=MAXW)


# les trois leviers -------------------------------------------------------------
M3 = [(at('lev1', "Un :"), "SALAIRES ↑ = *COTISATIONS ↑*"),
      (start('lev2'), "*+0,25 POINT* DE COTISATION PAR AN, PENDANT 5 ANS"),
      (start('lev3'), "FAIRE COTISER *DIVIDENDES, INTÉRESSEMENT, PARTICIPATION*")]
for ti, _ in M3:
    SFX.append((ti, 'place', 12))


@scene(sb('lev1'), sb('bain'))
def s_leviers(img, t):
    episode_tag(img, 3, t)
    draw_text(img, "3 LEVIERS POUR LA PAYER", CX, TOP + 14, CYAN)
    checklist(img, t, M3, TOP + 36, dy=40)


# la baignoire ----------------------------------------------------------------
WIDE_T = at('bain', "élargir")
NOT_T = at('bain', "au lieu")


@scene(sb('bain'), sb('qui'))
def s_bain(img, t):
    episode_tag(img, 3, t)
    lt = t - sb('bain')
    w = 2 + int(6 * clamp((t - WIDE_T) / 1.0)) if t >= WIDE_T else 2
    # robinet
    img.paste(LGREY, (54, 78, 96, 86))
    img.paste(LGREY, (88, 78, 96, 96))
    img.paste(CYAN, (92 - w // 2, 96, 92 + w // 2 + 1, 150))
    draw_text(img, "COTISATIONS", 46, 62, CYAN)
    # baignoire
    level = clamp(0.3 + lt * 0.05 * w / 2, 0, 0.9)
    img.paste(WHITE, (30, 150, 140, 154))
    img.paste(WHITE, (30, 150, 34, 196))
    img.paste(WHITE, (136, 150, 140, 196))
    img.paste(WHITE, (30, 192, 140, 196))
    img.paste(CYAN, (34, int(192 - 38 * level), 136, 192))
    img.paste(LGREY, (40, 196, 46, 202))
    img.paste(LGREY, (124, 196, 130, 202))
    draw_text(img, "RETRAITES", CX + 1, 172, INK, shadow=None)
    if t >= NOT_T:
        box(img, 208, 238)
        draw_text(img, "PLUTÔT QUE « RESTEZ", CX, 210, LGREY)
        draw_text(img, "MOINS LONGTEMPS DEDANS »", CX, 222, LGREY)
        if t >= NOT_T + 1.0:
            ImageDraw.Draw(img).line([(20, 232), (148, 210)], fill=STAMP_RED, width=2)


# 60 ans pour qui ? -----------------------------------------------------------
CH_T, BU_T = at('qui', "Quarante ans sur"), at('qui', "ce n'est pas")
PROP_T = at('prop', "60 ans")
impact(PROP_T, 3)
SFX.append((PROP_T + 0.1, 'sparkle', None))


@scene(sb('qui'), sb('fin'))
def s_qui(img, t):
    episode_tag(img, 3, t)
    if t < start('prop'):
        draw_text(img, "60 ANS POUR QUI ?", CX, TOP + 14, YELLOW, scale=2, shadow=PURPLE, maxw=170)
        if t >= CH_T:
            big_sprite(img, BRICKS, 44, 150, 3)
            big_sprite(img, WORKER, 44, 116, 3)
            draw_text(img, "40 ANS DE", 44, 176, WHITE)
            draw_text(img, "CHANTIER", 44, 188, ORANGE)
        if t >= BU_T:
            big_sprite(img, DESK, 124, 150, 3)
            big_sprite(img, SUIT, 116, 120, 3)
            draw_text(img, "40 ANS DE", 124, 176, WHITE)
            draw_text(img, "BUREAU", 124, 188, CYAN)
            draw_text(img, "≠", CX, 136, STAMP_RED, scale=3)
        return
    draw_text(img, "LA PROPOSITION", CX, TOP + 14, CYAN)
    if t >= PROP_T:
        p = pop(t, PROP_T)
        draw_text(img, "60 ANS", CX, int(TOP + 34 + (1 - p) * 10), GREEN, scale=3, shadow=PURPLE)
        burst(img, t, PROP_T, CX, TOP + 52)
    if t >= at('prop', "à taux plein"):
        draw_text(img, "À TAUX PLEIN", CX, 132, WHITE, scale=2)
    if t >= at('prop', "avec 40"):
        draw_text(img, "AVEC 40 ANNUITÉS", CX, 158, YELLOW, scale=2, maxw=170)


# verdict + appel ---------------------------------------------------------------
STAMP_T, FIX_T = at('fin', "Alors"), at('fin', "Ici")
SFX.append((STAMP_T, 'impact', None))
SFX.append((FIX_T + 0.35, 'sparkle', None))
DEBAT_T = at('fin', "Est-ce")
CTA_T = start('cta')
SFX.append((CTA_T, 'coin', None))


@scene(sb('fin'), EP.dur)
def s_fin(img, t):
    episode_tag(img, 3, t)
    verdict(img, t, STAMP_T, FIX_T)
    if DEBAT_T <= t < CTA_T:
        box(img, 190, 230)
        draw_text(img, "LE VRAI DÉBAT :", CX, 194, WHITE)
        draw_text(img, "*EST-CE QUE ÇA MARCHERAIT ?*", CX, 208, WHITE, maxw=MAXW)
    if t >= CTA_T:
        box(img, 186, 238)
        draw_text(img, "LEQUEL ON", CX, 190, WHITE, scale=2)
        draw_text(img, "DÉMONTE ?", CX, 210, YELLOW, scale=2, shadow=PURPLE)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 168)


if __name__ == '__main__':
    EP.write_text(os.path.join(HERE, 'texte_ep3.txt'))
    render(EP, 'ep3_retraite.mp4', MUSIC_SERIE)
