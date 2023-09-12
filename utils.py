import requests
import zipfile
import io
import os
from pprint import pprint
import inquirer
import requests

SERVER_URL = "http://192.168.111.131:8000"
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
        print(f"dir {path} already exists")
        pass

def separate_tracks(file_path, id):
    print("FILE PATH", file_path, id)
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
        print("separate_tracks zip_path", zip_path)
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
    print("change_voice", file_path, id, pitch, voice)
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
        print("separate_tracks zip_path", zip_path)
        # Save the ZIP content to a file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        # Unzip the downloaded file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(TEMP_FOLDER, id))
            os.remove(zip_path)
    else:
        print("Request failed with status code:", response.status_code)



def get_answers():
    models = get_models_from_api()
    questions = [
        inquirer.List(
            "separate",
            message="Séparer la voix et les instruments",
            choices=["oui", "non"],
            default="oui",
            carousel=True
        ),
        inquirer.List(
            "voice_cover",
            message="Changer la voix",
            choices=["oui", "non"],
            default="oui",
            carousel=True
        ),
        inquirer.List(
            "model",
            message="Quelle voix ?",
            ignore=lambda a: a["voice_cover"] == "non",
            choices=models,
            carousel=True
        ),
        inquirer.List(
            "pitch",
            message="Modifier le pitch de la voix ?\n Femme -> Homme ~= -6\n Homme -> Femme ~= 6 |  ",
            ignore=lambda a: a["voice_cover"] == "non",
            choices=["-12", " -9", " -6", "  0", "  6", "  9", " 12"],
            default="  0",
            carousel=True
        ),
    ]
    res = {}
    answers = inquirer.prompt(questions)
    if (answers["separate"] == "oui"):
        res["separate"] = True
    if (answers["voice_cover"] == "oui"):
        model = [model for model in models if model == answers["model"]]
        res["model"] = model.pop()
        res["pitch"] = int(answers["pitch"])

    
    return res