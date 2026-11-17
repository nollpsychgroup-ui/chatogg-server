#!/usr/bin/env python3
"""THE QUIET CAR: scratch voice track and subtitles for the previs animatic.

Owner: Screenwriter. The source of truth for the lines is script/voice-sides.md
(verbatim from the LOCKED script/draft-02.md). Timing anchors come from
camera/cues.json (DP), so the track lines up with the lighting cues and the cut.

This is TIMING ONLY, not performance. It's offline TTS (CMU Flite, the system
libflite voices, loaded through ctypes) plus ffmpeg for pitch, tempo, level and
phone filtering. It will be replaced by the real voice record.

Outputs (written next to this script, and ../quiet-car.srt):
  scratch-voice.flac      48 kHz mono, full film length (cues.json duration)
  scratch-voice-lines.json  every placed line: id, voice, start/end (s), level
  ../quiet-car.srt        subtitles: intelligible dialogue only

Run: python3 film/previs/voice/build_scratch_voice.py   (needs ffmpeg + numpy)
"""
import ctypes as C, json, os, subprocess, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.normpath(os.path.join(HERE, '..', '..'))
CUES = json.load(open(os.path.join(FILM, 'camera', 'cues.json')))
SR = 48000
DUR = float(CUES['duration_s'])
CUE_T = {c['id']: c['t'] for c in CUES['cues']}
EV_T = {e['id']: e['t'] for e in CUES['events']}

# ---------------------------------------------------------------- voices ----
# Distinct voice per character: base Flite voice + pitch factor + tempo.
VOICES = {
    'NOOR':   dict(base='slt',   pitch=1.00, tempo=0.97),
    'BEA':    dict(base='slt',   pitch=0.86, tempo=0.88),   # lower, slower: the patient voice
    'MUM':    dict(base='slt',   pitch=1.08, tempo=1.00),
    'KAI':    dict(base='kal16', pitch=1.12, tempo=1.08),   # younger, quicker
    'WALTER': dict(base='awb',   pitch=0.88, tempo=0.85),   # older, unhurried
    'MARK':   dict(base='rms',   pitch=0.95, tempo=1.00),
    'PA':     dict(base='kal',   pitch=1.00, tempo=0.95),   # the classic machine diphone voice
}

# Level scale from voice-sides.md -> ffmpeg filter chain (after pitch/tempo).
LEVELS = {
    'FULL':    'volume=0dB',
    'LOW':     'volume=-6dB',
    'WHISPER': 'highpass=f=250,volume=-13dB',
    'FAINT':   'highpass=f=250,volume=-19dB',             # "barely audible"
    'PHONE':   'highpass=f=350,lowpass=f=3200,acompressor=threshold=-20dB:ratio=6,volume=-14dB',
    'PHONE_TINY': 'highpass=f=450,lowpass=f=2800,acompressor=threshold=-20dB:ratio=6,volume=-20dB',
    # Mark's beds and Mum's first bed must NEVER be intelligible (Director ruling):
    'MURMUR':  'lowpass=f=520,highpass=f=180,acompressor=threshold=-24dB:ratio=8,volume=-21dB',
    'MURMUR_FAR': 'lowpass=f=420,highpass=f=200,acompressor=threshold=-24dB:ratio=8,volume=-27dB',
    'PA':      'highpass=f=400,lowpass=f=4500,aecho=0.6:0.5:38|71:0.35|0.2,volume=+4dB',
}

# ----------------------------------------------------------------- flite ----
_L = '/usr/lib/x86_64-linux-gnu/'
for _n in ('libflite.so.1', 'libflite_usenglish.so.1', 'libflite_cmulex.so.1'):
    C.CDLL(_L + _n, mode=C.RTLD_GLOBAL)
_fl = C.CDLL(_L + 'libflite.so.1')
_fl.flite_init()
_fl.flite_text_to_speech.restype = C.c_float
_fl.flite_text_to_speech.argtypes = [C.c_char_p, C.c_void_p, C.c_char_p]
_VO = {}

def _voice(base):
    if base not in _VO:
        lib = C.CDLL(_L + f'libflite_cmu_us_{base}.so.1', mode=C.RTLD_GLOBAL)
        reg = getattr(lib, f'register_cmu_us_{base}')
        reg.restype, reg.argtypes = C.c_void_p, [C.c_char_p]
        _VO[base] = reg(None)
    return _VO[base]

TMP = tempfile.mkdtemp(prefix='qc_voice_')

