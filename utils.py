import requests
import zipfile
import io
import os
from pprint import pprint
import inquirer
import requests

# SERVER_URL = "http://192.168.111.131:8000"
SERVER_URL = "http://localhost:8000"
TEMP_FOLDER = os.path.join(os.getcwd(), "temp_files")

def get_models_from_api():
    url = f"{SERVER_URL}/get_models"
    resp = requests.get(url=url)
    models = resp.json() # Check the JSON Response Content
    return models

def mkdir(path: str):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

def separate_tracks(file_path, id):
    url = f"{SERVER_URL}/separate_tracks"
    headers = {
        "accept": "application/json"
    }

    data = {
        "id": id
    }

    files = {
        "file": (f"{id}.mp3", open(file_path, "rb"))
    }

    response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        extract_path = os.path.join(TEMP_FOLDER, id)
        mkdir(extract_path)
        zip_path = os.path.join(extract_path, f"{id}.zip")
        # Save the ZIP content to a file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        # Unzip the downloaded file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(TEMP_FOLDER, id))
            os.remove(zip_path)
    else:
        print("Request failed with status code:", response.status_code)


def change_voice(file_path, id, pitch, voice):
    url = f"{SERVER_URL}/change_voice"
    headers = {
        "accept": "application/json"
    }

    data = {
        "id": id,
        "pitch": pitch,
        "voice": voice
    }

    files = {
        "file": (f"{id}.mp3", open(file_path, "rb"))
    }

    response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        extract_path = os.path.join(TEMP_FOLDER, id)
        mkdir(extract_path)
        zip_path = os.path.join(extract_path, f"{id}.zip")
        # Save the ZIP content to a file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        # Unzip the downloaded file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(TEMP_FOLDER, id))
            os.remove(zip_path)
    else:
        print("Request failed with status code:", response.status_code)



lang = "en"
texts = {
    "fr": {
        "yes": "oui",
        "no": "non",
        "q1": "Séparer la voix et les instruments",
        "q2": "Changer la voix",
        "q3": "Quelle voix ?",
        "q4": "Modifier le pitch de la voix ?\n Femme -> Homme ~= -6\n Homme -> Femme ~= 6 |  "
    },
    "en": {
        "yes": "yes",
        "no": "no",
        "q1": "Separate voice and instruments",
        "q2": "Change the voice",
        "q3": "Which voice?",
        "q4": "Change the pitch of the voice?\n Female -> Male ~= -6\n Male -> Female ~= 6 |  "
    }
}

def get_answers():
    models = get_models_from_api()
    questions = [
        inquirer.List(
            "separate",
            message=texts[lang]["q1"],
            choices=[texts[lang]["yes"], texts[lang]["no"]],
            default="oui",
            carousel=True
        ),
        inquirer.List(
            "voice_cover",
            message=texts[lang]["q2"],
            choices=[texts[lang]["yes"], texts[lang]["no"]],
            default="oui",
            carousel=True
        ),
        inquirer.List(
            "model",
            message=texts[lang]["q3"],
            ignore=lambda a: a["voice_cover"] == "non",
            choices=models,
            carousel=True
        ),
        inquirer.List(
            "pitch",
            message=texts[lang]["q4"],
            ignore=lambda a: a["voice_cover"] == "non",
            choices=["-12", " -9", " -6", "  0", "  6", "  9", " 12"],
            default="  0",
            carousel=True
        ),
    ]
    res = {}
    answers = inquirer.prompt(questions)
    if (answers["separate"] == texts[lang]["yes"]):
        res["separate"] = True
    if (answers["voice_cover"] == texts[lang]["yes"]):
        model = [model for model in models if model == answers["model"]]
        res["model"] = model.pop()
        res["pitch"] = int(answers["pitch"])

    
    return res