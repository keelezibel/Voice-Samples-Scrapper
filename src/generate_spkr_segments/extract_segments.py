##############################################################################################
"""
This script will read the CSV containing the POIs, compare the original audio against the reference audio.
If same speaker, write to the POI destination folder
"""
##############################################################################################

from enum import unique
import os
import re
import ast
import shutil
import numpy as np
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from glob import glob
from pydub import AudioSegment
from speechbrain.pretrained import SpeakerRecognition
import torchaudio

load_dotenv()

verification = SpeakerRecognition.from_hparams(
    source="/app/models/sb_ecapa_pretrained",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
)


class ProcessPOISegments:
    def __init__(
        self, poi_filename, original_audio_dir, diarization_dir, dst_audio_dir
    ):
        """Initialize a class to scrape the actual videos

        Args:
            poi_filename (str): filepath to the csv with URLs
            original_audio_dir (str): Directory to store the audio files
            diarization_dir (str): Diarization output
            dst_audio_dir (str): POI segments
        """
        self.poi_filename = poi_filename
        self.original_audio_dir = original_audio_dir
        self.diarization_dir = diarization_dir
        self.dst_audio_dir = dst_audio_dir
        self.df = None

        self.read_poi_file()

    def read_poi_file(self):
        """Read in the CSV file"""
        self.df = pd.read_csv(self.poi_filename)

    def grab_orig_audio_poi(self, poi):
        """Generate list of filenames related to POI

        Args:
            poi (str): Name of POI

        Returns:
            [list]: List of filenames (w/o ext) related to POI
        """
        audio_dir = os.path.join(self.original_audio_dir, f"{poi}/*.wav")
        files = glob(audio_dir)
        # Grab filename
        basenames = [
            os.path.basename(f).split(".")[0] for f in files
        ]  # Get basenames without .ext

        return basenames

    def save_segments(self, poi_name, tmp_file):
        dst_folder = os.path.join(self.dst_audio_dir, poi_name)
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        try:
            shutil.move(tmp_file, dst_folder)
            print(f"Copied {tmp_file} to {dst_folder}")
        # If source and destination are same
        except shutil.SameFileError:
            print("Source and destination represents the same file.")
        # If there is any permission issue
        except PermissionError:
            print("Permission denied.")
        # For other errors
        except Exception as e:
            print(e)

    def read_rttm(self, filename, poi_name):
        df = pd.read_csv(
            filename,
            delim_whitespace=True,
            names=[
                "Type",
                "FileID",
                "ChannelID",
                "Start",
                "Duration",
                "OrthField",
                "SpkrType",
                "SpkrName",
                "Conf",
                "LookaheadTime",
            ],
            header=None,
        )

        unique_speakers = set(df["SpkrName"].tolist())
        # Extract audio samples for each unique speaker
        ref_audio_dir = os.path.join(os.getenv("REF_AUDIO_DIR"), poi_name) + "/*.wav"
        ref_audio = glob(ref_audio_dir)
        if len(ref_audio) == 0:
            return
        ref_audio = ref_audio[0]

        same_spkrs = []
        for spkr in unique_speakers:
            spkr_series = df[df["SpkrName"] == spkr].iloc[0, :]

            audio_wav = AudioSegment.from_wav(
                os.path.join(original_audio_dir, poi_name)
                + f"/{spkr_series.FileID}.wav"
            )
            # Change time(s) to time(ms)
            start_ms = spkr_series.Start * 1000
            end_ms = (spkr_series.Start + spkr_series.Duration) * 1000
            fileID = spkr_series.FileID
            outfile = self.segment_audio(start_ms, end_ms, poi_name, fileID, 0)

            same_spkr_flag = self.compare_spkr(ref_audio, outfile)
            if same_spkr_flag:
                same_spkrs.append(spkr)

            # Clean up file
            os.remove(outfile)

        # Copy files from same speakers into POI folder
        for spkr in same_spkrs:
            spkr_series = df[df["SpkrName"] == spkr]
            for idx, row in spkr_series.iterrows():
                if row["Duration"] < 5:
                    continue

                start_ms = row["Start"] * 1000
                end_ms = (row["Start"] + row["Duration"]) * 1000
                fileID = row["FileID"]
                outfile = self.segment_audio(start_ms, end_ms, poi_name, fileID, idx)

                self.save_segments(poi_name, outfile)

    def segment_audio(self, start_ms, end_ms, poi_name, fileID, idx):
        audio_wav = AudioSegment.from_wav(
            os.path.join(original_audio_dir, poi_name) + f"/{fileID}.wav"
        )
        segmented_audio = audio_wav[start_ms:end_ms]
        outfile = os.path.join(os.getenv("TMP_FOLDER"), fileID) + f"_{idx}.wav"
        segmented_audio.export(outfile, format="wav")

        return outfile

    def compare_spkr(self, ref_audio, audio):
        _, prediction = verification.verify_files(ref_audio, audio)
        return np.array(prediction)[0]

    def iterate_poi(self):
        """Iterate through each name and download videos into each speaker folder"""
        for _, row in tqdm(self.df.iterrows()):
            # Parse string as list
            name = row["Name"]
            name = re.sub(
                r"[^A-Za-z0-9 ]+", "", name
            )  # Strip special characters from name
            url = row["Urls"]

            if url != "":
                basenames = self.grab_orig_audio_poi(name)
                for file in basenames:
                    # Read RTTM
                    rttm_path = os.path.join(self.diarization_dir, f"{file}.rttm")
                    if os.path.isfile(rttm_path):
                        self.read_rttm(rttm_path, name)


if __name__ == "__main__":
    poi_filename = os.getenv("REF_AUDIO_CSV")
    dst_audio_dir = os.getenv("SPKR_AUDIO_SEGMENTS_DIR")
    diarization_dir = os.getenv("NEMO_PRED_RTTM_FOLDER")
    original_audio_dir = os.path.join(
        os.getenv("DATA_FOLDER"), os.getenv("ORIG_AUDIO_FOLDER")
    )
    clsObj = ProcessPOISegments(
        poi_filename, original_audio_dir, diarization_dir, dst_audio_dir
    )
    clsObj.iterate_poi()
