"""Assemble la piste voix de chaque épisode : narrateur (Hugo) + le Sceptique.

Le narrateur est enregistré d'un bloc (audio/epN_narrateur.mp3), le Sceptique
réplique par réplique (audio/epN_<id>.mp3). On découpe le narrateur aux pauses
repérées (CUTS), on intercale les répliques dans l'ordre du texte, on aligne
les volumes et on écrit audio/epN_voix.wav. Les temps de chaque phrase dans
cette piste sont imprimés au format MEASURED, à recopier dans epN_*.py.

    python3 build_voices.py
"""
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
PAUSE = 0.35

# phrases du narrateur : (id, début, fin) dans audio/epN_narrateur.mp3
CUTS = {
    1: [('intro', 0.00, 8.76), ('esc', 9.36, 13.11), ('panne', 13.46, 17.24),
        ('prop', 17.88, 27.79), ('oui', 28.24, 32.33), ('autre', 32.80, 40.75),
        ('verre', 41.16, 48.21), ('fin', 48.45, 54.91)],
    2: [('intro', 0.00, 6.83), ('pas', 7.30, 12.60), ('buffett', 13.02, 22.57),
        ('mes', 22.99, 29.89), ('mamie', 30.49, 35.08), ('her', 35.51, 44.04),
        ('pas12', 44.43, 47.59), ('univ', 48.04, 60.93), ('disc', 61.37, 66.20),
        ('fin', 66.63, 74.45)],
    3: [('intro', 0.00, 3.25), ('macron', 3.72, 16.13), ('coffre', 16.66, 24.52),
        ('lev1', 24.79, 30.12), ('lev2', 30.52, 34.33), ('lev3', 34.48, 40.10),
        ('bain', 40.24, 46.45), ('qui', 46.98, 51.60), ('prop', 52.13, 56.32),
        ('fin', 56.75, 66.79), ('cta', 67.24, 69.80)],
}
# ordre complet du texte, répliques du Sceptique comprises
ORDER = {
    1: ['hook', 'intro', 'esc', 'panne', 'prop', 'obj', 'oui', 'autre', 'verre', 'fin'],
    2: ['hook', 'intro', 'pas', 'buffett', 'mes', 'mamie', 'her', 'pas12', 'obj', 'univ', 'disc', 'fin'],
    3: ['hook', 'intro', 'macron', 'coffre', 'lev1', 'lev2', 'lev3', 'bain', 'qui', 'prop', 'fin', 'cta'],
}


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768


def trim(x, thr=0.02):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a, b = max(0, idx[0] - int(0.03 * SR)), min(len(x), idx[-1] + int(0.08 * SR))
    return x[a:b]


def rms(x):
    loud = x[np.abs(x) > 0.02]
    return np.sqrt((loud ** 2).mean()) if len(loud) else 1.0


def build(ep):
    nar = load(os.path.join(HERE, 'audio', f'ep{ep}_narrateur.mp3'))
    pieces = {pid: nar[int(a * SR):int(b * SR)] for pid, a, b in CUTS[ep]}
    target = rms(nar)
    for pid in ORDER[ep]:
        if pid not in pieces:
            sc = trim(load(os.path.join(HERE, 'audio', f'ep{ep}_{pid}.mp3')))
            pieces[pid] = sc * (target / rms(sc))
    out, measured, t = [], {}, 0.0
    for pid in ORDER[ep]:
        p = pieces[pid]
        measured[pid] = (round(t, 2), round(t + len(p) / SR, 2))
        out += [p, np.zeros(int(PAUSE * SR))]
        t += len(p) / SR + PAUSE
    mix = np.concatenate(out)
    mix = np.clip(mix / max(1e-9, np.abs(mix).max()) * 0.95, -1, 1)
    path = os.path.join(HERE, 'audio', f'ep{ep}_voix.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return measured


if __name__ == '__main__':
    for ep in (int(a) for a in sys.argv[1:]) if len(sys.argv) > 1 else CUTS:
        m = build(ep)
        print(f"# épisode {ep}\nMEASURED = {{")
        items = [f"'{k}': {v}" for k, v in m.items()]
        for i in range(0, len(items), 4):
            print("    " + ", ".join(items[i:i + 4]) + ",")
        print("}")
