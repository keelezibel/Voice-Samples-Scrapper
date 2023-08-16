##############################################################################################
"""
This script will diarize the audios and compare against ref segment

python src/diarize.py --file poi_list.csv
"""
##############################################################################################

import os
import re
import ast
import time
import torch
import argparse
import pydub
import shutil
import ffmpeg
import datetime
from tqdm import tqdm
import pandas as pd
from glob import glob
from speechbrain.pretrained import SpeakerRecognition
from pyannote.audio import Pipeline, Audio
from pyannote.core import Segment
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.utils import make_chunks
from deepface import DeepFace


load_dotenv()


class Diarization:
    def __init__(self, poi_filename):
        self.poi_filename = poi_filename
        self.spkr_embed_model = None
        self.audio_reader = None
        self.pipeline = None
        self.export_video = os.getenv("EXPORT_VIDEO_FLAG")
        self.diarization_folder = os.path.join(
            os.getenv("DATA_FOLDER"), os.getenv("DIARIZATION_FOLDER")
        )
        self.min_seg_len = float(os.getenv("MIN_SEGMENT_LEN"))
        self.max_seg_len = float(os.getenv("MAX_SEGMENT_LEN"))

        self.model_init()
        self.read_poi_file()

        self.video_folder = os.path.join(
            os.getenv("DATA_FOLDER"), os.getenv("VIDEO_FOLDER")
        )

    def model_init(self):
        self.spkr_embed_model = SpeakerRecognition.from_hparams("/models/speechbrain")
        self.pipeline = Pipeline.from_pretrained("/models/pyannote/config.yaml")
        self.pipeline.to(torch.device("cuda"))

    def read_poi_file(self):
        """Read in the CSV file"""
        self.df = pd.read_csv(self.poi_filename)

    def compare_speaker(self, ref, audio):
        score, prediction = self.spkr_embed_model.verify_files(ref, audio)
        return score.numpy()[0], prediction.numpy()[0]

    def verify_face(
        self,
        img1_path,
        img2_path,
        model_name: str,
        distance_metric: str,
        detector_backend: str,
    ):
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name=model_name,
            distance_metric=distance_metric,
            detector_backend=detector_backend,
        )
        return result["verified"]

    def extract_frame(self, in_filename, out_filename, timestamp):
        stream = ffmpeg.input(in_filename, ss=timestamp)
        stream = stream.output(out_filename, frames=1)
        stream.compile()
        stream.run(overwrite_output=True, quiet=True)

    def extract_video_segment(self, in_filename, out_filename, start_timestamp, end_timestamp):
        stream = ffmpeg.input(in_filename, ss=start_timestamp, to=end_timestamp)
        stream = stream.output(out_filename)
        stream.compile()
        stream.run(overwrite_output=True, quiet=True)

    def diarize(self, name):
        video_path = os.path.join(os.getenv("DATA_FOLDER"), os.getenv("VIDEO_FOLDER"))
        poi_video_path = f"{os.path.join(video_path, name)}/*.wav"
        wav_files = glob(poi_video_path)

        ref_path = os.path.join(
            os.getenv("REF_AUDIO_DIR"),
            f"{name}/*.wav",
        )
        ref = glob(ref_path)[0]
        ref_image_format = os.getenv("DEFAULT_REF_IMAGE_FORMAT")
        ref_face = os.path.join(
            os.getenv("REF_IMAGES_DIR"),
            f"{name}.{ref_image_format}",
        )

        tmpfolder = os.getenv("TMP_FOLDER")
        for file in tqdm(wav_files):
            diarization = self.pipeline(file)

            sound = AudioSegment.from_file(
                file,
                format="wav",
            )

            wav_name = os.path.basename(file)
            wav_name_no_ext = wav_name.split(".")[0]

            orig_video_file = os.path.join(
                self.video_folder,
                f"{name}/{wav_name_no_ext}.mp4",
            )

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if float(turn.end) - float(turn.start) >= self.min_seg_len:
                    segment = sound[turn.start * 1000 : turn.end * 1000]
                    outfile = f"{self.diarization_folder}/{name}/{wav_name_no_ext}_{turn.start}_{turn.end}.wav"
                    tmpfile = (
                        f"{tmpfolder}/{wav_name_no_ext}_{turn.start}_{turn.end}.wav"
                    )
                    segment.export(tmpfile, format="wav")

                    # Speaker Verification
                    score, voice_prediction = self.compare_speaker(ref, tmpfile)
                    # Face Verification
                    ref_image_format = os.getenv("DEFAULT_REF_IMAGE_FORMAT")
                    tmpfile_img = f"{tmpfolder}/{name}_{turn.start}_{turn.end}.{ref_image_format}"
                    timestamp = datetime.timedelta(seconds=(turn.end + turn.start) / 2)

                    self.extract_frame(orig_video_file, tmpfile_img, timestamp)

                    try:
                        face_prediction = self.verify_face(
                            ref_face,
                            tmpfile_img,
                            model_name="Facenet",
                            distance_metric="cosine",
                            detector_backend="mtcnn"
                        )
                    except Exception as e:
                        face_prediction = False

                    print(f"{str(datetime.timedelta(seconds=turn.start))} - {str(datetime.timedelta(seconds=turn.end))}, VoiceScore: {score}, Face: {face_prediction}")
                    if (
                        score >= float(os.getenv("VOICE_THRESHOLD"))
                        and voice_prediction
                        and face_prediction
                    ):
                        # Slice audio into multiple segments if exceed max length
                        if float(turn.end) - float(turn.start) >= self.max_seg_len:
                            chunks = make_chunks(
                                segment, self.min_seg_len * 1000
                            )  # Make chunks
                            for i, chunk in enumerate(chunks):
                                chunk_name = f"{self.diarization_folder}/{name}/{wav_name_no_ext}_{turn.start}_{turn.end}_{i}.wav"
                                chunk.export(chunk_name, format="wav")
                                # Export video segment as well
                                if self.export_video == "true":
                                    out_filename = f"{self.diarization_folder}/{name}/{wav_name_no_ext}_{turn.start}_{turn.end}_{i}.mp4"
                                    self.extract_video_segment(orig_video_file, out_filename, turn.start, turn.end)
                            os.remove(tmpfile)
                        else:
                            # Export video segment as well
                            if self.export_video == "true":
                                out_filename = f"{self.diarization_folder}/{name}/{wav_name_no_ext}_{turn.start}_{turn.end}.mp4"
                                self.extract_video_segment(orig_video_file, out_filename, turn.start, turn.end)
                            shutil.move(tmpfile, outfile)
                    else:
                        os.remove(tmpfile)
                    os.remove(tmpfile_img)

    def create_directory(self, name):
        """Create target folder to store audio clips for each name

        Args:
            name (str): Name of each POI
        """
        target_video_dir = os.path.join(self.diarization_folder, name)
        if os.path.exists(target_video_dir):  # If directory exists, dont do anything
            return False
        os.makedirs(target_video_dir, exist_ok=True)
        return True

    def process_pois(self):
        self.read_poi_file()
        for _, row in tqdm(self.df.iterrows(), total=self.df.shape[0]):
            # Parse string as list
            name = row["Name"]
            name = re.sub(
                r"[^A-Za-z0-9 ]+", "", name
            )  # Strip special characters from name

            new_poi_flag = self.create_directory(name)  # Create folder for each POI
            if new_poi_flag:
                self.diarize(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()

    poi_filename = os.path.join(os.getenv("POI_FOLDER"), args.file)
    clsObj = Diarization(poi_filename)
    diarizaton_res = clsObj.process_pois()
