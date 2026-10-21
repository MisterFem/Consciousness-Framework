"""Utopiste ? — Épisode 1/3 : ton salaire.

    python3 ep1_salaire.py                 # produit ep1_salaire.mp4
    python3 ep1_salaire.py preview 2 15    # images de contrôle
"""
from serie import *  # noqa: F403

LINES = [
    ('hook', "C'est bien beau… mais c'est utopiste."),
    ('intro', "C'est ce qu'on entend sur le programme de LFI. Alors on vérifie, en trois épisodes. "
              "Épisode un : ton salaire. Et si t'es pas d'accord, dis-le en commentaire."),
    ('esc', "Imagine un escalator. Ton loyer monte. Tes courses montent. Ton électricité monte."),
    ('panne', "Et ton salaire, lui, prend l'escalier d'à côté… qui est en panne."),
    ('prop', "LFI propose d'augmenter le SMIC, et d'indexer les salaires sur l'inflation : si les "
             "prix montent, ton salaire suit. Et de bloquer les prix de certains produits essentiels."),
    ('obj', "« Oui, mais ça coûtera plus cher aux entreprises ! »"),
    ('oui', "Oui. Et c'est assumé : l'effort ne doit pas reposer que sur le salarié."),
    ('autre', "L'autre option, c'est de baisser les cotisations, en disant que les entreprises "
              "pourront augmenter les salaires. Sauf que « pourront », ce n'est pas « devront »."),
    ('verre', "C'est la différence entre donner de l'eau à quelqu'un en espérant qu'il remplisse ton "
              "verre… et remplir directement ton verre."),
    ('fin', "Alors, utopiste ? Le mécanisme existe. La vraie question, c'est : qui paie ? "
            "Réponse dans l'épisode deux."),
]
# temps des phrases dans audio/ep1_voix.wav (généré par build_voices.py)
MEASURED = {
    'hook': (0.0, 3.01), 'intro': (3.36, 12.12), 'esc': (12.47, 16.22), 'panne': (16.57, 20.35),
    'prop': (20.7, 30.61), 'obj': (30.96, 33.98), 'oui': (34.33, 38.42), 'autre': (38.77, 46.72),
    'verre': (47.07, 54.12), 'fin': (54.47, 60.9),
}
EP = Episode(LINES, scene_starts={'intro': 0.2, 'esc': 0.6, 'prop': 0.8, 'obj': 0.8, 'verre': 0.6,
                                  'fin': 0.8},
             inner_gaps={'panne': 0.3, 'oui': 0.3, 'autre': 0.4},
             measured=MEASURED, audio=os.path.join(HERE, 'audio', 'ep1_voix.wav'))
sb, at, start, stop = EP.sb, EP.at, EP.start, EP.stop

# ---------------------------------------------------------------- sprites
HOUSE = art(["....r....", "...rrr...", "..rrrrr..", ".rrrrrrr.", "rrrrrrrrr", ".wwwwwww.",
             ".wbwwwbw.", ".wwwddww.", ".wwwddww."],
            {'r': RED, 'w': WHITE, 'b': BLUE, 'd': BROWN})
CART = art(["c.........", "cccccccccc", ".cwwwwwwc.", ".cwwwwwwc.", "..cccccc..", "..c....c..",
            "..k....k.."], {'c': LGREY, 'w': ORANGE, 'k': INK})
BOLT = art(["...yy", "..yy.", ".yy..", "yyyyy", "..yy.", ".yy..", "yy..."], {'y': YELLOW})
WORKER = art(["..oo..", "..oo..", "..ss..", ".bbbb.", "sbbbbs", ".bbbb.", ".b..b.", ".k..k."],
             {'o': ORANGE, 's': PEACH, 'b': BLUE, 'k': INK})
PITCHER = art(["..wwww..", ".wcccww.", "wwcccw.w", ".wcccw.w", ".wcccww.", ".wcccw..", ".wwwww.."],
              {'w': WHITE, 'c': CYAN})


def glass(img, x, y, level, label=None):
    """Verre 12x16 rempli à `level` (0..1)."""
    img.paste(WHITE, (x, y, x + 1, y + 16))
    img.paste(WHITE, (x + 11, y, x + 12, y + 16))
    img.paste(WHITE, (x, y + 15, x + 12, y + 16))
    h = int(14 * clamp(level))
    if h:
        img.paste(CYAN, (x + 1, y + 15 - h, x + 11, y + 15))
    if label:
        draw_text(img, label, x + 6, y + 19, WHITE)


# ================================================================ SCÈNES
SFX.append((0.0, 'impact', None))
COM_T = at('intro', "Et si")
SFX.append((COM_T, 'coin', None))
EP1_T = at('intro', "Épisode un")
SFX.append((EP1_T, 'whoosh', None))


