import yt_dlp
import os
import uuid

def download_audio(url, output_dir="downloads"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    task_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{task_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    # Check if file already exists (for testing/mocking)
    if url == "test_local":
        return "test-id", "app/backend/test_downloads/sample.wav", "Sample Video"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        final_filename = os.path.splitext(filename)[0] + ".wav"

    return task_id, final_filename, info.get('title', 'Unknown Title')