def _read(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a

def synth(voice, text, level):
    """TTS one phrase -> processed float32 mono at SR."""
    v = VOICES[voice]
    raw = os.path.join(TMP, f'raw_{len(os.listdir(TMP))}.wav')
    _fl.flite_text_to_speech(text.encode(), _voice(v['base']), raw.encode())
    with wave.open(raw) as w:
        sr0 = w.getframerate()
    p, t = v['pitch'], v['tempo']
    mid = raw.replace('raw_', 'pt_')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af',
                    f"asetrate={int(sr0 * p)},aresample={SR},atempo={t / p:.4f}", '-ac', '1', '-ar', str(SR), mid], check=True)
    # normalise every voice to the same speech loudness (-20 dBFS RMS over voiced
    # samples) so the LEVEL scale, not the TTS engine, decides how loud a line is
    a = _read(mid)
    act = a[np.abs(a) > 0.02]
    g = 10 ** (-20 / 20) / (np.sqrt((act ** 2).mean()) if len(act) else 1)
    a = np.clip(a * g, -1, 1)
    norm = raw.replace('raw_', 'nm_')
    with wave.open(norm, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
    out = raw.replace('raw_', 'fx_')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', norm, '-af', LEVELS[level], out], check=True)
    a = _read(out)
    # trim TTS leading/trailing silence so anchors are honest
    nz = np.where(np.abs(a) > 10 ** (-50 / 20))[0]
    return a[nz[0]:nz[-1] + 1] if len(nz) else a

def fricative(dur, kind, level_db):
    """A cut-off consonant onset: /s/ (bright hiss) or /f/ (soft, dull)."""
    n = int(dur * SR)
    rng = np.random.default_rng(7 if kind == 's' else 11)
    x = rng.standard_normal(n).astype(np.float32)
    if kind == 's':      # crude high-pass: first difference twice
        x = np.diff(np.diff(x, prepend=0), prepend=0) * 0.35
    else:                # /f/: gentler
        x = np.diff(x, prepend=0) * 0.18
    env = np.minimum(1, np.arange(n) / (0.02 * SR))
    return x * env * 10 ** (level_db / 20)

def fade(a, tin=0.005, tout=0.008):
    a = a.copy(); i, o = int(tin * SR), int(tout * SR)
    if i: a[:i] *= np.linspace(0, 1, i)
    if o: a[-o:] *= np.linspace(1, 0, o)
    return a

def dur(a):
    return len(a) / SR

# ------------------------------------------------------------- placement ----
MIX = np.zeros(int((DUR + 1) * SR), dtype=np.float32)
PLACED = []
SUBS = []

def put(lid, voice, a, start, level, sub=None, italic=False, sub_end=None, note=''):
    s = int(round(start * SR))
    MIX[s:s + len(a)] += a
    end = start + dur(a)
    PLACED.append(dict(id=lid, voice=voice, level=level, start=round(start, 3), end=round(end, 3), note=note))
    if sub:
        SUBS.append(dict(start=start, end=sub_end if sub_end is not None else end, text=sub, italic=italic))
    return end

def say(lid, voice, text, level, start=None, end=None, sub=None, italic=False, note=''):
    """Place a line by its start time, or by its end time (end= anchors before a cue)."""
    a = fade(synth(voice, text, level))
    if start is None:
        start = end - dur(a)
    return put(lid, voice, a, start, level, sub if sub is not None else text, italic, note=note)

def seq(lid, voice, parts, level, start, sub=None, note=''):
    """Several phrases with explicit gaps: parts = [(text, gap_after), ...]."""
    t = start; first = start
    for i, (text, gap) in enumerate(parts):
        a = fade(synth(voice, text, level))
        put(f'{lid}.{i+1}', voice, a, t, level, note=note)
        t += dur(a) + gap
    SUBS.append(dict(start=first, end=t - parts[-1][1], text=sub or ' '.join(p[0] for p in parts), italic=False))
    return t

def seq_end(lid, voice, parts, level, end, sub=None):
    """Like seq() but anchored so the last phrase ends at `end` (lines that set off a cue)."""
    clips = [fade(synth(voice, p, level)) for p, _ in parts]
    total = sum(dur(c) for c in clips) + sum(g for _, g in parts[:-1])
    t = end - total; first = t
    for i, (c, (_, gap)) in enumerate(zip(clips, parts)):
        put(f'{lid}.{i+1}', voice, c, t, level)
        t += dur(c) + gap
    SUBS.append(dict(start=first, end=end, text=sub or ' '.join(p for p, _ in parts), italic=False))

PRE = 0.25   # a line that sets off a cue ends this long before the cue fires

# ---- Scene 2: Mark's first call ---------------------------------------
say('NOOR-01', 'NOOR', 'Hi. Hi, yeah. I\'m on the train.', 'WHISPER', start=EV_T['mark_call_1'] + 3.5)
say('MARK-01', 'MARK', 'Hey, you. You on your way? How was it today?', 'MURMUR', start=EV_T['mark_call_1'] + 6.6, sub='')
say('NOOR-02', 'NOOR', 'Just leaving the office now.', 'WHISPER', end=CUE_T['1'] - PRE, note='lie 1 -> cue 1')
say('MARK-01b', 'MARK', 'Oh no. Long one?', 'MURMUR', start=CUE_T['1'] + 4.0, sub='')
say('NOOR-03', 'NOOR', 'Long day. The Henley account. Again.', 'WHISPER', end=CUE_T['2'] - PRE, note='lie 2 -> cue 2')
say('KAI-01', 'KAI', 'Was that the brakes?', 'LOW', start=103.5)
say('NOOR-04', 'NOOR', 'No, don\'t wait up. Love you.', 'WHISPER', end=EV_T['love_you'] + 0.9, note="'Love you' is true: no cue")

# ---- Scene 3: Kai -------------------------------------------------------
say('KAI-02', 'KAI', 'Yeah?', 'FULL', start=EV_T['mum_call'] + 2.0)
say('MUM-01', 'MUM', 'Where are you? It\'s gone eleven, Kai.', 'MURMUR', start=EV_T['mum_call'] + 3.2, sub='')
say('KAI-03', 'KAI', 'I\'m at the library, Mum.', 'FULL', end=CUE_T['3'] - PRE, note='his lie -> cue 3 brownout')
# KAI-04: performed past the cut; hard digital cut on the blackout frame (cue 4).
laugh = fade(synth('KAI', 'Heh.', 'LOW'))
pre = fade(synth('KAI', 'No, that\'s, it\'s the library. They\'re doing work on the', 'FULL'))
run = fade(synth('KAI', 'No, that\'s, it\'s the library. They\'re doing work on the, on the lines, or, I dunno, it\'s', 'FULL'), tout=0)
t4 = CUE_T['4']
k_start = t4 - dur(pre) - 0.12
put('KAI-04.laugh', 'KAI', laugh, k_start - dur(laugh) - 0.25, 'LOW', note='nervous laugh')
cut = int((t4 - k_start) * SR)
put('KAI-04', 'KAI', run[:cut], k_start, 'FULL',
    sub='No, that\'s — it\'s the library. They\'re doing work on the —', sub_end=t4,
    note='HARD CUT at cue 4 (blackout): true dead air until 4.up')
# Mum, after lights up: the only intelligible phone line.
up = CUE_T['4.up']
say('MUM-02a', 'MUM', 'Kai?', 'PHONE', start=up + 1.0, sub='Kai?', italic=True)
say('MUM-02b', 'MUM', 'Kai?', 'PHONE', start=up + 3.4, sub='Kai?', italic=True)

# ---- Scene 4: the note and the test --------------------------------------
say('NOOR-06', 'NOOR', 'What, where did he', 'LOW', start=up + 8.5, sub='What — where did he —')
say('NOOR-08a', 'NOOR', 'Hey.', 'LOW', start=173.0)
say('NOOR-08b', 'NOOR', 'Hey!', 'FULL', start=175.0, sub='Hey!')
say('NOOR-09', 'NOOR', 'That\'s insane.', 'FAINT', start=206.5)
say('NOOR-10', 'NOOR', 'My name is Noor.', 'LOW', start=CUE_T['5'] - 9.5, note='truth: nothing; hold')
# NOOR-11: "My name is S-": /s/ onset only, cut by Walter's hand at cue 5.
mn = fade(synth('NOOR', 'My name is', 'LOW'))
s_on = fricative(0.15, 's', -26)
t5 = CUE_T['5']
put('NOOR-11', 'NOOR', np.concatenate([mn, np.zeros(int(0.04 * SR), np.float32), s_on]), t5 - dur(mn) - 0.19, 'LOW',
    sub='My name is S—', sub_end=t5 + 0.6, note='cut on the /s/ at cue 5 (wrist clamp)')
MUM_LATE = [(EV_T['D2'] + 17.0, 'PHONE_TINY'), (EV_T['thumb_over_end_call'] + 2.5, 'PHONE_TINY')]
for i, (tm, lv) in enumerate(MUM_LATE):
    say(f'MUM-02{chr(99 + i)}', 'MUM', 'Kai?', lv, start=tm, sub='Kai?', italic=True)

# ---- Scene 5: the truth exchange ---------------------------------------
say('BEA-01', 'BEA', 'You okay?', 'LOW', start=286.0)
im = fade(synth('NOOR', 'I\'m', 'LOW'))
t6 = CUE_T['6']
put('NOOR-13', 'NOOR', np.concatenate([im, np.zeros(int(0.03 * SR), np.float32), fricative(0.11, 'f', -30)]),
    t6 - dur(im) - 0.14, 'LOW', sub='I\'m f—', sub_end=t6 + 0.5, note='self-caught on the /f/ at cue 6')
say('NOOR-14', 'NOOR', 'I\'m not fine.', 'LOW', start=t6 + 2.6)
seq('BEA-02', 'BEA', [('Me neither.', 0.7), ('I haven\'t slept in two days.', 0)], 'LOW', start=301.5)
say('NOOR-15', 'NOOR', 'You\'ve seen this before.', 'LOW', start=309.8)
say('WALTER-01', 'WALTER', 'I ride it every night.', 'LOW', start=314.0)
say('NOOR-16', 'NOOR', 'Why?', 'LOW', start=317.0)
t = seq('WALTER-02', 'WALTER', [
    ('My wife was ill a long time.', 0.7),
    ('Everyone told me she\'d be fine.', 0.7),
    ('Doctors.', 0.45), ('Her sister.', 0.6), ('Me, to her.', 0)], 'LOW', start=321.5,
    sub='My wife was ill a long time. Everyone told me she\'d be fine.\nDoctors. Her sister. Me, to her.')
say('WALTER-02.6', 'WALTER', 'This is the only place nobody can say that to me.', 'LOW', start=t + 2.6, note='after the (beat)')

# ---- Scene 6: the creeping dark ----------------------------------------
say('NOOR-17', 'NOOR', 'Nobody said anything.', 'WHISPER', end=CUE_T['7.2'] - PRE)
say('BEA-03', 'BEA', 'It isn\'t only what you say.', 'LOW', start=381.0)
say('BEA-04', 'BEA', 'Whatever it is, say it.', 'WHISPER', end=CUE_T['7.8'] - PRE)
# "I can't -" / "Say it.": a live overlap (Director ruling); the 7.9 tick FOLLOWS the pair.
bea5 = fade(synth('BEA', 'Say it.', 'LOW'))
b5_start = CUE_T['7.9'] - 0.4 - dur(bea5)
n19 = synth('NOOR', 'I can\'t, he\'ll', 'WHISPER')            # performed past the cut
n19 = fade(n19[:int((dur(fade(synth('NOOR', 'I can\'t', 'WHISPER'))) + 0.12) * SR)], tout=0.03)
put('NOOR-19', 'NOOR', n19, b5_start + 0.15 - dur(n19), 'WHISPER', sub=None,
    note='Bea overlaps on the dash; cut off by "Say it."')
put('BEA-05', 'BEA', bea5, b5_start, 'LOW', note='ends 0.4 s before the 7.9 tick')
# one two-speaker title for the overlap (a 0.5 s title would be unreadable)
SUBS.append(dict(start=b5_start + 0.15 - dur(n19), end=CUE_T['7.9'], text='- I can\'t —\n- Say it.', italic=False))
say('WALTER-03', 'WALTER', 'He\'s asking.', 'LOW', start=EV_T['he_is_asking'])

# ---- Scene 7: the confession -------------------------------------------
say('NOOR-20', 'NOOR', 'Mark.', 'LOW', start=456.5)
say('MARK-02', 'MARK', 'Hey. You\'re late. Everything all right?', 'MURMUR', start=457.4, sub='')
seq_end('NOOR-21', 'NOOR', [('No.', 0.3), ('Listen.', 0.45), ('I\'m not leaving the office.', 0)], 'LOW', end=CUE_T['8.0'] - PRE)
seq_end('NOOR-22', 'NOOR', [('I haven\'t been to the office since September.', 0.8), ('They let me go.', 0.6),
                            ('The whole floor.', 0)], 'LOW', end=CUE_T['8.1'] - PRE)
# NOOR-23: the run-on, the half-beat catch on "library", the restart.
a1 = fade(synth('NOOR', 'I get dressed and I get on the train and I go to the library', 'LOW'))
a2 = [fade(synth('NOOR', p, 'LOW')) for p in ('and I sit there.', 'All day.', 'And then I come home.')]
gaps = [0.5, 0.6, 0]
tail = sum(dur(x) for x in a2) + sum(gaps)
t_end = CUE_T['8.2'] - PRE
t2 = t_end - tail
t1 = t2 - 0.7 - dur(a1)
put('NOOR-23.1', 'NOOR', a1, t1, 'LOW', sub='I get dressed and I get on the train and I go to the library —', sub_end=t1 + dur(a1) + 0.5)
t = t2
for i, (x, g) in enumerate(zip(a2, gaps)):
    put(f'NOOR-23.{i+2}', 'NOOR', x, t, 'LOW'); t += dur(x) + g
SUBS.append(dict(start=t2, end=t_end, text='— and I sit there. All day. And then I come home.', italic=False))
# NOOR-24: trails off on "couldn't"; the relight run (8.3 on) ANSWERS the broken sentence (DP/script).
a = synth('NOOR', 'I didn\'t tell you because you\'d have been kind about it, and I couldn\'t', 'LOW')
n = int(0.45 * SR); a = fade(a); a[-n:] *= np.linspace(1, 0, n) ** 2
put('NOOR-24', 'NOOR', a, CUE_T['8.3'] - 0.3 - dur(a), 'LOW', sub='I didn\'t tell you because you\'d have been kind about it, and I couldn\'t —',
    note='trails into breath; ends 0.3 s before 8.3, then the relight run')
say('NOOR-25', 'NOOR', 'I\'m sorry.', 'WHISPER', end=EV_T['silence_on_line'] - 1.2, note='then silence on the line')

# ---- Scene 8: Holloway -------------------------------------------------
say('MARK-04', 'MARK', 'Noor. Okay. Where are you now?', 'MURMUR_FAR', start=EV_T['doors_open'] + 8.0, sub='',
    note='the neutral scaffold (Director ruling); unintelligible')
say('PA-01', 'PA', 'Thank you for riding quietly.', 'PA', start=EV_T['pa_line'], italic=True,
    note='the PA speaks exactly once')

# ---------------------------------------------------------------- checks ----
DEAD = (CUE_T['4'], CUE_T['4.up'])
for p in PLACED:
    assert not (p['start'] < DEAD[1] and p['end'] > DEAD[0] + 1e-3), f"{p['id']} intrudes on the blackout's dead air"
    assert p['end'] <= EV_T['cut'], f"{p['id']} runs past the cut"
lie_cues = {'NOOR-02': '1', 'NOOR-03': '2', 'KAI-03': '3'}
for lid, c in lie_cues.items():
    p = next(x for x in PLACED if x['id'] == lid)
    assert 0 < CUE_T[c] - p['end'] < 1.0, f'{lid} not tight to cue {c}'
TICKS = [c['t'] for c in CUES['cues'] if c['type'] in ('panel_out', 'relight')]
for p in PLACED:
    hit = [t for t in TICKS if p['start'] < t < p['end']]
    assert not hit, f"{p['id']} has a tick/relight inside it at {hit}"
assert abs(MIX).max() < 1.0, 'clipping'

# --------------------------------------------------------------- outputs ----
pcm = (np.clip(MIX[:int(DUR * SR)], -1, 1) * 32767).astype(np.int16)
wav = os.path.join(TMP, 'mix.wav')
with wave.open(wav, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-compression_level', '8',
                os.path.join(HERE, 'scratch-voice.flac')], check=True)