@scene(0.0, sb('esc'))
def s_hook(img, t):
    episode_tag(img, 1, t)
    if t < EP1_T:
        for k, line in enumerate(("« C'EST BIEN", "BEAU... MAIS", "C'EST")):
            draw_text(img, line, CX, TOP + 14 + k * 22, WHITE, scale=2, maxw=MAXW + 6)
        rubber_stamp(img, "UTOPISTE ? »", CX, TOP + 100, t, -1)
        big_sprite(img, SCEPTIC, 136, 196, 3)
        draw_text(img, "LE SCEPTIQUE", 136, 222, LGREY)
        draw_text(img, "LE PROGRAMME LFI, VÉRIFIÉ EN 3 ÉPISODES", 62, 186, CYAN, maxw=90)
    else:
        p = pop(t, EP1_T)
        draw_text(img, "ÉPISODE 1", CX, int(TOP + 24 + (1 - p) * 10), CYAN, scale=2)
        draw_text(img, "TON SALAIRE", CX, TOP + 48, YELLOW, scale=2, shadow=PURPLE, maxw=170)
        big_sprite(img, WORKER, CX, 150, 5)
    if t >= COM_T:
        box(img, 200, 238)
        draw_text(img, "PAS D'ACCORD ?", CX, 202, WHITE, scale=2, maxw=MAXW + 6)
        draw_text(img, "COMMENTE !", CX, 220, YELLOW, scale=2, shadow=PURPLE, maxw=MAXW + 6)
        arrow(img, 138 + abs(math.sin(t * 5)) * 5, 182)


# l'escalator ------------------------------------------------------------
ESC_ITEMS = [(at('esc', "Ton loyer"), HOUSE, "LOYER ↑"), (at('esc', "Tes courses"), CART, "COURSES ↑"),
             (at('esc', "Ton électricité"), BOLT, "ÉLECTRICITÉ ↑")]
for ti, _, _ in ESC_ITEMS:
    SFX.append((ti, 'place', 14))
PANNE_T = at('panne', "qui est en panne")
impact(PANNE_T, 2)
E0, E1 = (16, 206), (92, 106)  # bas et haut de l'escalator


def esc_point(u):
    return E0[0] + (E1[0] - E0[0]) * u, E0[1] + (E1[1] - E0[1]) * u


@scene(sb('esc'), sb('prop'))
def s_escalator(img, t):
    episode_tag(img, 1, t)
    d = ImageDraw.Draw(img)
    # escalator : rampe + marches qui défilent
    d.line([E0, E1], fill=LGREY, width=2)
    d.line([(E0[0], E0[1] - 14), (E1[0], E1[1] - 14)], fill=DGREY, width=1)
    for k in range(12):
        u = ((k / 12) + t * 0.15) % 1
        x, y = esc_point(u)
        d.line([(x, y - 1), (x + 6, y - 1)], fill=CYAN)
    draw_text(img, "LES PRIX", 30, 216, RED)
    for k, (ti, spr, lab) in enumerate(ESC_ITEMS):
        if t < ti:
            continue
        u = clamp(0.1 + (t - ti) * 0.25, 0, 0.78 - k * 0.22)
        x, y = esc_point(u)
        big_sprite(img, spr, x + 4, y - 12, 2)
        draw_text(img, lab, CX, TOP + 14 + k * 13, RED)
    # l'escalier en panne
    sx, sy = 108, 206
    for k in range(6):
        img.paste(DGREY, (sx + k * 8, sy - (k + 1) * 10, sx + 48, sy - k * 10))
        img.paste(LGREY, (sx + k * 8, sy - (k + 1) * 10, sx + 48, sy - (k + 1) * 10 + 1))
    if t >= start('panne'):
        big_sprite(img, WORKER, sx + 6, sy - 18, 2)
        draw_text(img, "TON SALAIRE", sx + 20, sy + 4, YELLOW)
    if t >= PANNE_T:
        p = pop(t, PANNE_T)
        img.paste(STAMP_RED, (sx + 6, int(118 - (1 - p) * 10), sx + 46, int(132 - (1 - p) * 10)))
        draw_text(img, "EN PANNE", sx + 26, int(119 - (1 - p) * 10), WHITE, shadow=None)


# la proposition ---------------------------------------------------------
M1 = [(at('prop', "d'augmenter le SMIC"), "*SMIC* AUGMENTÉ"),
      (at('prop', "et d'indexer"), "SALAIRES *INDEXÉS* SUR L'INFLATION"),
      (at('prop', "Et de bloquer"), "*PRIX BLOQUÉS* SUR L'ESSENTIEL")]
for ti, _ in M1:
    SFX.append((ti, 'place', 12))
SUIT_T = at('prop', "si les")


