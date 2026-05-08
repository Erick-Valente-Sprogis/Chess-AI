import array
import math
import pygame


def _gen_sine(freq, ms, vol=0.3, decay=20.0, sample_rate=44100):
    n      = int(sample_rate * ms / 1000)
    attack = int(sample_rate * 0.005)
    buf    = array.array('h', [0] * n)
    for i in range(n):
        t      = i / sample_rate
        env    = math.exp(-decay * t) * min(1.0, i / max(1, attack))
        buf[i] = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
    return buf


def make_sounds():
    sr  = 44100
    gap = array.array('h', [0] * int(sr * 0.055))
    return {
        'move':     pygame.mixer.Sound(buffer=_gen_sine(800,  50, vol=0.30, decay=28)),
        'capture':  pygame.mixer.Sound(buffer=_gen_sine(350,  80, vol=0.50, decay=18)),
        'check':    pygame.mixer.Sound(buffer=_gen_sine(1047, 120, vol=0.40, decay=12)),
        'game_end': pygame.mixer.Sound(
            buffer=_gen_sine(523, 130, vol=0.35, decay=10) + gap +
                   _gen_sine(415, 130, vol=0.35, decay=10) + gap +
                   _gen_sine(311, 220, vol=0.35, decay=7)
        ),
    }
