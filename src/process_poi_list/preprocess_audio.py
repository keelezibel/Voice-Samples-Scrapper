##############################################################################################
"""
This script will ...
"""
##############################################################################################

from webbrowser import get
from pydub import AudioSegment
from glob import glob
from tqdm import tqdm

class PreProcAudio:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.audio_files = None

    def get_all_files(self):
        self.audio_files = glob(self.data_folder)

    def check_num_channels(self, wav_audio):
        """Check that audio is mono-channel and not stereo

        Args:
            wav_audio (_type_): _description_

        Returns:
            _type_: _description_
        """
        return wav_audio.set_channels(1) if wav_audio.channels != 1 else wav_audio

    def check_sr(self, wav_audio):
        return (
            wav_audio.set_frame_rate(16000)
            if wav_audio.frame_rate != 16000
            else wav_audio
        )

    def export_file(self, wav_audio, outfile):
        wav_audio.export(outfile, format="wav")

    def iterate_all_files(self):
        for file in tqdm(self.audio_files):
            wav_audio = AudioSegment.from_file(file, format="wav")
            wav_audio = self.check_num_channels(wav_audio)
            wav_audio = self.check_sr(wav_audio)
            self.export_file(wav_audio, file)

    def check_all_files(self):
        for file in tqdm(self.audio_files):
            wav_audio = AudioSegment.from_file(file, format="wav")
            if wav_audio.channels != 1 or wav_audio.frame_rate != 16000:
                print(file, wav_audio.channels, wav_audio.frame_rate)

if __name__ == "__main__":
    procObj = PreProcAudio(data_folder="/app/data/original_audio/**/*.wav")
    procObj.get_all_files()
    procObj.iterate_all_files()
    procObj.check_all_files()
    