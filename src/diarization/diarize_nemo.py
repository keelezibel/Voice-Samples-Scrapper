##############################################################################################
"""
This script will ...
"""
##############################################################################################

from email.mime import audio
import os
import json
import wget
import logging
from glob import glob
from omegaconf import OmegaConf
from nemo.collections.asr.models import ClusteringDiarizer
from nemo.collections.asr.parts.utils.speaker_utils import (
    rttm_to_labels,
    labels_to_pyannote_object,
)
from dotenv import load_dotenv

ROOT = os.getcwd()
load_dotenv()

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class DiarizeNemo:
    def __init__(self):
        self.data_dir = os.path.join(ROOT, os.getenv("DATA_FOLDER"))
        self.audio_dir = os.path.join(self.data_dir, os.getenv("ORIG_AUDIO_FOLDER"))
        self.DIARIZATION_YAML = os.getenv("NEMO_DIARIZATION_YAML")
        self.INPUT_MANIFEST_FOLDER = os.getenv("NEMO_INPUT_MANIFEST_FOLDER")
        self.DIARIZATION_OUTPUT = os.path.join(
            self.data_dir, os.getenv("DIARIZATION_FOLDER")
        )
        self.records_per_manifest = int(os.getenv("RECORDS_PER_MANIFEST"))

    def glob_all_files(self):
        audio_files_str = os.path.join(self.audio_dir, "**/*.wav")
        files = glob(audio_files_str)
        return files

    def write_manifest(self):
        filesnames_unique = {}  # Use a dict to keep track of basenames
        files = self.glob_all_files()
        input_metadata = []
        for idx, audio_f in enumerate(files):
            audio_basename = os.path.basename(audio_f)
            if audio_basename not in filesnames_unique:
                filesnames_unique[audio_basename] = os.path.dirname(audio_f)
                meta = {
                    "audio_filepath": audio_f,
                    "offset": 0,
                    "duration": None,
                    "label": "infer",
                    "text": "-",
                }
                input_metadata.append(meta)

            if idx % self.records_per_manifest == 0 and idx != 0:
                outfile = os.path.join(
                    self.INPUT_MANIFEST_FOLDER, f"input_manifest{idx}.json"
                )
                with open(outfile, "w") as fp:
                    fp.write("\n".join(map(json.dumps, input_metadata)))
                input_metadata = []

    def download_yaml(self):
        if not os.path.exists(self.DIARIZATION_YAML):
            config_url = os.getenv("TELEPHONIC_CONFIG_URL")
            self.DIARIZATION_YAML = wget.download(config_url, self.data_dir)

    def init_diarization_model(self, input_manifest):
        nemo_config = OmegaConf.load(self.DIARIZATION_YAML)
        nemo_config.diarizer.manifest_filepath = input_manifest
        nemo_config.diarizer.out_dir = (
            self.DIARIZATION_OUTPUT  # Directory to store intermediate files and prediction outputs
        )
        return nemo_config

    def diarize(self, input_manifest):
        config = self.init_diarization_model(input_manifest)
        sd_model = ClusteringDiarizer(cfg=config)
        sd_model.diarize()
        del config

    def diarize_all_manifests(self):
        input_manifest_files_str = os.path.join(self.INPUT_MANIFEST_FOLDER, "*.json")
        files = glob(input_manifest_files_str)
        for f in files:
            logging.info(f"------------------------------\n")
            logging.info(f"Processing manifest {f} now...\n")
            logging.info(f"------------------------------\n")
            self.diarize(f)


if __name__ == "__main__":
    nemoObj = DiarizeNemo()
    # nemoObj.download_yaml()
    # nemoObj.write_manifest()
    nemoObj.diarize_all_manifests()
