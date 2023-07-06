# Purpose of this repository

Isn't it a pain to collect audio data of specific speakers for enrollment? Look no further, this repo will help you collect audio samples for your list of interested speakers.

Libraries:
- Pyannote (for diarization)
- DeepFace (for face recognition)
- SpeechBrain (for speaker recognition)


### Step 0: Download [models](https://drive.google.com/file/d/1Nipli4nTcdCjQz2tblI-bQ25b3xHdOs6/view?usp=sharing) and copy to `models`

### Step 1: `docker-compose up -d`

### Step 2: Prepare POI CSV put into `data/poi_list/poi_list.csv`
```
<POI Name 1>
<POI Name 2>
```

### Step 3: Get Video Links for each URL (Based on YT)
```python
python src/video_link_scrapper.py --file poi_list.csv
```

### Step 4: Get Video for each URL (Based on YT)
```python
python src/video_scrapper.py --file poi_list_withurls.csv
```

### Step 5: Prepare reference audio CSV put into `data/ref_audio/ref_audio.csv`
```python
python src/download_ref_segments.py
```

### Step 6: Prepare reference image and put into `data/ref_images/*`
- All images name must match the names in `data/poi_list/poi_list.csv`
- Make sure all images are the same format (e.g. jpg, png etc.) and update `DEFAULT_REF_IMAGE_FORMAT` in `.env` file.


### Step 7: Diarize
```python
python src/diarize.py --file poi_list.csv
```

## Repo Structure

```
📦Voice Scrapper
    📦data
    ┣ 📂diarization
    ┣ 📂poi_list
    ┃ ┣ 📜poi_list.csv
    ┃ ┗ 📜poi_list_withurls.csv
    ┣ 📂ref_audio
    ┃ ┗ 📜ref_audios.csv
    ┣ 📂ref_images
    ┗ 📂tmp
    📦models
    ┣ 📂.deepface
    ┃ ┗ 📂weights
    ┃ ┃ ┣ 📜dlib_face_recognition_resnet_model_v1.dat
    ┃ ┃ ┣ 📜facenet512_weights.h5
    ┃ ┃ ┗ 📜shape_predictor_5_face_landmarks.dat
    ┣ 📂pyannote
    ┃ ┣ 📜config.yaml
    ┃ ┣ 📜segmentation_model_pyannote.bin
    ┃ ┗ 📜segmentation_model_pyannote_backup.bin
    ┗ 📂speechbrain
    ┃ ┣ 📜classifier.ckpt
    ┃ ┣ 📜embedding_model.ckpt
    ┃ ┣ 📜hyperparams.yaml
    ┃ ┣ 📜label_encoder.txt
    ┃ ┗ 📜mean_var_norm_emb.ckpt
    📦src
    ┣ 📜diarize.py
    ┣ 📜download_ref_segments.py
    ┣ 📜video_link_scrapper.py
    ┗ 📜video_scrapper.py
    .dockerignore
    .env
    .gitignore
    docker-compose.yaml
    Dockerfile
    README.md
    requirements.txt
```

## Installation Issues 
```
OpenCV
pip uninstall opencv-python
pip uninstall opencv-contrib-python
pip uninstall opencv-contrib-python-headless

pip install opencv-contrib-python==4.5.5.64
```