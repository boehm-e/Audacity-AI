import subprocess
import pyaudacity as pa
import uuid
import os
import demucs.separate
import utils

questions = utils.get_answers()
print(questions)

def import_audio(pa, input_path):
    pa.do("Select: Track=0")
    pa.do("Import2: Filename={}".format(input_path))

def select_track(pa, track):
    pa.do(f"Select: Track={track}")


id = str(uuid.uuid4())
os.mkdir(id)
filename = f"{id}/{id}.mp3"

# export the selected part to mp3
pa.export(filename)

if questions.get("separate") is True:
    # separate vocals from song using demucs
    demucs.separate.main(["--mp3", "--out", id, filename])


    path = f"{os.getcwd()}/{id}/htdemucs/{id}"
    # track 1
    import_audio(pa, f"{path}/vocals.mp3")
    # track 2
    import_audio(pa, f"{path}/other.mp3")
    # track 3
    import_audio(pa, f"{path}/drums.mp3")
    # track 4
    import_audio(pa, f"{path}/bass.mp3")

    # fit tracks vertically
    pa.do("FitV:")

if questions.get("model"):

    # Mute original track
    select_track(pa, "0")
    pa.mute_tracks()

    commands = ["/home/erwan/anaconda3/envs/ai_perso/bin/python",
    "./rvc/cli.py",
    "--input_audio",
    f"{path}/vocals.mp3",
    "--speaker_id",
    "0",
    "--f0_method",
    "crepe",
    "--crepe_hop_length",
    "1",
    "--f0_up_key",
    str(questions.get("pitch", 0)),
    "--output_path",
    f"{path}/ai_generated.wav",
    "--model_path",
    questions["model"]["pth"],
    "--file_index",
    questions["model"]["index"]]

    list_files = subprocess.run(commands)

    print("The exit code was: %d" % list_files.returncode)
    print(list_files)
    import_audio(pa, f"{path}/ai_generated.wav")

    # fit tracks vertically
    pa.do("FitV:")

    # mute separated audio track
    select_track(pa, "1")
    pa.mute_tracks()