PLACED.sort(key=lambda p: p['start'])
json.dump(dict(_note='Scratch voice placement for the previs (TTS, timing only). Generated by '
               'build_scratch_voice.py from script/voice-sides.md + camera/cues.json. Do not edit by hand.',
               sample_rate=SR, duration_s=DUR, voices=VOICES, lines=PLACED),
          open(os.path.join(HERE, 'scratch-voice-lines.json'), 'w'), indent=1)

def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

subs = sorted([s for s in SUBS if s['text']], key=lambda s: s['start'])
out = []
for i, s in enumerate(subs):
    end = max(s['end'], s['start'] + 1.0)              # minimum on-screen time
    if i + 1 < len(subs):
        end = min(end, subs[i + 1]['start'] - 0.04)    # never overlap the next title
    if s['start'] < DEAD[0] < end:
        end = DEAD[0]                                   # the blackout takes the title with it
    text = s['text']
    if s['italic']:
        text = '\n'.join(f'<i>{l}</i>' for l in text.split('\n'))
    out.append(f'{i + 1}\n{ts(s["start"])} --> {ts(end)}\n{text}\n')
open(os.path.join(FILM, 'previs', 'quiet-car.srt'), 'w').write('\n'.join(out))
print(f'{len(PLACED)} clips, {len(subs)} subtitles, peak {abs(MIX).max():.2f}')
