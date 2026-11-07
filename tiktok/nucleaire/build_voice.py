"""Assemble la voix : Hugo (audio/hugo.mp3) + les 2 répliques du Sceptique (audio/sceptique.mp3).

Découpe aux pauses repérées, intercale les répliques, aligne les volumes, écrit
audio/narration.wav et imprime les temps de chaque paragraphe (MEASURED).
"""
import os
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
PAUSE = 0.35
HUGO = [('flam', 0.0, 7.60), ('intro', 8.17, 16.63), ('plan', 17.13, 27.91), ('cout', 28.53, 39.08),
        ('uranium', 39.63, 48.89), ('dechets', 49.34, 60.35), ('reponse', 60.86, 71.83), ('rte', 72.39, 83.78),
        ('verdict', 84.36, 96.01), ('cta', 96.53, 100.05)]
SCEP = [('scep1', 0.0, 3.78), ('scep2', 4.31, 7.89)]
ORDER = ['flam', 'scep1', 'intro', 'plan', 'cout', 'uranium', 'dechets', 'scep2', 'reponse', 'rte', 'verdict', 'cta']


def load(name):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'audio', name), '-f', 's16le',
                          '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768


def rms(x):
    loud = x[np.abs(x) > 0.02]
    return np.sqrt((loud ** 2).mean()) if len(loud) else 1.0


hugo, scep = load('hugo.mp3'), load('sceptique.mp3')
scep = scep * (rms(hugo) / rms(scep))
pieces = {pid: hugo[int(a * SR):int(b * SR)] for pid, a, b in HUGO}
pieces.update({pid: scep[int(a * SR):int(b * SR)] for pid, a, b in SCEP})
out, t, meas = [], 0.0, {}
for pid in ORDER:
    p = pieces[pid]
    meas[pid] = (round(t, 2), round(t + len(p) / SR, 2))
    out += [p, np.zeros(int(PAUSE * SR))]
    t += len(p) / SR + PAUSE
mix = np.concatenate(out)
mix = np.clip(mix / np.abs(mix).max() * 0.95, -1, 1)
with wave.open(os.path.join(HERE, 'audio', 'narration.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(meas)
