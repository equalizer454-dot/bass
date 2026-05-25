from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('app/static/index.html')
