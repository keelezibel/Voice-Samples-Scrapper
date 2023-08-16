##############################################################################################
"""
This script will compare the audio file against the folder of reference audio

python src/compare_speaker.py --audio <filename.wav> --ref <folder_name>
"""
##############################################################################################

import os
import ffmpeg
import argparse
import datetime
import torch
from glob import glob
from pyannote.audio import Pipeline
from dotenv import load_dotenv
from pydub import AudioSegment
from statistics import mean
from speechbrain.pretrained import SpeakerRecognition

load_dotenv()

def diarize(audio_file):
    pipeline = Pipeline.from_pretrained("/models/pyannote/config.yaml")
    pipeline.to(torch.device("cuda"))
    # apply the pipeline to an audio file
    diarization_res = pipeline(audio_file)
    return diarization_res

class CompareSpeaker():
    def __init__(self):
        self.model_init()

    def model_init(self):
        self.spkr_embed_model = SpeakerRecognition.from_hparams("/models/speechbrain")

    def compare_speaker(self, ref, audio):
        score, prediction = self.spkr_embed_model.verify_files(ref, audio)
        return score.numpy()[0], prediction.numpy()[0]
    
    def extract_frame(self, in_filename, out_filename, start_timestamp, end_timestamp):
        command_str = f"ffmpeg -y -i '{in_filename}' -ss {start_timestamp} -to {end_timestamp} -ac 1 -ar 16000 '{out_filename}' -hide_banner -loglevel error"
        os.system(command=command_str)
    
    def split_hms_secs(self, timestamp):
        pt = datetime.datetime.strptime(timestamp,'%H:%M:%S.%f')
        return (pt.second + pt.minute*60 + pt.hour*3600)

    def iterate_timestamps(self, ref_audio_files, audio_file, diarization_res, resolution=5, method="max"):
        sound = AudioSegment.from_file(
            audio_file,
            format="wav",
        )

        for turn, _, _ in diarization_res.itertracks(yield_label=True):
            # segment = sound[turn.start * 1000 : turn.end * 1000]
            start_time = turn.start
            end_time = turn.end
            # Slice into segments of length == resolution
            for r in range(int(start_time), int(end_time), resolution):
                if r+resolution > end_time:
                    segment_end = end_time
                else:
                    segment_end = r + resolution    

                self.extract_frame(audio_file, f"/app/data/tmp/tmp.wav", r, segment_end)
                # Compare against all reference speeches
                score_overall = []
                for ref_audio_file in ref_audio_files:
                    score, _ = cp_spkr.compare_speaker(ref_audio_file, f"/app/data/tmp/tmp.wav")
                    score_overall.append(score)

                final_score = 0
                if method == "max":
                    final_score = max(score_overall)
                elif method == "mean":
                    final_score = mean(score_overall)

                print(f"{str(datetime.timedelta(seconds=r))} - {str(datetime.timedelta(seconds=segment_end))}, Score: {final_score}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, required=True)
    parser.add_argument("--ref", type=str, required=True)
    args = parser.parse_args()

    diarization_res = diarize(args.audio)
    
    cp_spkr = CompareSpeaker()
    ref_audio_files = glob(f"{args.ref}/*.wav")

    cp_spkr.iterate_timestamps(ref_audio_files, args.audio, diarization_res, resolution=5, method="mean")