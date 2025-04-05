from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import whisper
import tempfile
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
try:
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")
    print("Model loaded successfully!")
except Exception as e:
    model = None
    print("Model loading failed:", e)

# Serve HTML on root
@app.get("/", response_class=HTMLResponse)
@app.head("/", response_class=HTMLResponse)
def home():
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
        <pre id="transcription"></pre>

        <script>
            async function uploadAudio() {
                const input = document.getElementById("fileInput");
                if (!input.files.length) {
                    alert("Please select a file!");
                    return;
                }

                const formData = new FormData();
                formData.append("file", input.files[0]);

                try {
                    const res = await fetch("/transcribe/", {
                        method: "POST",
                        body: formData
                    });

                    const data = await res.json();
                    document.getElementById("transcription").innerText =
                        data.transcription || data.error || "No transcription returned.";
                } catch (err) {
                    document.getElementById("transcription").innerText = "Error during transcription: " + err;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded. Please reload the server or check logs."}

    try:
        # Save file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name

        print(f"Saved uploaded file to: {temp_path}")

        # Run transcription
        result = model.transcribe(temp_path)
        print("Transcription result:", result)

        os.remove(temp_path)

        return {
            "filename": file.filename,
            "transcription": result.get("text", "")
        }

    except Exception as e:
        print("Transcription error:", e)
        return {"error": f"Transcription failed: {str(e)}"}
