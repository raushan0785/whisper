from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import os
from fastapi.responses import HTMLResponse

app = FastAPI()

# CORS for all domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper Tiny model (low memory)
model = whisper.load_model("tiny")

@app.get("/", response_class=HTMLResponse)
def read_index():
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
        <input type="file" id="fileInput">
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

                try {
                    const response = await fetch("/transcribe/", {
                        method: "POST",
                        body: formData
                    });

                    const result = await response.json();
                    document.getElementById("transcription").innerText = result.transcription;
                } catch (error) {
                    document.getElementById("transcription").innerText = "Error transcribing file!";
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    result = model.transcribe(temp_audio_path)
    os.remove(temp_audio_path)
    return {"filename": file.filename, "transcription": result["text"]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
