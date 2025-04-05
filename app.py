from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import whisper
import tempfile
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
try:
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")  # Use 'tiny' or 'base'
    print("Model loaded successfully!")
except Exception as e:
    model = None
    print("Model loading failed:", e)

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Transcriber</title></head>
    <body>
        <h2>Upload Audio</h2>
        <input type="file" id="fileInput" accept="audio/*" />
        <button onclick="uploadAudio()">Upload</button>
        <p id="status"></p>
        <pre id="result"></pre>

        <script>
            async function uploadAudio() {
                const input = document.getElementById("fileInput");
                const status = document.getElementById("status");
                const result = document.getElementById("result");

                if (!input.files.length) {
                    alert("Choose an audio file!");
                    return;
                }

                status.innerText = "Uploading...";
                const formData = new FormData();
                formData.append("file", input.files[0]);

                try {
                    const res = await fetch("/transcribe", {
                        method: "POST",
                        body: formData,
                    });

                    const data = await res.json();
                    result.innerText = data.transcription || data.error || "No transcription.";
                    status.innerText = "Done";
                } catch (err) {
                    status.innerText = "Network error";
                    result.innerText = err;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Use under 5MB.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(contents)
            temp_path = temp_audio.name

        print("Transcribing:", temp_path)
        result = model.transcribe(temp_path, fp16=False)

        os.remove(temp_path)

        return {"filename": file.filename, "transcription": result.get("text", "")}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
