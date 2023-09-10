import argparse
import random
import string
import os
import sys
import torch
import warnings
import traceback
import soundfile as sf
from vc_infer_pipeline import VC
from fairseq import checkpoint_utils
from scipy.io import wavfile
from my_utils import load_audio
from infer_pack.models import SynthesizerTrnMs256NSFsid, SynthesizerTrnMs256NSFsid_nono
from infer_pack.modelsv2 import SynthesizerTrnMs768NSFsid_nono, SynthesizerTrnMs768NSFsid
from multiprocessing import cpu_count
from time import sleep
import subprocess
import zipfile
from config import Config

config = Config()

now_dir = os.getcwd()
tmp = os.path.join(now_dir, "TEMP")
os.makedirs(os.path.join(now_dir, "models"), exist_ok=True)
os.makedirs(os.path.join(now_dir, "output"), exist_ok=True)
os.environ["TEMP"] = tmp
warnings.filterwarnings("ignore")
torch.manual_seed(114514)

device = config.device
print(device)
is_half = config.is_half

def load_hubert():
    global hubert_model
    models, _, _ = checkpoint_utils.load_model_ensemble_and_task(
        ["hubert_base.pt"],
        suffix="",
    )
    hubert_model = models[0]
    hubert_model = hubert_model.to(config.device)
    if is_half:
        hubert_model = hubert_model.half()
    else:
        hubert_model = hubert_model.float()
    hubert_model.eval()