@scene(sb('prop'), sb('obj'))
def s_prop(img, t):
    episode_tag(img, 1, t)
    draw_text(img, "CE QUE PROPOSE LFI", CX, TOP + 14, CYAN, scale=1)
    checklist(img, t, M1, TOP + 34, dy=26)
    # « si les prix montent, ton salaire suit » : les deux montent ensemble
    if t >= SUIT_T:
        p = ease_io((t - SUIT_T) / 1.6)
        for k, (lab, col) in enumerate((("PRIX", RED), ("SALAIRE", GREEN))):
            x = 46 + k * 52
            h = int(10 + 36 * p)
            img.paste(col, (x, 224 - h, x + 24, 224))
            draw_text(img, lab, x + 12, 228, col)
            draw_text(img, "↑", x + 12, 224 - h - 14, col, scale=2)
        img.paste(LGREY, (30, 224, 136, 225))


# l'objection ------------------------------------------------------------
OUI_T = start('oui')
impact(OUI_T, 2)
POURRONT_T, DEVRONT_T = at('autre', "Sauf que"), at('autre', "ce n'est pas")
SFX.append((DEVRONT_T, 'coin', None))
S_OUI = EP.N.text("L'EFFORT NE DOIT PAS REPOSER *QUE SUR LE SALARIÉ*", 'oui', 206)
S_AUTRE = EP.N.text("BAISSER LES COTISATIONS EN ESPÉRANT QUE LES SALAIRES SUIVENT", 'autre', 206,
                    color=LGREY)


@scene(sb('obj'), sb('verre'))
def s_obj(img, t):
    episode_tag(img, 1, t)
    if t < OUI_T:
        sceptic(img, t, start('obj'), "ÇA COÛTERA PLUS CHER *AUX ENTREPRISES* !", y=170)
        return
    if t < start('autre'):
        rubber_stamp(img, "OUI.", CX, 100, t, OUI_T, col=GREEN, scale=3, angle=-4)
        draw_text(img, "ET C'EST ASSUMÉ", CX, 140, WHITE, scale=2, maxw=MAXW + 6)
        caption(img, t, S_OUI)
        return
    draw_text(img, "L'AUTRE OPTION", CX, TOP + 14, CYAN)
    if t >= POURRONT_T:
        draw_text(img, "POURRONT", CX, 96, LGREY, scale=3, maxw=170)
    if t >= DEVRONT_T:
        p = pop(t, DEVRONT_T)
        draw_text(img, "≠", CX, 132, STAMP_RED, scale=3)
        draw_text(img, "DEVRONT", CX, int(166 + (1 - p) * 8), YELLOW, scale=3, shadow=PURPLE, maxw=170)
    caption(img, t, S_AUTRE)


# le verre d'eau ---------------------------------------------------------
V2_T = at('verre', "et remplir")
SFX.append((V2_T + 0.8, 'sparkle', None))


@scene(sb('verre'), sb('fin'))
def s_verre(img, t):
    episode_tag(img, 1, t)
    lt = t - sb('verre')
    # 1) on donne la carafe à quelqu'un, en espérant
    y1 = TOP + 18
    draw_text(img, "ESPÉRER", 44, y1, LGREY, scale=2)
    big_sprite(img, PITCHER, 30, y1 + 44, 3)
    big_sprite(img, WORKER, 64, y1 + 44, 3)
    glass(img, 104, y1 + 34, 0.0, "TON VERRE")
    draw_text(img, "?", 110, y1 + 14, STAMP_RED, scale=2)
    draw_text(img, "COTISATIONS BAISSÉES", CX, y1 + 72, LGREY)
    # 2) on remplit directement
    if t >= V2_T:
        y2 = 150
        img.paste(GRID2, (20, y2 - 6, 148, y2 - 5))
        draw_text(img, "GARANTIR", 50, y2, GREEN, scale=2)
        p = clamp((t - V2_T) / 1.2)
        big_sprite(img, PITCHER, 84, y2 + 34, 3)
        if p < 1:
            img.paste(CYAN, (96, y2 + 34, 98, y2 + 50))
        glass(img, 104, y2 + 34, p, "TON VERRE")
        if p >= 1:
            draw_text(img, "✓", 134, y2 + 34, GREEN, scale=2)
        draw_text(img, "SMIC + INDEXATION", CX - 10, y2 + 70, GREEN)


# verdict ----------------------------------------------------------------
STAMP_T, FIX_T = at('fin', "Alors"), at('fin', "Le mécanisme")
SFX.append((STAMP_T, 'impact', None))
SFX.append((FIX_T + 0.35, 'sparkle', None))
NEXT_T = at('fin', "La vraie")


@scene(sb('fin'), EP.dur)
def s_fin(img, t):
    episode_tag(img, 1, t)
    verdict(img, t, STAMP_T, FIX_T)
    if t >= NEXT_T:
        p = pop(t, NEXT_T)
        box(img, 188, 238)
        draw_text(img, "ÉPISODE 2", CX, int(192 + (1 - p) * 6), CYAN, scale=1)
        draw_text(img, "QUI PAIE ?", CX, 206, YELLOW, scale=3, shadow=PURPLE, maxw=170)


if __name__ == '__main__':
    EP.write_text(os.path.join(HERE, 'texte_ep1.txt'))
    render(EP, 'ep1_salaire.mp4', MUSIC_SERIE)
