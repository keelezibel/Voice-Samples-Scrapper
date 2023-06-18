# How to use this repo

This code base will pull people information from the various parliament sites.

## Repo Structure

**_cache_** This folder contains the cached html text for the various sites so that we dont keep making requests to the sites

**_data_** This folder contains the csv data for each COI

**_.env_** This file contains the URL to the sites

```
📦POI Scrapper
 ┣ 📂cache
 ┃ ┣ 📜html.txt
 ┣ 📂data
 ┃ ┣ 📂diarization
 ┃ ┃ ┣ 📂input_manifest
 ┃ ┃ ┣ 📂pred_rttms
 ┃ ┃ ┣ 📂speaker_outputs
 ┃ ┃ ┣ 📂vad_outputs
 ┃ ┃ ┗ 📜diar_infer_telephonic.yaml
 ┃ ┣ 📂original_audio
 ┃ ┣ 📂spkr_list
 ┃ ┃ ┣ 📜spkrs_autogen.csv
 ┃ ┃ ┣ 📜spkrs_manual.csv
 ┃ ┃ ┣ 📜spkrs_withurls.csv
 ┃ ┣ 📂processed_audio
 ┃ ┣ 📂ref_audio
 ┃ ┃ ┗ 📜ref_audios.csv
 ┃ ┗ 📂tmp
 ┣ 📂models
 ┃ ┣ 📂sb_ecapa_pretrained
 ┃ ┣ 📜titanet-large.nemo
 ┃ ┗ 📜vad_telephony_marblenet.nemo
 ┣ 📂src
 ┃ ┣ 📂diarization
 ┃ ┣ 📂generate_spkr_segments
 ┃ ┣ 📂process_poi_list
```

## Usage
### Step 1: Prepare POI CSV put into `data/poi_list`
```
<POI Name 1>
<POI Name 2>
```

### Step 2: Get Video Links for each URL (Based on YT)
```python
python src/process_poi_list_video_link_scrapper.py --file <poi_list.csv>
```



## Installation Issues 
```
OpenCV
pip uninstall opencv-python
pip uninstall opencv-contrib-python
pip uninstall opencv-contrib-python-headless

pip install opencv-contrib-python==4.5.5.64
```