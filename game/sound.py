"""
sound.py — Sistem suara prosedural (tanpa file audio eksternal).
Menggunakan pygame.mixer untuk men-generate dan memutar suara retro di Ursina.
"""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import array
import math
import random
import time

_RATE = 22050
_CHANNELS = 1  # mono

def _wave(freq: float, dur_ms: int, vol: float = 0.35, shape: str = 'sine') -> pygame.mixer.Sound:
    n = max(1, int(_RATE * dur_ms / 1000))
    fade = min(n // 4, int(_RATE * 0.015))
    buf = array.array('h', [0] * n)
    prev_v = 0.0
    for i in range(n):
        t = i / _RATE
        if shape == 'sine':
            v = math.sin(2 * math.pi * freq * t)
        elif shape == 'square':
            v = 0.6 if math.sin(2 * math.pi * freq * t) > 0 else -0.6
        elif shape == 'noise':
            raw_v = random.uniform(-1, 1)
            v = 0.5 * prev_v + 0.5 * raw_v
            prev_v = v
        else:
            v = math.sin(2 * math.pi * freq * t)
        env = (i / fade) if i < fade else ((n - i) / fade if i > n - fade else 1.0)
        buf[i] = int(min(32767, max(-32767, vol * 32767 * v * env)))
    return pygame.mixer.Sound(buffer=buf)

def _sweep(f0: float, f1: float, dur_ms: int, vol: float = 0.3) -> pygame.mixer.Sound:
    n = max(1, int(_RATE * dur_ms / 1000))
    fade = min(n // 4, int(_RATE * 0.015))
    buf = array.array('h', [0] * n)
    phase = 0.0
    for i in range(n):
        freq = f0 + (f1 - f0) * (i / n)
        phase += 2 * math.pi * freq / _RATE
        v = math.sin(phase)
        env = (i / fade) if i < fade else ((n - i) / fade if i > n - fade else 1.0)
        buf[i] = int(min(32767, max(-32767, vol * 32767 * v * env)))
    return pygame.mixer.Sound(buffer=buf)

def _chord(freqs: list, dur_ms: int, vol: float = 0.3) -> pygame.mixer.Sound:
    n = max(1, int(_RATE * dur_ms / 1000))
    fade = min(n // 4, int(_RATE * 0.02))
    buf = array.array('h', [0] * n)
    per = vol / max(1, len(freqs))
    for i in range(n):
        t = i / _RATE
        v = sum(math.sin(2 * math.pi * f * t) for f in freqs)
        env = (i / fade) if i < fade else ((n - i) / fade if i > n - fade else 1.0)
        buf[i] = int(min(32767, max(-32767, per * 32767 * v * env)))
    return pygame.mixer.Sound(buffer=buf)

SOUNDS: dict = {}
_enabled: bool = False

def init_sound() -> bool:
    global _enabled
    try:
        pygame.mixer.pre_init(_RATE, -16, _CHANNELS, 512)
        pygame.mixer.init()
        _enabled = True
        return True
    except Exception as e:
        print(f"[Sound] Mixer gagal: {e}")
        return False

def build_sounds():
    global SOUNDS, _enabled
    if not _enabled: return
    try:
        SOUNDS.update({
            'step_grass': _wave(190, 42, 0.10, 'noise'),
            'step_dirt':  _wave(140, 52, 0.13, 'noise'),
            'step_path':  _wave(360, 38, 0.11, 'noise'),
            'step_floor': _wave(480, 35, 0.09, 'noise'),
            'hoe':        _wave(105, 95, 0.36, 'square'),
            'water':      _sweep(720, 240, 170, 0.26),
            'plant':      _wave(440, 65, 0.20, 'sine'),
            'harvest':    _chord([523, 659, 784], 230, 0.30),
            'axe':        _wave(88, 115, 0.40, 'square'),
            'sword':      _sweep(800, 300, 100, 0.30),
            'gift':       _chord([440, 554, 659], 210, 0.26),
            'dialog':     _wave(860, 32, 0.11, 'sine'),
            'notif':      _chord([523, 784], 165, 0.20),
            'quest':      _chord([392, 494, 587, 784], 440, 0.36),
            'blocked':    _wave(175, 95, 0.16, 'square'),
            'menu_move':  _wave(630, 26, 0.09, 'sine'),
            'menu_select':_chord([440, 550], 85, 0.16),
            'buy':        _sweep(370, 590, 105, 0.26),
            'sell':       _chord([660, 880], 160, 0.26),
            'sleep':      _sweep(450, 215, 560, 0.26),
            'morning':    _chord([261, 329, 392, 523], 580, 0.30),
            'capture':    _sweep(275, 740, 330, 0.36),
            'heal':       _sweep(330, 560, 210, 0.20),
        })
    except Exception:
        _enabled = False

_cooldowns: dict = {}
_CD_DEFAULTS = {'step_grass': 320, 'step_dirt': 320, 'step_path': 320, 'step_floor': 320}

def play(name: str, volume: float = 1.0):
    if not _enabled or name not in SOUNDS: return
    now = time.time() * 1000
    cd = _CD_DEFAULTS.get(name, 0)
    if cd and now < _cooldowns.get(name, 0): return
    if cd: _cooldowns[name] = now + cd
    try:
        s = SOUNDS[name]
        s.set_volume(max(0.0, min(1.0, volume)))
        s.play()
    except Exception: pass

def get_step_sound(tile_name: str) -> str:
    if tile_name in ('grass',): return 'step_grass'
    elif tile_name in ('dirt', 'tilled_dry', 'tilled_wet'): return 'step_dirt'
    elif tile_name in ('path_stone',): return 'step_path'
    elif tile_name in ('floor_wood', 'cave_floor'): return 'step_floor'
    return 'step_grass'


# ─── AMBIENT BGM LOOPS PER SCENE ────────────────────────────────────────────
_AMBIENT_LOOPS: dict = {}
_current_ambient: tuple = (None, None)  # (channel, name)


# Helper functions for cozy mathematical music synthesis
def _midi_to_freq(midi: float) -> float:
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((midi - 69.0) / 12.0))

def _add_sine_note(mix: list, freq: float, start_sec: float, dur_sec: float, vol: float, shape: str = 'cozy', fade_in_sec: float = 0.15, fade_out_sec: float = 0.5):
    """Mixes a single note with custom shape and gentle envelope into the float buffer."""
    n = len(mix)
    start_idx = int(start_sec * _RATE)
    dur_samples = int(dur_sec * _RATE)
    
    if start_idx >= n:
        return
        
    end_idx = min(n, start_idx + dur_samples)
    actual_dur = end_idx - start_idx
    if actual_dur <= 0:
        return
        
    fade_in_samples = int(fade_in_sec * _RATE)
    fade_out_samples = int(fade_out_sec * _RATE)
    
    inv_fade_in = 1.0 / fade_in_samples if fade_in_samples > 0 else 1.0
    inv_fade_out = 1.0 / fade_out_samples if fade_out_samples > 0 else 1.0
    
    k = 2 * math.pi * freq / _RATE
    
    for i in range(actual_dur):
        idx = start_idx + i
        
        # Envelope calculation
        if i < fade_in_samples:
            env = i * inv_fade_in
        elif i > actual_dur - fade_out_samples:
            env = (actual_dur - i) * inv_fade_out
        else:
            env = 1.0
            
        # Shape calculation
        if shape == 'sine':
            v = math.sin(i * k)
        elif shape == 'triangle':
            phase_t = i * (freq / _RATE)
            v = 2.0 * abs(2.0 * (phase_t - math.floor(phase_t + 0.5))) - 1.0
        elif shape == 'cozy':
            # A rich blend of 75% sine and 25% triangle for a nostalgic chiptune EP sound
            v_sine = math.sin(i * k)
            phase_t = i * (freq / _RATE)
            v_tri = 2.0 * abs(2.0 * (phase_t - math.floor(phase_t + 0.5))) - 1.0
            v = 0.75 * v_sine + 0.25 * v_tri
        else:
            v = math.sin(i * k)
            
        mix[idx] += vol * v * env

def _add_sine_chord(mix: list, midi_notes: list, start_sec: float, dur_sec: float, vol: float, shape: str = 'cozy', fade_in_sec: float = 0.5, fade_out_sec: float = 0.5):
    """Mixes a chord of notes with custom shape and gentle envelope into the float buffer."""
    per_note_vol = vol / max(1, len(midi_notes))
    for note in midi_notes:
        _add_sine_note(mix, _midi_to_freq(note), start_sec, dur_sec, per_note_vol, shape, fade_in_sec, fade_out_sec)

def _ambient_loop(scene: str, dur_sec: float = 16.0) -> pygame.mixer.Sound:
    """Generate ambient loop khas per scene type. Stereo-ish via 2 channel."""
    n = int(_RATE * dur_sec)
    buf = array.array('h', [0] * n)
    mix = [0.0] * n
    
    if scene == 'outdoor':
        # Wind: low-freq sweep + soft noise
        prev_n = 0.0
        for i in range(n):
            t = i / _RATE
            wind = 0.14 * math.sin(2*math.pi*0.20*t) * math.sin(2*math.pi*0.13*t + 1.2)
            raw_n = 0.015 * random.uniform(-1, 1)
            # One-pole low-pass filter to smooth out high frequency crackle
            prev_n = 0.9 * prev_n + 0.1 * raw_n
            mix[i] = wind + prev_n
            
        # BGM progression (G -> C -> D -> G) - cozy major feel
        # Bar 1 (0-4s): G
        _add_sine_chord(mix, [43, 50, 55, 59], start_sec=0.0, dur_sec=4.0, vol=0.07, shape='cozy', fade_in_sec=0.8, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(83), start_sec=0.5, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        _add_sine_note(mix, _midi_to_freq(86), start_sec=2.0, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        
        # Bar 2 (4-8s): C
        _add_sine_chord(mix, [48, 55, 60, 64], start_sec=4.0, dur_sec=4.0, vol=0.07, shape='cozy', fade_in_sec=0.8, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(84), start_sec=4.5, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        _add_sine_note(mix, _midi_to_freq(88), start_sec=6.0, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        
        # Bar 3 (8-12s): D
        _add_sine_chord(mix, [50, 57, 62, 66], start_sec=8.0, dur_sec=4.0, vol=0.07, shape='cozy', fade_in_sec=0.8, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(81), start_sec=8.5, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        _add_sine_note(mix, _midi_to_freq(86), start_sec=10.0, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        
        # Bar 4 (12-16s): G
        _add_sine_chord(mix, [43, 50, 55, 59], start_sec=12.0, dur_sec=4.0, vol=0.07, shape='cozy', fade_in_sec=0.8, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(83), start_sec=12.5, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)
        _add_sine_note(mix, _midi_to_freq(79), start_sec=14.0, dur_sec=1.5, vol=0.035, shape='cozy', fade_in_sec=0.1, fade_out_sec=0.4)

    elif scene == 'forest':
        # Bird chirps + wind
        for i in range(n):
            t = i / _RATE
            wind = 0.08 * math.sin(2*math.pi*0.25*t)
            chirp = 0
            if random.random() < 0.00008:
                chirp = math.sin(2*math.pi*2800*t) * 0.12
            mix[i] = wind + chirp
            
        # BGM progression (Am9 -> Dm9) - ancient mysterious forest feel
        # Bar 1-2 (0-8s): Am9
        _add_sine_chord(mix, [45, 52, 59, 60, 67], start_sec=0.0, dur_sec=8.0, vol=0.05, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Chime 1 (E6 + E7 soft harmonic)
        _add_sine_note(mix, _midi_to_freq(88), start_sec=2.0, dur_sec=3.0, vol=0.02, shape='cozy', fade_in_sec=0.05, fade_out_sec=2.0)
        _add_sine_note(mix, _midi_to_freq(88) * 2.0, start_sec=2.0, dur_sec=2.0, vol=0.01, shape='sine', fade_in_sec=0.01, fade_out_sec=1.0)
        # Chime 2 (B6 + B7 soft harmonic)
        _add_sine_note(mix, _midi_to_freq(95), start_sec=5.5, dur_sec=3.0, vol=0.02, shape='cozy', fade_in_sec=0.05, fade_out_sec=2.0)
        _add_sine_note(mix, _midi_to_freq(95) * 2.0, start_sec=5.5, dur_sec=2.0, vol=0.01, shape='sine', fade_in_sec=0.01, fade_out_sec=1.0)
        
        # Bar 3-4 (8-16s): Dm9
        _add_sine_chord(mix, [38, 57, 64, 65, 72], start_sec=8.0, dur_sec=8.0, vol=0.05, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Chime 3 (C7 + C8 soft harmonic)
        _add_sine_note(mix, _midi_to_freq(96), start_sec=10.0, dur_sec=3.0, vol=0.02, shape='cozy', fade_in_sec=0.05, fade_out_sec=2.0)
        _add_sine_note(mix, _midi_to_freq(96) * 2.0, start_sec=10.0, dur_sec=2.0, vol=0.01, shape='sine', fade_in_sec=0.01, fade_out_sec=1.0)
        # Chime 4 (A6 + A7 soft harmonic)
        _add_sine_note(mix, _midi_to_freq(93), start_sec=13.5, dur_sec=3.0, vol=0.02, shape='cozy', fade_in_sec=0.05, fade_out_sec=2.0)
        _add_sine_note(mix, _midi_to_freq(93) * 2.0, start_sec=13.5, dur_sec=2.0, vol=0.01, shape='sine', fade_in_sec=0.01, fade_out_sec=1.0)

    elif scene == 'cave':
        # Drip + low rumble
        for i in range(n):
            t = i / _RATE
            rumble = 0.08 * math.sin(2*math.pi*55*t) * (0.5 + 0.5*math.sin(2*math.pi*0.1*t))
            drip = 0
            if random.random() < 0.00006:
                drip = math.sin(2*math.pi*1200*t) * 0.10
            mix[i] = rumble + drip
            
        # BGM drone (Deep low fifths, very calm)
        # Bar 1-2 (0-8s): E1, E2, B2
        _add_sine_chord(mix, [28, 40, 47], start_sec=0.0, dur_sec=8.0, vol=0.07, shape='sine', fade_in_sec=2.0, fade_out_sec=2.0)
        # Crystal droplets (gentle resonance)
        _add_sine_note(mix, _midi_to_freq(91), start_sec=3.0, dur_sec=2.5, vol=0.015, shape='cozy', fade_in_sec=0.02, fade_out_sec=1.5)
        _add_sine_note(mix, _midi_to_freq(91) * 3.0, start_sec=3.0, dur_sec=1.5, vol=0.005, shape='sine', fade_in_sec=0.01, fade_out_sec=0.8)
        
        # Bar 3-4 (8-16s): A1, A2, E3
        _add_sine_chord(mix, [33, 45, 52], start_sec=8.0, dur_sec=8.0, vol=0.07, shape='sine', fade_in_sec=2.0, fade_out_sec=2.0)
        _add_sine_note(mix, _midi_to_freq(95), start_sec=11.0, dur_sec=2.5, vol=0.015, shape='cozy', fade_in_sec=0.02, fade_out_sec=1.5)
        _add_sine_note(mix, _midi_to_freq(95) * 3.0, start_sec=11.0, dur_sec=1.5, vol=0.005, shape='sine', fade_in_sec=0.01, fade_out_sec=0.8)

    elif scene == 'indoor':
        # Cozy hum + fire crackle (softened with decay filter)
        crackle_decay = 0.0
        prev_crackle = 0.0
        for i in range(n):
            t = i / _RATE
            hum = 0.03 * math.sin(2*math.pi*120*t)
            if random.random() < 0.0003:
                crackle_decay = random.uniform(0.5, 1.0) * 0.025
            else:
                crackle_decay *= 0.96
            raw_crackle = crackle_decay * random.uniform(-1, 1)
            prev_crackle = 0.8 * prev_crackle + 0.2 * raw_crackle
            mix[i] = hum + prev_crackle
            
        # BGM progression (Cmaj9 -> Fmaj9) - warm fireplace feel
        # Bar 1-2 (0-8s): Cmaj9
        _add_sine_chord(mix, [48, 55, 59, 62, 64], start_sec=0.0, dur_sec=8.0, vol=0.08, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Slow sweet melody
        _add_sine_note(mix, _midi_to_freq(76), start_sec=1.0, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(79), start_sec=2.5, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(83), start_sec=5.0, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(81), start_sec=6.5, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        
        # Bar 3-4 (8-16s): Fmaj9
        _add_sine_chord(mix, [41, 48, 52, 55, 57], start_sec=8.0, dur_sec=8.0, vol=0.08, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Slow sweet melody response
        _add_sine_note(mix, _midi_to_freq(84), start_sec=9.0, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(81), start_sec=10.5, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(79), start_sec=13.0, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(76), start_sec=14.5, dur_sec=2.0, vol=0.03, shape='cozy', fade_in_sec=0.3, fade_out_sec=0.8)

    elif scene == 'water':
        # Lake lapping waves
        prev_ripple = 0.0
        for i in range(n):
            t = i / _RATE
            wave = 0.08 * math.sin(2*math.pi*0.4*t) * math.sin(2*math.pi*0.7*t)
            raw_ripple = 0.008 * random.uniform(-1, 1) * math.sin(2*math.pi*0.5*t)
            prev_ripple = 0.9 * prev_ripple + 0.1 * raw_ripple
            mix[i] = wave + prev_ripple
            
        # BGM progression (Fmaj9 -> G6) - floating liquid feel
        # Bar 1-2 (0-8s): Fmaj9
        _add_sine_chord(mix, [41, 48, 55, 57, 64], start_sec=0.0, dur_sec=8.0, vol=0.07, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Rippling waterfall droplets: E6, C6, A5
        _add_sine_note(mix, _midi_to_freq(88), start_sec=1.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(84), start_sec=2.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(81), start_sec=3.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        # Bar 2 ripples: G6, E6, D6
        _add_sine_note(mix, _midi_to_freq(91), start_sec=5.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(88), start_sec=6.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(86), start_sec=7.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        
        # Bar 3-4 (8-16s): G6
        _add_sine_chord(mix, [43, 50, 55, 59, 64], start_sec=8.0, dur_sec=8.0, vol=0.07, shape='cozy', fade_in_sec=1.5, fade_out_sec=1.5)
        # Rippling droplets: F6, D6, B5
        _add_sine_note(mix, _midi_to_freq(89), start_sec=9.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(86), start_sec=10.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(83), start_sec=11.5, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        # Bar 4 ripples: E6, C6, G5
        _add_sine_note(mix, _midi_to_freq(88), start_sec=13.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(84), start_sec=14.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
        _add_sine_note(mix, _midi_to_freq(79), start_sec=15.0, dur_sec=1.5, vol=0.025, shape='cozy', fade_in_sec=0.2, fade_out_sec=0.8)
    elif scene == 'dungeon_combat':
        # Intense heart-pounding chiptune beat
        # Fast bass notes + alert chiptune theme
        for i in range(n):
            t = i / _RATE
            rumble = 0.05 * math.sin(2*math.pi*75*t)
            # Add a ticking hi-hat noise
            hihat = 0
            if (i % int(_RATE * 0.25)) < int(_RATE * 0.02): # 16th beat tick
                hihat = 0.01 * random.uniform(-1, 1)
            mix[i] = rumble + hihat
            
        # Fast combat bass progression (Am -> F -> G -> Em)
        # 140 BPM, so beats are every 0.43 seconds.
        # Bar 1 (0-4s): Am / F / G / Em chiptune arpeggio
        for bar in range(4):
            start = bar * 4.0
            root_note = [45, 41, 43, 40][bar]
            _add_sine_chord(mix, [root_note, root_note+7], start_sec=start, dur_sec=4.0, vol=0.08, shape='triangle', fade_in_sec=0.1, fade_out_sec=0.1)
            # Fast minor melody
            _add_sine_note(mix, _midi_to_freq(root_note+12), start_sec=start+0.0, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            _add_sine_note(mix, _midi_to_freq(root_note+15), start_sec=start+0.5, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            _add_sine_note(mix, _midi_to_freq(root_note+19), start_sec=start+1.0, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            _add_sine_note(mix, _midi_to_freq(root_note+17), start_sec=start+1.5, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            
            _add_sine_note(mix, _midi_to_freq(root_note+12), start_sec=start+2.0, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            _add_sine_note(mix, _midi_to_freq(root_note+14), start_sec=start+2.5, dur_sec=0.4, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.1)
            _add_sine_note(mix, _midi_to_freq(root_note+15), start_sec=start+3.0, dur_sec=0.8, vol=0.04, shape='cozy', fade_in_sec=0.01, fade_out_sec=0.2)
    else:
        # Silent
        pass
        
    # Master clip & convert to 16-bit PCM integer buffer with scaling
    for i in range(n):
        buf[i] = int(max(-32767, min(32767, mix[i] * 0.45 * 32767)))
        
    return pygame.mixer.Sound(buffer=buf)


def _build_ambients():
    if not _enabled: return
    try:
        for scene_type in ('outdoor', 'forest', 'cave', 'indoor', 'water', 'dungeon_combat'):
            _AMBIENT_LOOPS[scene_type] = _ambient_loop(scene_type)
    except Exception:
        pass


# Mapping nama scene game → kategori ambient
_SCENE_AMBIENT = {
    'farm': 'outdoor', 'town': 'outdoor',
    'mountain': 'forest', 'cemetery': 'forest',
    'lake': 'water',
    'naga_cave': 'cave', 'dungeon': 'cave',
    'house': 'indoor', 'shop': 'indoor', 'smith': 'indoor',
    'clinic': 'indoor', 'studio': 'indoor', 'greenhouse': 'indoor',
}


def set_ambient_for_scene(scene_name: str, volume: float = 0.30):
    """Switch ambient loop berdasarkan scene aktif."""
    global _current_ambient
    if not _enabled or not _AMBIENT_LOOPS:
        return
    category = _SCENE_AMBIENT.get(scene_name, 'outdoor')
    if _current_ambient[1] == category:
        return  # already playing
    # Stop previous
    if _current_ambient[0] is not None:
        try: _current_ambient[0].fadeout(500)
        except Exception: pass
    snd = _AMBIENT_LOOPS.get(category)
    if snd is None:
        _current_ambient = (None, None)
        return
    try:
        snd.set_volume(volume)
        ch = snd.play(loops=-1, fade_ms=500)
        _current_ambient = (ch, category)
    except Exception:
        _current_ambient = (None, None)


def update_ambient_dynamic(state, player, dt):
    """Secara dinamis menyesuaikan volume/BGM berdasarkan intensitas pertempuran, 
    HP kritis, maupun mode Sapoe Terbang melesat cepat."""
    global _current_ambient
    if not _enabled or not _AMBIENT_LOOPS:
        return
        
    # 1. Cek intensitas dungeon (adanya musuh aktif di dekat player)
    mobs_nearby = False
    if state.scene_name == 'dungeon' and hasattr(state, 'mobs'):
        for mob in state.mobs:
            # Hitung jarak tile 2D
            dist = math.hypot(mob['x'] - player.x/2.0, mob['y'] - player.z/2.0)
            if dist < 4.5: # 4.5 tiles radius
                mobs_nearby = True
                break
                
    # Tentukan target ambient kategori
    target_category = _SCENE_AMBIENT.get(state.scene_name, 'outdoor')
    if mobs_nearby:
        target_category = 'dungeon_combat'
        
    # Switch ambient jika berubah
    if _current_ambient[1] != target_category:
        # Stop ambient lama dengan fadeout cepat
        if _current_ambient[0] is not None:
            try: _current_ambient[0].fadeout(350)
            except Exception: pass
        snd = _AMBIENT_LOOPS.get(target_category)
        if snd is not None:
            try:
                snd.set_volume(0.30)
                ch = snd.play(loops=-1, fade_ms=350)
                _current_ambient = (ch, target_category)
            except Exception:
                _current_ambient = (None, None)
        else:
            _current_ambient = (None, None)
            
    # 2. Sesuaikan volume berdasarkan status intensitas (HP Kritis & Sapoe Terbang)
    if _current_ambient[0] is not None:
        ch = _current_ambient[0]
        base_vol = 0.32 if target_category == 'dungeon_combat' else 0.30
        
        # Nyawa kritis meredupkan musik
        hp_ratio = max(0.0, state.hp / max(state.max_hp, 1))
        if hp_ratio < 0.35:
            target_vol = base_vol * (0.2 + 0.8 * (hp_ratio / 0.35))
        else:
            target_vol = base_vol
            
        # Sapoe terbang mendongkrak intensitas volume!
        if getattr(player, '_is_flying', False):
            target_vol *= 1.25
            
        try:
            # Lakukan transisi volume secara lerp halus
            cur_vol = ch.get_volume()
            new_vol = cur_vol + (target_vol - cur_vol) * 4.0 * dt
            ch.set_volume(max(0.0, min(1.0, new_vol)))
        except Exception:
            pass