"""Moteur « DA fine » : rendu 360x640 (agrandi x3), dégradés tramés, calque de
texte posé après la caméra, zooms, transitions « whip », vignette, grain.

Une vidéo déclare ses paragraphes (Story), ses scènes (une fonction par
paragraphe) et sa caméra, puis appelle render(). Police, bruitages et
narration viennent de pixel_engine.
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_engine as pe  # noqa: E402
from pixel_engine import SFX, draw_text, layout, clamp, ease_out_back, ease_io  # noqa: E402,F401

W, H, S, FPS, SR = 360, 640, 3, 30, 44100
CX = W // 2
TOP = 96            # sous la barre de recherche TikTok
SAFE_B = 480        # au-dessus de la description

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:H, 0:W]
BAY = BAYER[YY % 4, XX % 4]
_cache = {}


# ---------------------------------------------------------------- narration
class Story:
    def __init__(self, ids, text_path, measured=None, rate=16.5, pause=0.45):
        self.ids = ids
        self.txt = dict(zip(ids, open(text_path).read().strip().split('\n\n')))
        if measured is None:
            measured, t = {}, 0.05
            for pid in ids:
                d = len(self.txt[pid]) / rate
                measured[pid] = (t, t + d)
                t += d + pause
        self.ph = measured
        self.end = measured[ids[-1]][1] + 0.1

    def at(self, pid, words):
        a, b = self.ph[pid]
        return a + (b - a) * self.txt[pid].index(words) / len(self.txt[pid])

    def start(self, pid):
        return self.ph[pid][0]

    def bounds(self):
        return [(self.ph[self.ids[i - 1]][1] + self.ph[self.ids[i]][0]) / 2 for i in range(1, len(self.ids))]

    def para(self, t):
        cur = self.ids[0]
        for b, pid in zip(self.bounds(), self.ids[1:]):
            if t >= b:
                cur = pid
        return cur


# ---------------------------------------------------------------- dessin
def gradient(stops, key, steps=8):
    """Dégradé vertical tramé (ordered dithering), mis en cache."""
    if key not in _cache:
        ys = YY / (H - 1)
        pos = np.array([p for p, _ in stops])
        cols = np.array([c for _, c in stops], float)
        q = np.clip(np.floor(ys * steps + BAY) / steps, 0, 1)
        out = np.zeros((H, W, 3))
        for k in range(3):
            out[..., k] = np.interp(q, pos, cols[:, k])
        _cache[key] = Image.fromarray(out.astype(np.uint8), 'RGB')
    return _cache[key].copy()


def mix(a, b, u):
    return tuple(int(a[k] + (b[k] - a[k]) * u) for k in range(3))


def ell(d, cx, cy, rx, ry, fill, outline=None, width=1):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=width)


UI = {'layer': None}


def text(img, s, y, col=(255, 241, 232), scale=3, cx=CX, maxw=330, shadow=(20, 10, 30), world=False, **kw):
    target = img if world or UI['layer'] is None else UI['layer']
    draw_text(target, s, int(cx), int(y), col, scale=scale, maxw=maxw, shadow=shadow, **kw)


def pop_word(img, s, t, t0, y, col, scale=4, cx=CX, maxw=340, shadow=(30, 10, 40)):
    if t < t0:
        return
    p = ease_out_back((t - t0) / 0.28)
    sc = scale + 1 if p > 1.02 else scale
    text(img, s, y + int((1 - min(p, 1)) * 18), col, scale=sc, cx=cx, maxw=maxw, shadow=shadow)


def fade_word(img, s, t, t0, y, col, scale=3, cx=CX, maxw=330, shadow=(20, 10, 30), dur=0.6):
    """Texte qui apparaît en fondu (pour les moments calmes)."""
    if t < t0:
        return
    a = clamp((t - t0) / dur)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_text(layer, s, int(cx), int(y), col, scale=scale, maxw=maxw, shadow=shadow)
    if a < 1:
        layer.putalpha(Image.eval(layer.getchannel('A'), lambda v: int(v * a)))
    target = UI['layer'] if UI['layer'] is not None else img
    target.alpha_composite(layer) if target.mode == 'RGBA' else target.paste(layer, (0, 0), layer)


def motes(img, t, n=40, col=(255, 230, 180), seed=1, area=(0, 0, W, H)):
    """Poussières dans la lumière."""
    import random
    r = random.Random(seed)
    px = img.load()
    x0, y0, x1, y1 = area
    for _ in range(n):
        bx, by, sp, ph = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(4, 12), r.uniform(0, 6.28)
        x = int(bx + math.sin(t * 0.7 + ph) * 10)
        y = int((by - t * sp) - y0) % (y1 - y0) + y0
        if 0 <= x < W and 0 <= y < H and (int(t * 3) + _) % 4:
            px[x, y] = col


def camera(img, t, z0, z1, cx, cy, a, b):
    z = z0 + (z1 - z0) * ease_io((t - a) / max(0.5, b - a))
    if abs(z - 1) < 0.005:
        return img
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.NEAREST, box=(x0, y0, x0 + w, y0 + h))


def _vignette(strength=0.55):
    r = np.sqrt(((XX - CX) / CX) ** 2 + ((YY - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.7) * 1.4 + BAY * 0.15, 0, strength)
    return Image.fromarray((a * 255).astype(np.uint8), 'L')


VIGNETTE = _vignette(0.42)
BLACK = Image.new('RGB', (W, H), (0, 0, 0))


def grain(img, t, amount=4):
    # grain renouvelé 6 fois par seconde seulement : garde l'effet pellicule sans exploser la taille du fichier
    rng = np.random.default_rng(int(t * 6))
    a = np.asarray(img).astype(np.int16)
    n = rng.integers(-amount, amount + 1, size=(H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8), 'RGB')


def compose(story, scenes, cameras, t, dur, whip=True, film=False, fade_out=True):
    pid = story.para(t)
    img = Image.new('RGB', (W, H))
    UI['layer'] = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    scenes[pid](img, t)
    a, b = story.ph[pid]
    img = camera(img, t, *cameras.get(pid, (1, 1, CX, H / 2)), a, b)
    img.paste(UI['layer'], (0, 0), UI['layer'])
    for bd in story.bounds():
        d = t - bd
        if whip and -0.12 <= d <= 0.12:
            p = 1 - abs(d) / 0.12
            shift = int(p * 90) * (1 if d < 0 else -1)
            smear = img.copy()
            for k in range(1, 5):
                smear = Image.blend(smear, img.transform(img.size, Image.AFFINE, (1, 0, shift * k / 4, 0, 1, 0)), 0.4)
            img = smear
        elif not whip and -0.35 <= d <= 0.35:
            img = Image.blend(img, BLACK, 0.85 * (1 - abs(d) / 0.35))
    img.paste(BLACK, (0, 0), VIGNETTE)
    if film:
        img = grain(img, t)
    if fade_out and t > dur - 0.6:
        img = Image.blend(img, BLACK, clamp((t - (dur - 0.6)) / 0.6))
    return img


# ---------------------------------------------------------------- rendu
def render(out, dur, frame_fn, voice_path, ph, end, music_gain=0.0, lufs=-16):
    """Voix + bruitages (SFX) ; pas de musique. `python3 x.py preview 2 15` -> PNG."""
    here = os.path.dirname(os.path.abspath(out))
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            frame_fn(float(ts)).resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(here, f'_preview_{ts}.png'))
        return
    n = int(dur * SR)
    voice = pe.Narration(voice_path, ph, [], end).load(n)
    sfx = pe.make_sfx(n, np.random.RandomState(1))
    m = sfx * 0.5 + voice * 1.9
    m /= max(1e-9, np.abs(m).max()) / 0.89
    wav = os.path.join(here, '_audio.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((m * 32767).astype(np.int16).tobytes())
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W * S}x{H * S}',
           '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
           '-pix_fmt', 'yuv420p', '-tune', 'grain', '-af', f'loudnorm=I={lufs}:TP=-1.5:LRA=11', '-ar', '44100', '-c:a', 'aac',
           '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(dur * FPS)):
        proc.stdin.write(frame_fn(f / FPS).resize((W * S, H * S), Image.NEAREST).tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print('->', out)
