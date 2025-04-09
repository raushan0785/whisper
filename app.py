from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import whisper
import tempfile
import os


os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model = whisper.load_model("tiny") 


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("index.html")

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
   
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name


    result = model.transcribe(temp_audio_path)


    os.remove(temp_audio_path)

    return {"filename": file.filename, "transcription": result["text"]}
