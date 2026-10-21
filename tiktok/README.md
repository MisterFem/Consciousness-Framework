# Vidéos TikTok pixel art

Vidéos verticales 1080x1920 générées entièrement en Python (Pillow + numpy +
ffmpeg) : images, musique chiptune, bruitages, et voix off ElevenLabs calée
dessus. Rendu interne 180x320, agrandi x6.

| Dossier | Vidéo | Script |
|---|---|---|
| `52-cartes/` | 52 ! mélanges d'un paquet de cartes (autonome, avant le moteur commun) | `make_video.py` |
| `anniversaires/` | Paradoxe des anniversaires | `make_video.py` |
| `feuille-lune/` | 42 plis pour atteindre la Lune (version courte, boucle) | `make_video.py` |
| `lfi-programme/` | Première version du programme LFI (remplacée par la série) | `make_video.py` |
| `utopiste/` | Série « Utopiste ? » en 3 épisodes, deux voix | `ep1_salaire.py`, `ep2_qui_paie.py`, `ep3_retraite.py` |

`pixel_engine.py` est le moteur commun : police bitmap (accents, €, ✓, «»…),
textes machine à écrire, fond étoilé (ou fond personnalisé via
`set_backdrop`), transitions, tremblements, musique, bruitages, calage sur la
voix (`Narration`), encodage.

## Fabriquer une vidéo

```bash
python3 make_video.py                 # rend la vidéo .mp4
python3 make_video.py preview 2 15.5  # images PNG de contrôle à 2 s et 15,5 s
```

Chaque script déclare `LINES` (les phrases de la voix off, avec un id), des
pauses à insérer (`SCENE_STARTS`, `INNER_GAPS`) et des scènes `@scene(t0, t1)`
qui dessinent l'image au temps `t`. Les temps se calent sur les phrases :
`N.start('id')`, `N.stop('id')`, ou `at('id', "mot")` pour un mot précis.

## Workflow avec la voix

1. Écrire `LINES`, rendre la vidéo avec les durées estimées (`MEASURED = None`)
   et produire le texte à enregistrer.
2. Enregistrer la voix sur ElevenLabs (narrateur : Hugo, « Serious and
   Professional »). Aucun silence au début.
3. Repérer les phrases dans le mp3 grâce aux silences :
   `ffmpeg -i voix.mp3 -af silencedetect=noise=-35dB:d=0.12 -f null -`
   puis associer chaque phrase à un segment (le débit d'Hugo est d'environ
   16 à 22 caractères/s, pour vérifier que l'association est cohérente).
4. Recopier les temps dans `MEASURED`, placer le mp3 dans `audio/`, relancer.

Série « Utopiste ? » : le Sceptique a une autre voix, enregistrée réplique par
réplique. `utopiste/build_voices.py` découpe le narrateur (`CUTS`),
intercale les répliques, aligne les volumes, écrit `audio/epN_voix.wav` et
imprime les `MEASURED`.

## Règles tirées des statistiques TikTok

- Vidéo 1 (cartes) : 88 vues, environ 75 % de départs avant 3 s. La première
  image était presque vide.
- Vidéo 2 (anniversaires) : 254 vues, ~42 % encore là à 3 s, 7,9 % de likes,
  0 commentaire (l'appel à commenter arrivait à 65 s).

Donc :
- **Première image = tout le message**, en gros, déjà en mouvement. Pas
  d'animation d'entrée, voix qui démarre à 0:00.
- **Demander un commentaire dans les 5 premières secondes** (pari, désaccord,
  question), pas seulement à la fin.
- **Court** : 30 à 45 s pour une anecdote ; une série plutôt qu'une longue vidéo.
- **Une question plutôt qu'une affirmation** dans l'accroche, réponse au sommet.
- **Fin qui boucle** sur l'image de départ (`loop=True`).
- **Zones sûres** : rien au-dessus de y=48 (barre de recherche), rien sous
  y≈245 (description), rien à droite de x≈150 entre y 120 et 245 (boutons),
  et garder 16 px sur les côtés (rognés sur les écrans allongés).
- Publier à la même heure pour pouvoir comparer, changer une chose à la fois.

## Vérification des faits

Tous les chiffres et citations sont à vérifier avant publication. Les vidéos
politiques n'utilisent que des citations réelles avec leur source à l'écran,
jamais de voix imitant une personne réelle.
