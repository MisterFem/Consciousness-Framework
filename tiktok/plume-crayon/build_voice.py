"""Assemble la voix à 3 personnages : audio/narrateur.mp3 (N1..N12), audio/plume.mp3 (P1, P2),
audio/crayon.mp3 (C1, C2). Chaque fichier est découpé aux pauses (programmation dynamique sur
la longueur des répliques), les répliques sont intercalées dans l'ordre de script.txt, volumes
alignés. Écrit audio/narration.wav et measured.json (temps de chaque réplique)."""
import json
import os
import re
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
BLOCKS = [ln.split('|', 1) for ln in open(os.path.join(HERE, 'script.txt'), encoding='utf-8').read().strip().split('\n')]
TXT = dict(BLOCKS)
IDS = [b[0] for b in BLOCKS]
FILES = {'N': 'narrateur.mp3', 'P': 'plume.mp3', 'C': 'crayon.mp3'}


def load(name):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'audio', name), '-f', 's16le',
                          '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768


def silences(name):
    err = subprocess.run(['ffmpeg', '-i', os.path.join(HERE, 'audio', name), '-af',
                          'silencedetect=noise=-35dB:d=0.25', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    return list(zip(st, en))


def split(name, ids):
    x = load(name)
    total = len(x) / SR
    sil = silences(name)
    # début / fin de parole
    t0 = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
    t1 = sil[-1][0] if sil and sil[-1][1] >= total - 0.05 else total
    cands = [(a, b) for a, b in sil if t0 < a and b < t1]
    k = len(ids)
    if k == 1:
        return x, {ids[0]: (t0, t1)}
    lens = np.array([len(TXT[i]) for i in ids], float)
    exp = lens / lens.sum() * (t1 - t0)
    m = len(cands)
    assert m >= k - 1, f'{name} : pas assez de pauses ({m}) pour {k} répliques'
    INF = 1e18
    # dp[j][c] = coût min en coupant la j-ième frontière à la pause c
    pos = [((a + b) / 2, b - a) for a, b in cands]
    dp = [[INF] * m for _ in range(k - 1)]
    bk = [[-1] * m for _ in range(k - 1)]
    for c in range(m):
        dp[0][c] = (pos[c][0] - t0 - exp[0]) ** 2 - 2 * pos[c][1]
    for j in range(1, k - 1):
        for c in range(m):
            for pc in range(c):
                v = dp[j - 1][pc] + (pos[c][0] - pos[pc][0] - exp[j]) ** 2 - 2 * pos[c][1]
                if v < dp[j][c]:
                    dp[j][c], bk[j][c] = v, pc
    best, bc = INF, -1
    for c in range(m):
        v = dp[k - 2][c] + (t1 - pos[c][0] - exp[k - 1]) ** 2
        if v < best:
            best, bc = v, c
    cuts = []
    for j in range(k - 2, -1, -1):
        cuts.append(bc)
        bc = bk[j][bc]
    cuts = cuts[::-1]
    seg, prev = {}, t0
    for i, c in enumerate(cuts):
        a, b = cands[c]
        seg[ids[i]] = (prev, a + 0.05)
        prev = b - 0.05
    seg[ids[-1]] = (prev, t1)
    return x, seg


def rms(x):
    loud = x[np.abs(x) > 0.02]
    return np.sqrt((loud ** 2).mean()) if len(loud) else 1.0


pieces, ref = {}, None
for who, f in FILES.items():
    ids = [i for i in IDS if i[0] == who]
    x, seg = split(f, ids)
    if ref is None:
        ref = rms(x)
    x = x * (ref / rms(x))
    for pid, (a, b) in seg.items():
        pieces[pid] = x[int(a * SR):int(b * SR)]
        print(f'{pid}: {b - a:5.2f}s  {TXT[pid][:50]}')
out, t, meas = [np.zeros(int(0.15 * SR))], 0.15, {}
for i, pid in enumerate(IDS):
    p = pieces[pid]
    meas[pid] = (round(t, 2), round(t + len(p) / SR, 2))
    nxt = IDS[i + 1] if i + 1 < len(IDS) else 'N'
    gap = 0.55 if (pid[0] != 'N' or nxt[0] != 'N' or pid == 'N1') else 0.45
    out += [p, np.zeros(int(gap * SR))]
    t += len(p) / SR + gap
mix = np.concatenate(out)
mix = np.clip(mix / np.abs(mix).max() * 0.95, -1, 1)
with wave.open(os.path.join(HERE, 'audio', 'narration.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
json.dump(meas, open(os.path.join(HERE, 'measured.json'), 'w'), indent=1)
print('durée totale', round(t, 1), 's ->', 'audio/narration.wav + measured.json')
