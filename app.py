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

# Load Whisper model
try:
    print("Loading Whisper model...")
    model = whisper.load_model("tiny.en")
    print("Model loaded successfully!")
except Exception as e:
    model = None
    print("Model loading failed:", e)

# Serve HTML UI
@app.get("/", response_class=HTMLResponse)
@app.head("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Transcription</title>
    </head>
    <body>
        <h2>Upload an Audio File</h2>
        <input type="file" id="fileInput" accept="audio/*">
        <button onclick="uploadAudio()">Upload</button>
        <p id="status" style="color:blue;"></p>
        <h3>Transcription:</h3>
        <pre id="transcription"></pre>

        <script>
            async function uploadAudio() {
                const input = document.getElementById("fileInput");
                const status = document.getElementById("status");
                const output = document.getElementById("transcription");

                if (!input.files.length) {
                    alert("Please select a file!");
                    return;
                }

                status.innerText = "Transcribing, please wait...";
                output.innerText = "";

                const formData = new FormData();
                formData.append("file", input.files[0]);

                try {
                    const res = await fetch(window.location.origin + "/transcribe", {
                        method: "POST",
                        body: formData
                    });

                    const data = await res.json();
                    if (data.transcription) {
                        status.innerText = "Done!";
                        output.innerText = data.transcription;
                    } else {
                        status.innerText = "Failed to transcribe.";
                        output.innerText = data.error || "No transcription found.";
                    }
                } catch (err) {
                    status.innerText = "Network error!";
                    output.innerText = err;
                }
            }
        </script>
    </body>
    </html>
    """

# Transcription route (no trailing slash)
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded. Please reload the server."}

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            temp.write(await file.read())
            temp_path = temp.name

        print(f"Saved uploaded file to: {temp_path}")
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
