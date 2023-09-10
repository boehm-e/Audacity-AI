import os
from pprint import pprint
import inquirer

def get_answers():
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
    # print(models)

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
            choices=[model["name"] for model in models],
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
        model = [model for model in models if model["name"] == answers["model"]]
        res["model"] = model.pop()
        res["pitch"] = int(answers["pitch"])

    
    return res