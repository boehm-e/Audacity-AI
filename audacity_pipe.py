import json
import pyaudacity as pa
import uuid
import os
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

def select_track(track):
    pa.do(f"Select: Track={track}")

id = str(uuid.uuid4())[:5]

utils.mkdir(os.path.join(utils.TEMP_FOLDER, id))
filename = os.path.join(utils.TEMP_FOLDER, id, f"{id}.mp3")

# export the selected part to mp3
pa.export(filename)

print("EXPORT", filename)


if questions.get("separate") is True:
    # separate vocals from song using demucs
    utils.separate_tracks(filename, id)

    separated_song_folder = os.path.join(utils.TEMP_FOLDER, id)
    # importe voice
    voice_label = f"voix-{id}"
    import_audio(os.path.join(separated_song_folder, "vocals.wav"), voice_label)
    pa.do("Align_StartToSelStart:")

    # import other
    other_label = f"autres-{id}"
    import_audio(os.path.join(separated_song_folder, "other.wav"), other_label)
    pa.do("Align_StartToSelStart:")

    # import drums
    drums_label = f"batterie-{id}"
    import_audio(os.path.join(separated_song_folder, "drums.wav"), drums_label)
    pa.do("Align_StartToSelStart:")

    # import bass
    bass_label = f"bass-{id}"
    import_audio(os.path.join(separated_song_folder, "bass.wav"), bass_label)
    pa.do("Align_StartToSelStart:")

    # remove files after import
    # os.remove(os.path.join(separated_song_folder, "vocals.wav"))
    # os.remove(os.path.join(separated_song_folder, "other.wav"))
    # os.remove(os.path.join(separated_song_folder, "drums.wav"))
    # os.remove(os.path.join(separated_song_folder, "bass.wav"))
    # os.removedirs(separated_song_folder)


    # fit tracks vertically
    pa.do("FitV:")

if questions.get("model"):
    model_name = questions.get("model")
    if questions.get("separate", False) is True:
        # Mute original track
        select_track("0")
        pa.mute_tracks()
        print("QUESTIONS", questions)
        utils.change_voice(os.path.join(separated_song_folder, "vocals.wav"), id, str(questions.get("pitch", 0)), questions["model"])

        import_audio(os.path.join(utils.TEMP_FOLDER, id, "aivoice.wav"), f"voix_ai_{model_name}-{id}")
        pa.do("Align_StartToSelStart:")

        # fit tracks vertically
        pa.do("FitV:")

        # mute separated audio track
        select_track(get_track_by_name(voice_label))
        pa.mute_tracks()
    # else:
    #     pa.export(filename)

