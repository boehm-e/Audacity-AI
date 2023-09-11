import json
import subprocess
import pyaudacity as pa
import uuid
import os
import demucs.separate
import utils

# python = "/home/erwan/anaconda3/envs/ai_perso/bin/python"
python = "python"

questions = utils.get_answers()
print(questions)

def import_audio(input_path, name=None):
    pa.do("Select: Track=0")
    pa.do(f"Import2: Filename={input_path}")
    if name:
        pa.do(f"SetTrackStatus: Name={name}")

def get_tracks():
    tracks = pa.do("GetInfo: Type=Tracks Format=JSON").replace("BatchCommand finished: OK", "")
    return json.loads(tracks)


def get_track_by_name(name):
    tracks = get_tracks()
    for i, track in enumerate(tracks):
        if track.get("name") == name:
            return str(i)
    return False

# def get_track_by_index(idx):
#     tracks = get_tracks()
#     return tracks[idx].get("name")
#     for i, track in enumerate(tracks):
#         if track.get("name") == name:
#             return str(i)
#     return False

def select_track(track):
    pa.do(f"Select: Track={track}")




id = str(uuid.uuid4())
id_short = id[:5]
os.mkdir(id)
filename = os.path.join(os.getcwd(), id, f"{id}.mp3")

# export the selected part to mp3
pa.export(filename)

if questions.get("separate") is True:
    # separate vocals from song using demucs
    demucs.separate.main(["--mp3", "--out", id, filename])


    path = os.path.join(os.getcwd(), id, 'htdemucs', id)
    # importe voice
    voice_label = f"voix-{id_short}"
    import_audio(os.path.join(path, "vocals.mp3"), voice_label)
    pa.do("Align_StartToSelStart:")

    # import other
    other_label = f"autres-{id_short}"
    import_audio(os.path.join(path, "other.mp3"), other_label)
    pa.do("Align_StartToSelStart:")

    # import drums
    drums_label = f"batterie-{id_short}"
    import_audio(os.path.join(path, "drums.mp3"), drums_label)
    pa.do("Align_StartToSelStart:")

    # import bass
    bass_label = f"bass-{id_short}"
    import_audio(os.path.join(path, "bass.mp3"), bass_label)
    pa.do("Align_StartToSelStart:")

    # fit tracks vertically
    pa.do("FitV:")

if questions.get("model"):
    model_name = questions.get("model",{}).get("name", "")
    if questions.get("separate", False) is True:
        # Mute original track
        select_track("0")
        pa.mute_tracks()

        commands = [python, os.path.join(os.getcwd(), "rvc", "cli.py"), "--input_audio", os.path.join(path, "vocals.mp3"), "--speaker_id", "0", "--f0_method", "crepe", "--crepe_hop_length", "1", "--f0_up_key", str(questions.get("pitch", 0)), "--output_path", os.path.join(path, "ai_generated.wav"), "--model_path", questions["model"]["pth"], "--file_index", questions["model"]["index"]]
        list_files = subprocess.run(commands)

        print("The exit code was: %d" % list_files.returncode)
        print(list_files)
        import_audio(os.path.join(path, "ai_generated.wav"), f"voix_ai_{model_name}-{id_short}")
        pa.do("Align_StartToSelStart:")

        # fit tracks vertically
        pa.do("FitV:")

        # mute separated audio track
        select_track(get_track_by_name(voice_label))
        pa.mute_tracks()
    # else:
    #     pa.export(filename)

