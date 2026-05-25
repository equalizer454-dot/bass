document.addEventListener('DOMContentLoaded', () => {
    const processBtn = document.getElementById('process-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const urlInput = document.getElementById('youtube-url');
    const fileInput = document.getElementById('file-upload');
    const statusMsg = document.getElementById('status-message');
    const playerSection = document.getElementById('player-section');
    const videoTitle = document.getElementById('video-title');
    const audioPlayer = document.getElementById('audio-player');
    const timeline = document.getElementById('timeline');

    const currentChordDisplay = document.getElementById('current-chord');
    const currentBassDisplay = document.getElementById('current-bass');

    const tempoControl = document.getElementById('tempo-control');
    const tempoVal = document.getElementById('tempo-val');
    const transposeControl = document.getElementById('transpose-control');
    const transposeVal = document.getElementById('transpose-val');

    let analysisData = null;
    let taskId = null;
    let pollInterval = null;

    processBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            alert('Please enter a YouTube URL');
            return;
        }

        statusMsg.textContent = 'Queueing task...';
        processBtn.disabled = true;

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await response.json();
            taskId = data.task_id;
            startPolling();
        } catch (error) {
            statusMsg.textContent = 'Error: ' + error.message;
            setButtonsDisabled(false);
        }
    });

    uploadBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file to upload');
            return;
        }

        statusMsg.textContent = 'Uploading file...';
        setButtonsDisabled(true);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                taskId = data.task_id;
                startPolling();
            } else {
                statusMsg.textContent = 'Error: ' + (data.detail || 'Upload failed');
                setButtonsDisabled(false);
            }
        } catch (error) {
            statusMsg.textContent = 'Error: ' + error.message;
            setButtonsDisabled(false);
        }
    });

    function setButtonsDisabled(disabled) {
        processBtn.disabled = disabled;
        uploadBtn.disabled = disabled;
    }

    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${taskId}`);
                const data = await response.json();

                statusMsg.textContent = `Status: ${data.status}`;

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    analysisData = data.result;
                    displayPlayer(data);
                } else if (data.status.startsWith('failed')) {
                    clearInterval(pollInterval);
                    setButtonsDisabled(false);
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);
    }

    function displayPlayer(data) {
        playerSection.classList.remove('hidden');
        videoTitle.textContent = data.title;
        audioPlayer.src = data.audio_url;
        statusMsg.textContent = 'Ready!';
        setButtonsDisabled(false);
        renderTimeline();
    }

    function renderTimeline() {
        timeline.innerHTML = '';
        const canvas = document.createElement('canvas');
        canvas.width = timeline.clientWidth;
        canvas.height = 100;
        timeline.appendChild(canvas);
        const ctx = canvas.getContext('2d');

        const draw = () => {
            if (!analysisData) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const duration = audioPlayer.duration || 60;
            const pixelsPerSecond = canvas.width / duration;

            ctx.fillStyle = '#333';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const playhead = audioPlayer.currentTime * pixelsPerSecond;
            ctx.fillStyle = '#bb86fc';
            ctx.fillRect(0, 0, playhead, canvas.height);

            ctx.strokeStyle = 'rgba(255,255,255,0.2)';
            ctx.fillStyle = 'white';
            ctx.font = '10px Arial';

            const step = Math.max(1, Math.floor(analysisData.chords.length / 100));
            for (let i = 0; i < analysisData.chords.length; i += step) {
                const c = analysisData.chords[i];
                const x = c.time * pixelsPerSecond;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
                if (i % (step * 5) === 0) {
                    ctx.fillText(applyTranspose(c.chord), x + 2, 15);
                }
            }
            requestAnimationFrame(draw);
        };
        draw();
    }

    tempoControl.addEventListener('input', () => {
        const val = tempoControl.value;
        tempoVal.textContent = val;
        audioPlayer.playbackRate = val;
    });

    transposeControl.addEventListener('input', () => {
        transposeVal.textContent = transposeControl.value;
    });

    // Optimized lookup using binary search
    function findNearest(data, time) {
        if (!data || data.length === 0) return null;
        let low = 0, high = data.length - 1;
        while (low <= high) {
            let mid = Math.floor((low + high) / 2);
            if (data[mid].time === time) return data[mid];
            if (data[mid].time < time) low = mid + 1;
            else high = mid - 1;
        }
        return high >= 0 ? data[high] : data[0];
    }

    // Update displays during playback
    audioPlayer.addEventListener('timeupdate', () => {
        if (!analysisData) return;
        const currentTime = audioPlayer.currentTime;

        const chord = findNearest(analysisData.chords, currentTime);
        const bass = findNearest(analysisData.bass, currentTime);

        currentChordDisplay.textContent = applyTranspose(chord ? chord.chord : '-');
        currentBassDisplay.textContent = applyTranspose(bass ? (bass.note || bass.chord) : '-');
    });

    function applyTranspose(noteOrChord) {
        if (noteOrChord === '-') return '-';
        const shift = parseInt(transposeControl.value);
        if (shift === 0) return noteOrChord;

        const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
        let root = noteOrChord;
        let suffix = "";

        if (noteOrChord.length > 1 && (noteOrChord[1] === '#' || noteOrChord[1] === 'b')) {
            root = noteOrChord.substring(0, 2);
            suffix = noteOrChord.substring(2);
        } else {
            root = noteOrChord.substring(0, 1);
            suffix = noteOrChord.substring(1);
        }

        const flats = { 'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#' };
        if (flats[root]) root = flats[root];

        const idx = notes.indexOf(root);
        if (idx === -1) return noteOrChord;

        let newIdx = (idx + shift) % 12;
        if (newIdx < 0) newIdx += 12;
        return notes[newIdx] + suffix;
    }
});
