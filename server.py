import io
import os
import shutil
import subprocess
from time import sleep
import zipfile
import demucs.separate
from fastapi import FastAPI, File, Response, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils import TEMP_FOLDER, mkdir

app = FastAPI()

python = "python"

class Item(BaseModel):
    action: str
    id: str

def get_models():
    folders = os.listdir(f"{os.getcwd()}/models")
    models = []
    for model in folders:
        model_files = os.listdir(f"{os.getcwd()}/models/{model}")
        pth = [file for file in model_files if file.endswith('.pth')].pop()
        index = [file for file in model_files if file.endswith('.index')].pop()
        models.append({
            "name": model,
            "index": f"{os.getcwd()}/models/{model}/{index}",
            "pth": f"{os.getcwd()}/models/{model}/{pth}",
        })
    return models


def zipfiles(id, filenames):
    zip_subdir = ""
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = io.BytesIO()
    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, f"{fname}")

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed")
    # ..and correct content-disposition
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp

@app.get("/get_models")
async def get_models_api():
    return JSONResponse([model["name"] for model in get_models()])



@app.post("/separate_tracks")
async def split_audio(id: str = Form(...), file: UploadFile = File(...)):
    # Define the directory where you want to save the file
    upload_dir = os.path.join(TEMP_FOLDER, id)
    print("server separate_tracks upload_dir", upload_dir)
    # Create the directory if it doesn't exist
    mkdir(upload_dir)
    
    # Create the file path
    file_path = os.path.join(upload_dir, f"{id}.mp3")
    # Save the file
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    demucs.separate.main(["-j", "10", "--out", upload_dir, file_path])

    sleep(1)

    files = zipfiles(id, [
        os.path.join(upload_dir, "htdemucs", id, "bass.wav"),
        os.path.join(upload_dir, "htdemucs", id, "drums.wav"),
        os.path.join(upload_dir, "htdemucs", id, "other.wav"),
        os.path.join(upload_dir, "htdemucs", id, "vocals.wav"),
    ])

    # shutil.rmtree(os.path.join(upload_dir, "htdemucs"))

    return files

@app.post("/change_voice")
async def change_voice(id: str = Form(...), pitch: str = Form(...), voice: str = Form(...), file: UploadFile = File(...)):
    # Define the directory where you want to save the file
    upload_dir = os.path.join(TEMP_FOLDER, id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"voiceonly.mp3")
    # Save the file
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    model = next(model for model in get_models() if model["name"] == voice)

    commands = [
        python, 
        os.path.join(os.getcwd(),
        "rvc",
        "cli.py"),
        "--input_audio",
        file_path,
        "--speaker_id",
        "0",
        "--f0_method",
        "crepe",
        "--crepe_hop_length",
        "1",
        "--f0_up_key",
        pitch or 0,
        "--output_path", 
        os.path.join(upload_dir, "aivoice.wav"), 
        "--model_path", model["pth"], 
        "--file_index", model["index"]
    ]
    subprocess.run(commands)

    sleep(1)

    files = zipfiles(id, [
        os.path.join(upload_dir, "aivoice.wav"),
    ])
    # shutil.rmtree(os.path.join(upload_dir, "htdemucs"))
    return files


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)