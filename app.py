from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import whisper
import tempfile
import os

app = FastAPI()

# Allow CORS (for local dev or frontend from other origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy load model
model = None

def get_model():
    global model
    if model is None:
        model = whisper.load_model("tiny")  # Use "base" if you want better accuracy
    return model

# Root HTML Page
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Audio Transcription</title>
    </head>
    <body>
        <h2>Upload an Audio File</h2>
        <input type="file" id="fileInput" accept="audio/*">
        <button onclick="uploadAudio()">Upload</button>
        <h3>Transcription:</h3>
        <p id="transcription"></p>

        <script>
            async function uploadAudio() {
                const fileInput = document.getElementById("fileInput");
                if (!fileInput.files.length) {
                    alert("Please select an audio file!");
                    return;
                }

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                document.getElementById("transcription").innerText = "Transcribing...";

                try {
                    const response = await fetch("https://whisper-9myq.onrender.com/transcribe/", {
                        method: "POST",
                        body: formData
                    });

                    const result = await response.json();

                    if (result.transcription) {
                        document.getElementById("transcription").innerText = result.transcription;
                    } else if (result.error) {
                        document.getElementById("transcription").innerText = "Error: " + result.error;
                    } else {
                        document.getElementById("transcription").innerText = "Unknown response format.";
                    }
                } catch (error) {
                    document.getElementById("transcription").innerText = "Failed to transcribe.";
                }
            }
        </script>
    </body>
    </html>
    """

# API to handle transcription
@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            contents = await file.read()
            temp_audio.write(contents)
            temp_audio_path = temp_audio.name

        model = get_model()
        result = model.transcribe(temp_audio_path)

        os.remove(temp_audio_path)

        return {"filename": file.filename, "transcription": result["text"]}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
