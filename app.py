from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import whisper
import tempfile
import os

app = FastAPI()

# Allow frontend to connect from any origin (safe for demo; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
try:
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")
    print("Model loaded successfully!")
except Exception as e:
    model = None
    print("Model loading failed:", e)

@app.get("/", response_class=HTMLResponse)
def root():
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
        <h3>Status:</h3>
        <div id="status">Waiting...</div>
        <h3>Transcription:</h3>
        <pre id="transcription"></pre>

        <script>
            async function uploadAudio() {
                const input = document.getElementById("fileInput");
                const status = document.getElementById("status");
                const transcription = document.getElementById("transcription");

                if (!input.files.length) {
                    alert("Please select a file first!");
                    return;
                }

                const file = input.files[0];
                if (file.size > 5 * 1024 * 1024) {
                    alert("Please upload a file under 5MB.");
                    return;
                }

                const formData = new FormData();
                formData.append("file", file);

                status.innerText = "Uploading and transcribing...";
                transcription.innerText = "";

                try {
                    const response = await fetch(`${window.location.origin}/transcribe`, {
                        method: "POST",
                        body: formData
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        status.innerText = "Error: " + (error.detail || response.statusText);
                        return;
                    }

                    const result = await response.json();
                    status.innerText = "Done!";
                    transcription.innerText = result.transcription || "No text found.";

                } catch (error) {
                    status.innerText = "Network error!";
                    transcription.innerText = error.message;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")

    # Size limit: 5MB
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Please upload a file under 5MB.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            temp.write(contents)
            temp_path = temp.name

        result = model.transcribe(temp_path)
        os.remove(temp_path)

        return {
            "filename": file.filename,
            "transcription": result.get("text", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
