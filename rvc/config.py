import argparse
import glob
import sys
import torch
from multiprocessing import cpu_count


class Config:
    def __init__(self):
        self.device = "cuda:0"
        # self.device = "cpu:0"
        self.is_half = False
        self.n_cpu = 0
        self.gpu_name = None
        self.gpu_mem = None
        (
            self.python_cmd,
            self.listen_port,
            self.iscolab,
            self.noparallel,
            self.noautoopen,
            self.use_gfloat,
            self.paperspace,
        ) = self.arg_parse()
        
        if self.use_gfloat: 
            print("Using g_float instead of g_half")
            self.is_half = False
        self.x_pad, self.x_query, self.x_center, self.x_max = self.device_config()

    def arg_parse(self) -> tuple:
        parser = argparse.ArgumentParser()

        parser.add_argument("--input_audio", type=str, help="Input audio file path")
        parser.add_argument("--speaker_id", type=int, default=0, help="Speaker ID")
        parser.add_argument("--f0_up_key", type=int, default=1, help="F0 up key")
        parser.add_argument("--f0_method", type=str, default="my", help="F0 method")
        parser.add_argument("--f0_file", type=str, default="input.f0", help="F0 file")
        parser.add_argument("--output_path", type=str, default=None, help="Output audio file path")
        parser.add_argument("--index_rate", type=float, default=0.05, help="Index rate")
        parser.add_argument("--crepe_hop_length", type=float, default=0.1, help="Crepe hop length")
        parser.add_argument("--port", type=int, default=5000, help="Port for serving the model")
        parser.add_argument("--pycmd", type=str, default="python3", help="Python command")
        parser.add_argument("--colab", action="store_true", help="Running on Google Colab")
        parser.add_argument("--noparallel", action="store_true", help="Disable parallel processing")
        parser.add_argument("--noautoopen", action="store_true", help="Do not open the web browser automatically")
        parser.add_argument("--use_gfloat", action="store_true", help="Use Google Colab float model")
        parser.add_argument("--paperspace", action="store_true", help="Running on Paperspace")
        parser.add_argument("--model_path", type=str, help="Crepe hop length")
        parser.add_argument("--file_index", type=str, help="File model index")



        # parser.add_argument("--port", type=int, default=7865, help="Listen port")
        # parser.add_argument(
        #     "--pycmd", type=str, default="python", help="Python command"
        # )
        # parser.add_argument("--colab", action="store_true", help="Launch in colab")
        # parser.add_argument(
        #     "--noparallel", action="store_true", help="Disable parallel processing"
        # )
        # parser.add_argument(
        #     "--noautoopen",
        #     action="store_true",
        #     help="Do not open in browser automatically",
        # )
        # parser.add_argument( # this argument (if set to false) allows windows users to avoid the "slow_conv2d_cpu not implemented for 'Half'" exception
        #     "--use_gfloat", action="store_true", help="Will use g_float instead of g_half during voice conversion."
        # )
        # parser.add_argument( # Fork Feature. Paperspace integration for web UI
        #     "--paperspace", action="store_true", help="Note that this argument just shares a gradio link for the web UI. Thus can be used on other non-local CLI systems."
        # )
        cmd_opts = parser.parse_args()

        cmd_opts.port = cmd_opts.port if 0 <= cmd_opts.port <= 65535 else 7865

        return (
            cmd_opts.pycmd,
            cmd_opts.port,
            cmd_opts.colab,
            cmd_opts.noparallel,
            cmd_opts.noautoopen,
            cmd_opts.use_gfloat,
            cmd_opts.paperspace,
        )

    def device_config(self) -> tuple:
        if torch.cuda.is_available():
            i_device = int(self.device.split(":")[-1])
            self.gpu_name = torch.cuda.get_device_name(i_device)
            if (
                ("16" in self.gpu_name and "V100" not in self.gpu_name.upper())
                or "P40" in self.gpu_name.upper()
                or "1060" in self.gpu_name
                or "1070" in self.gpu_name
                or "1080" in self.gpu_name
            ):
                print("16系/10系显卡和P40强制单精度")
                self.is_half = False
                with open("trainset_preprocess_pipeline_print.py", "r") as f:
                    strr = f.read().replace("3.7", "3.0")
                with open("trainset_preprocess_pipeline_print.py", "w") as f:
                    f.write(strr)
            else:
                self.gpu_name = None
            self.gpu_mem = int(
                torch.cuda.get_device_properties(i_device).total_memory
                / 1024
                / 1024
                / 1024
                + 0.4
            )
            if self.gpu_mem <= 4:
                with open("trainset_preprocess_pipeline_print.py", "r") as f:
                    strr = f.read().replace("3.7", "3.0")
                with open("trainset_preprocess_pipeline_print.py", "w") as f:
                    f.write(strr)
        elif torch.backends.mps.is_available():
            print("No supported Nvidia cards found, using MPS for inference ")
            self.device = "mps"
        else:
            print("No supported Nvidia cards found, using CPU for inference")
            self.device = "cpu"
            if not self.use_gfloat: # Fork Feature: Force g_float (is_half = False) if --use_gfloat arg is used. 
                self.is_half = False

        if self.n_cpu == 0:
            self.n_cpu = cpu_count()

        if self.is_half:
            # 6G显存配置
            x_pad = 3
            x_query = 10
            x_center = 60
            x_max = 65
        else:
            # 5G显存配置
            x_pad = 1
            x_query = 6
            x_center = 38
            x_max = 41

        if self.gpu_mem != None and self.gpu_mem <= 4:
            x_pad = 1
            x_query = 5
            x_center = 30
            x_max = 32

        return x_pad, x_query, x_center, x_max
