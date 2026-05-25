import librosa
import numpy as np
import os
import json

def process_audio(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    y, sr = librosa.load(filepath, sr=None)

    # 1. Chord Detection
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chords = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    chord_sequence = []
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr)

    for i in range(chroma.shape[1]):
        peak_idx = np.argmax(chroma[:, i])
        chord_sequence.append({
            'time': float(times[i]),
            'chord': chords[peak_idx]
        })

    # 2. Bass Line Extraction
    fmin = librosa.note_to_hz('C1')
    fmax = librosa.note_to_hz('C3')

    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr)

    bass_sequence = []
    times_bass = librosa.frames_to_time(np.arange(len(f0)), sr=sr)

    for i in range(len(f0)):
        if voiced_flag[i]:
            note_name = librosa.hz_to_note(f0[i])
            bass_sequence.append({
                'time': float(times_bass[i]),
                'note': note_name
            })

    # 3. Tempo detection
    tempo_array, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = tempo_array.item() if hasattr(tempo_array, 'item') else float(tempo_array)

    result = {
        'tempo': tempo,
        'chords': chord_sequence,
        'bass': bass_sequence
    }

    return result
