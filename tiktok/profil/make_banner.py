"""Bannière YouTube (2560x1440) dans l'esprit du coucher de soleil des « Dernières fois ».

Dessinée en 640x360 puis agrandie x4. Le texte reste dans la zone visible sur
tous les écrans (1546x423 au centre, soit 386x106 en pixels internes).

    python3 make_banner.py   # -> banniere_youtube.png
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pixel_engine import draw_text, BAYER  # noqa: E402

W, H, S = 640, 360, 4
HERE = os.path.dirname(os.path.abspath(__file__))
yy, xx = np.mgrid[0:H, 0:W]
bay = BAYER[yy % 4, xx % 4]

stops = [(0, (30, 20, 70)), (0.32, (120, 50, 120)), (0.5, (230, 100, 120)), (0.62, (255, 170, 110)),
         (0.7, (255, 225, 160)), (1, (255, 225, 160))]
pos = np.array([p for p, _ in stops]); cols = np.array([c for _, c in stops], float)
q = np.clip(np.floor(yy / (H - 1) * 14 + bay) / 14, 0, 1)
sky = np.stack([np.interp(q, pos, cols[:, k]) for k in range(3)], -1).astype(np.uint8)
img = Image.fromarray(sky, 'RGB')
d = ImageDraw.Draw(img)

r = random.Random(5)
for _ in range(140):                       # étoiles dans le haut du ciel
    x, y = r.randrange(W), r.randrange(0, 110)
    c = (255, 240, 230) if r.random() < 0.7 else (200, 190, 255)
    img.putpixel((x, y), c)
    if r.random() < 0.12:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            img.putpixel((x + dx, y + dy), (170, 150, 220))

cx, cy = W // 2, 282                       # soleil avec halo tramé et bandes
for rad, col in ((92, (255, 200, 140)), (74, (255, 225, 170)), (60, (255, 240, 200)), (50, (255, 250, 225))):
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
for k, y in enumerate(range(cy + 6, cy + 50, 7)):
    d.rectangle([cx - 60, y, cx + 60, y + 1 + k // 2], fill=(255, 190, 130))

for k, (col, base, amp, f) in enumerate((((170, 80, 120), 250, 22, 0.011), ((120, 50, 100), 275, 18, 0.017),
                                         ((70, 30, 80), 305, 14, 0.023), ((35, 18, 50), 335, 10, 0.031))):
    pts = [(0, H)] + [(x, base + math.sin(x * f + k * 1.7) * amp + math.sin(x * f * 2.3) * amp * 0.3)
                      for x in range(0, W + 4, 4)] + [(W, H)]
    d.polygon(pts, fill=col)

for k in range(5):                         # oiseaux au loin
    bx, by = 470 + k * 22, 100 + (k % 2) * 8
    d.line([bx - 4, by - 2, bx, by, bx + 4, by - 2], fill=(60, 30, 70))

# silhouette assise sur la dernière colline, qui regarde le soleil
sx, sy = 470, 322
d.ellipse([sx - 5, sy - 26, sx + 5, sy - 16], fill=(20, 10, 30))
d.rounded_rectangle([sx - 6, sy - 16, sx + 6, sy], radius=3, fill=(20, 10, 30))
d.line([sx, sy, sx - 12, sy + 2], fill=(20, 10, 30), width=4)

# poussières lumineuses
for _ in range(60):
    x, y = r.randrange(160, 480), r.randrange(150, 300)
    if r.random() < 0.5:
        img.putpixel((x, y), (255, 245, 210))

# vignette douce
v = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
a = np.clip((v - 0.8) * 1.2 + bay * 0.1, 0, 0.45)
img = Image.composite(Image.new('RGB', (W, H), (10, 5, 20)), img, Image.fromarray((a * 255).astype(np.uint8)))

# texte dans la zone sûre (centre, 386x106)
draw_text(img, "TIKETI", W // 2, 140, (255, 244, 225), scale=4, maxw=380, shadow=(80, 30, 70))

out = os.path.join(HERE, 'banniere_youtube.png')
img.resize((W * S, H * S), Image.NEAREST).save(out)
prev = img.copy(); dp = ImageDraw.Draw(prev)
dp.rectangle([W // 2 - 193, H // 2 - 53, W // 2 + 193, H // 2 + 53], outline=(0, 255, 0))
prev.resize((W * 2, H * 2), Image.NEAREST).save('/tmp/claude-0/-home-user-Consciousness-Framework/7b8feb02-21fe-5860-ab20-a1c173880623/scratchpad/banner_prev.png')
print(out)
