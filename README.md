# Bass Line & Chord Tracker

A web application that extracts chords and bass lines from YouTube links or uploaded audio files.

## Features
- YouTube link processing (via `yt-dlp`)
- Audio file upload (MP3, WAV, M4A, OGG)
- Chord detection and bass line extraction (via `librosa`)
- Interactive player with real-time chord/note display
- Tempo control (0.5x - 2.0x)
- Transposition control (-12 to +12 semitones)
- Visualized timeline

## Requirements
- Python 3.10+
- `ffmpeg` (must be in your system PATH)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   python3 -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
   ```

3. Open your browser at `http://localhost:8000`.
