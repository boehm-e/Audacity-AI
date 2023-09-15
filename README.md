# Audacity AI

## Overview
This Python project utilizes the [Demucs](https://github.com/facebookresearch/demucs) library for voice separation and Retrieval-based Voice Conversion ([RVC](https://github.com/RVC-Project/)) techniques to achieve two primary objectives:

1. Voice Separation: It aims to separate vocals from instrumental audio tracks within Audacity audio clips. The project leverages the power of [Demucs](https://github.com/facebookresearch/demucs), a state-of-the-art source separation model, to cleanly isolate the human voice from the accompanying instruments.

2. Voice Conversion: Once the vocals are extracted, this project employs Retrieval-based Voice Conversion ([RVC](https://github.com/RVC-Project/)) technology to transform the original voice into another voice.

## Audacity integration

The project seamlessly interfaces with Audacity using [mod-script-pipe](https://manual.audacityteam.org/man/scripting.html), allowing for easy processing of audio clips directly within the Audacity environment.

## Demo
![](./demo.gif)

## Decoupled Processing

I've chosen to separate the processing part of the project from the Audacity communication into two distinct scripts for practical reasons. By doing this, it allows us to:

1. Optimize Resource Usage: I can run the processing server on a high-performance machine equipped with a GPU, ensuring efficient and speedy voice separation and conversion tasks.

2. Decouple Audacity Work: Simultaneously, Audacity can be run on a less powerful machine since it primarily handles communication tasks. This separation of responsibilities enables us to utilize resources more effectively, ensuring that both the audio editing and processing tasks can be performed efficiently.


## Installation

Downlaod [hubert_base.pt](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt/) and place it in the root folder

```bash
pip install -r requirements.txt
```

**mod-script-pipe** : This script will communicate with Audacity using mod-script-pipe. So you need to enable it. To do that:
1. Open Audacity's preferences (`ctrl+P` or `Edit --> Preferences`)
2. In Modules tab, select `Enabled` for `mod-script-pipe`

## Adding voice models
1. Voice models should be inside the `models/` folder
2. Each voice model consists of a Folder, which will be used as the name of the model.
3. Each voice model folder should contain a `.pth` and `.index` file

## Usage
1. Import an audio clip into Audacity (It must be the first clip).
2. Select the audio range you want to edit
3. Start the server by running the following command : `python server.py` 
4. Start the client by running the following command : `python index.py`
5. The `index.py` file will guide you through the process.

# Offloading the computation to another computer (server,...)

You can offload computation to a dedicated server. Follow these steps:

**Server**: Install and run this project on your powerfull server (with CUDA enabled GPU).

**Client Configuration**: On your Audacity machine, edit the SERVER_URL in `utils.py` to match the server's IP or hostname.

**File Transfer**: Note that communication between the client and server will involve transferring audio files zipped using FastAPI.


This setup optimizes performance by leveraging high-end resources for tasks like voice separation and conversion while maintaining seamless communication with Audacity on a less powerful system.
