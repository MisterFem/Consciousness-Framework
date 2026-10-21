"""Photo de profil en pixel art, à partir du dessin d'origine (silhouette + « ? »).

    python3 make_avatar.py chemin/vers/dessin.jpg   # -> photo_profil_pixel.png (1024x1024)
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import BAYER, WHITE  # noqa: E402

N = 64
BOX = (200, 268, 1660, 1728)          # cadrage de la silhouette dans le dessin 1732x1732
SIL, RIM, OUTLINE = (8, 8, 20), (70, 60, 130), (150, 150, 170)
SKY = np.array([(29, 43, 83), (52, 60, 140), (78, 86, 190), (104, 112, 222)])
QMARK = [".GGGGGGGGG..",
         "GWWWWWWWWWG.",
         "GWWWGGGGWWWG",
         "GWWG....GWWG",
         ".GG.....GWWG",
         ".......GWWWG",
         "......GWWWG.",
         ".....GWWWG..",
         "....GWWWG...",
         "....GWWG....",
         "....GWWG....",
         "....GWWG....",
         ".....GG.....",
         "............",
         ".....GG.....",
         "....GWWG....",
         "....GWWG....",
         ".....GG....."]


def main(path):
    src = Image.open(path).convert('RGB')
    small = np.array(src.crop(BOX).resize((N, N), Image.LANCZOS)).astype(float)
    lum, sat = small.mean(2), small.max(2) - small.min(2)
    sil = (lum < 55) | (sat < 45)      # silhouette (le « ? » d'origine est redessiné)
    out = np.zeros((N, N, 3), np.uint8)
    for y in range(N):
        for x in range(N):
            if sil[y, x]:
                edge = any(0 <= y + dy < N and 0 <= x + dx < N and not sil[y + dy, x + dx]
                           for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                out[y, x] = RIM if edge else SIL
            else:
                v = (small[y, x, 2] - 120) / 120 * (len(SKY) - 1) + 0.6
                out[y, x] = SKY[int(np.clip(np.floor(v + BAYER[y % 4, x % 4] - 0.5), 0, len(SKY) - 1))]
    for r, row in enumerate(QMARK):
        for c, ch in enumerate(row):
            if ch != '.':
                out[14 + r, 17 + c] = WHITE if ch == 'W' else OUTLINE
    img = Image.fromarray(out)
    px = img.load()
    rng = np.random.RandomState(7)
    for _ in range(45):
        x, y = rng.randint(1, N - 1), rng.randint(1, N - 1)
        if any(sil[y + dy, x + dx] for dy, dx in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        if rng.rand() < 0.3:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px[x + dx, y + dy] = (170, 180, 255)
            px[x, y] = WHITE
        else:
            px[x, y] = (200, 205, 255)
    img.resize((N * 16, N * 16), Image.NEAREST).save(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo_profil_pixel.png'))


if __name__ == '__main__':
    main(sys.argv[1])
