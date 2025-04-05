from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import whisper
import tempfile
import os
import traceback

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

# Serve frontend HTML
@app.get("/", response_class=HTMLResponse)
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
                    const res = await fetch("https://whisper-9myq.onrender.com/transcribe", {
                        method: "POST",
                        body: formData
                    });

                    let data;
                    try {
                        data = await res.json();
                    } catch (e) {
                        status.innerText = "Server error! Could not parse response.";
                        output.innerText = "Invalid JSON response.";
                        return;
                    }

                    if (data.transcription) {
                        status.innerText = "Done!";
                        output.innerText = data.transcription;
                    } else {
                        status.innerText = "Failed to transcribe.";
                        output.innerText = data.error || "No transcription returned.";
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

# Transcription route
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if model is None:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Model not loaded."}
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            temp.write(await file.read())
            temp_path = temp.name

        print(f"Saved uploaded file to: {temp_path}")

        # Transcribe using Whisper
        result = model.transcribe(temp_path)
        print("Transcription completed.")

        return {
            "filename": file.filename,
            "transcription": result.get("text", "")
        }

    except Exception as e:
        print("Transcription error:", traceback.format_exc())
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Transcription failed: {str(e)}"}
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
