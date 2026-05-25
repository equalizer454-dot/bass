from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
import time
import asyncio
from pydantic import BaseModel
import os
import uuid
import shutil
from .downloader import download_audio
from .processor import process_audio
import json

app = FastAPI()

tasks = {}

class ProcessRequest(BaseModel):
    url: str

def background_process(task_id: str, url: str):
    try:
        tasks[task_id]['status'] = 'downloading'
        tid, filepath, title = download_audio(url, output_dir="app/static/downloads")
        tasks[task_id]['title'] = title
        tasks[task_id]['audio_url'] = f"/static/downloads/{os.path.basename(filepath)}"

        tasks[task_id]['status'] = 'processing'
        result = process_audio(filepath)
        tasks[task_id]['result'] = result
        tasks[task_id]['status'] = 'completed'
    except Exception as e:
        tasks[task_id]['status'] = f'failed: {str(e)}'

@app.post("/api/process")
async def process(request: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'queued', 'title': '', 'result': None, 'audio_url': None}
    background_tasks.add_task(background_process, task_id, request.url)
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    upload_dir = "app/static/downloads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_extension = os.path.splitext(file.filename)[1]
    if file_extension.lower() not in [".mp3", ".wav", ".m4a", ".ogg"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    temp_path = os.path.join(upload_dir, f"{task_id}_temp{file_extension}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convert to wav if not already wav
    final_path = os.path.join(upload_dir, f"{task_id}.wav")
    if file_extension.lower() != ".wav":
        try:
            import subprocess
            subprocess.run(["ffmpeg", "-y", "-i", temp_path, final_path], check=True)
            os.remove(temp_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    else:
        os.rename(temp_path, final_path)

    tasks[task_id] = {'status': 'queued', 'title': file.filename, 'result': None, 'audio_url': f"/static/downloads/{task_id}.wav"}

    def background_process_file(task_id: str, filepath: str):
        try:
            tasks[task_id]['status'] = 'processing'
            result = process_audio(filepath)
            tasks[task_id]['result'] = result
            tasks[task_id]['status'] = 'completed'
        except Exception as e:
            tasks[task_id]['status'] = f'failed: {str(e)}'

    background_tasks.add_task(background_process_file, task_id, final_path)
    return {"task_id": task_id}

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('app/static/index.html')

# Background task for cleaning up old files
async def cleanup_old_files():
    while True:
        try:
            now = time.time()
            upload_dir = "app/static/downloads"
            if os.path.exists(upload_dir):
                for f in os.listdir(upload_dir):
                    if f == ".gitkeep": continue
                    filepath = os.path.join(upload_dir, f)
                    if os.path.isfile(filepath):
                        if now - os.path.getmtime(filepath) > 3600: # 1 hour
                            os.remove(filepath)
                            # Also remove from tasks dict if possible
                            task_id = f.split('.')[0].replace("_temp", "")
                            if task_id in tasks:
                                del tasks[task_id]
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(600) # Run every 10 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_files())