def extract_model_from_zip(zip_path, output_dir):
    # Extract the folder name from the zip file path
    folder_name = os.path.splitext(os.path.basename(zip_path))[0]

    # Create a folder with the same name as the zip file inside the output directory
    output_folder = os.path.join(output_dir, folder_name)
    os.makedirs(output_folder, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if (member.endswith('.pth') and not (os.path.basename(member).startswith("G_") or os.path.basename(member).startswith("D_")) and zip_ref.getinfo(member).file_size < 200*(1024**2)) or (member.endswith('.index') and not (os.path.basename(member).startswith("trained"))):
                # Extract the file to the output folder
                zip_ref.extract(member, output_folder)

                # Move the file to the top level of the output folder
                file_path = os.path.join(output_folder, member)
                new_path = os.path.join(output_folder, os.path.basename(file_path))
                os.rename(file_path, new_path)

    print(f"Model files extracted to folder: {output_folder}")

def get_full_path(path):
    return os.path.abspath(path)

hubert_model = None

def load_vc_model(weight_root, sid):
    global n_spk, tgt_sr, net_g, vc, cpt, version
    if sid == "" or sid == []:
        global hubert_model
        if hubert_model != None:
            print("clean_empty_cache")
            del net_g, n_spk, vc, hubert_model, tgt_sr
            hubert_model = net_g = n_spk = vc = hubert_model = tgt_sr = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if_f0 = cpt.get("f0", 1)
            version = cpt.get("version", "v1")
            if version == "v1":
                if if_f0 == 1:
                    net_g = SynthesizerTrnMs256NSFsid(
                        *cpt["config"], is_half=config.is_half
                    )
                else:
                    net_g = SynthesizerTrnMs256NSFsid_nono(*cpt["config"])
            elif version == "v2":
                if if_f0 == 1:
                    net_g = SynthesizerTrnMs768NSFsid(
                        *cpt["config"], is_half=config.is_half
                    )
                else:
                    net_g = SynthesizerTrnMs768NSFsid_nono(*cpt["config"])
            del net_g, cpt
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            cpt = None
        return

    person = (weight_root)
    print("loading %s" % person)
    cpt = torch.load(person, map_location="cpu")
    tgt_sr = cpt["config"][-1]
    cpt["config"][-3] = cpt["weight"]["emb_g.weight"].shape[0]
    if_f0 = cpt.get("f0", 1)
    version = cpt.get("version", "v1")
    if version == "v1":
        if if_f0 == 1:
            net_g = SynthesizerTrnMs256NSFsid(*cpt["config"], is_half=config.is_half)
        else:
            net_g = SynthesizerTrnMs256NSFsid_nono(*cpt["config"])
    elif version == "v2":
        if if_f0 == 1:
            net_g = SynthesizerTrnMs768NSFsid(*cpt["config"], is_half=config.is_half)
        else:
            net_g = SynthesizerTrnMs768NSFsid_nono(*cpt["config"])
    del net_g.enc_q
    print(net_g.load_state_dict(cpt["weight"], strict=False))
    net_g.eval().to(config.device)
    if config.is_half:
        net_g = net_g.half()
    else:
        net_g = net_g.float()
    vc = VC(tgt_sr, config)
    n_spk = cpt["config"][-3]

def vc_single(sid, input_audio, f0_up_key, f0_file, f0_method, file_index, index_rate, crepe_hop_length, output_path=None):
    global tgt_sr, net_g, vc, hubert_model
    if input_audio is None:
        return "You need to provide an input audio file", None
    f0_up_key = int(f0_up_key)
    try:
        audio = load_audio(input_audio, 16000)
        times = [0, 0, 0]
        if hubert_model is None:
            load_hubert()
        if_f0 = cpt.get("f0", 1)
        file_index = (
            file_index.strip(" ")
            .strip('"')
            .strip("\n")
            .strip('"')
            .strip(" ")
            .replace("trained", "added")
        )
        audio_opt = vc.pipeline(
            hubert_model,
            net_g,
            sid,
            audio,
            times,
            f0_up_key,
            f0_method,
            file_index,
            index_rate,
            if_f0,
            version,
            crepe_hop_length,
            None,
        )
        print(
            "total_cost_time %dms, p512 %.2f, d512 %.2f, f %.2f"
            % (times[0], times[1], times[2], len(audio) / times[0])
        )
        output_wav_path = output_path or os.path.join(
            config.output_dir, f"{file_index.replace('index', 'syn')}.wav"
        )
        sf.write(output_wav_path, audio_opt, tgt_sr)
        return "Success", output_wav_path
    except Exception as e:
        print(e)
        return "An error occurred during the conversion process", None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VC-Convertor")
    parser.add_argument("--input_audio", type=str, help="Input audio file path", required=True)
    parser.add_argument("--speaker_id", type=int, default=0, help="Speaker ID")
    parser.add_argument("--f0_up_key", type=int, default=1, help="F0 up key")
    parser.add_argument("--f0_method", type=str, default="my", help="F0 method")
    parser.add_argument("--f0_file", type=str, default=None, help="F0 file")
    parser.add_argument("--output_path", type=str, default=None, help="Output audio file path")
    parser.add_argument("--index_rate", type=float, default=0.05, help="Index rate")
    parser.add_argument("--crepe_hop_length", type=float, default=0.1, help="Crepe hop length")
    parser.add_argument("--model_path", type=str, help="Crepe hop length")
    parser.add_argument("--file_index", type=str, help="File model index")
    parser.add_argument("--use_gfloat", action="store_true", help="Use Google Colab float model")

    args = parser.parse_args()

    print("VC-Convertor")

    sid = args.speaker_id
    f0_up_key = args.f0_up_key
    f0_method = args.f0_method
    f0_file = args.f0_file
    input_audio = args.input_audio
    output_path = args.output_path
    file_index = args.file_index

    # Check if the specified model exists, if not, extract it from the zip file
    if not os.path.exists(args.model_path):
        zip_path = config.zip_path
        if os.path.exists(zip_path):
            extract_model_from_zip(zip_path, os.path.dirname(args.model_path))
        else:
            print(f"Model file '{args.model_path}' does not exist.")
            sys.exit(1)

    # Load the VC model
    load_vc_model(args.model_path, sid)

    crepe_hop_length = round((args.crepe_hop_length) * 64)

    # Perform VC conversion
    result, output_wav_path = vc_single(
        sid, input_audio, f0_up_key, f0_file, f0_method, file_index, args.index_rate, crepe_hop_length, output_path
    )
    print(result)
