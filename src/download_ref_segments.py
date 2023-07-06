##############################################################################################
"""
This script will read the CSV containing the POIs reference audio urls and download the relevant
segments as reference audios.

python src/download_ref_segments.py
"""
##############################################################################################

import os
import re
import ast
import pandas as pd
from tqdm import tqdm
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
from dotenv import load_dotenv

load_dotenv()


class YTLogger:
    def debug(self):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        pass

    def info(self):
        pass

    def warning(self):
        pass

    def error(self):
        pass


class RefVideoScrapper:
    def __init__(self, poi_filename, audio_dir):
        """Initialize a class to scrape the actual videos

        Args:
            poi_filename (str): filepath to the csv with URLs
            audio_dir(str): Directory to store the audio files
        """
        self.poi_filename = poi_filename
        self.df = None
        self.audio_dir = audio_dir

        self.read_poi_file()

    def read_poi_file(self):
        """Read in the CSV file"""
        self.df = pd.read_csv(self.poi_filename)

    def download_videos(self, url, name, start, end):
        """Specify the yt-dlp parameters

        Args:
            url (str): URL to retrieve videl
            name (str): speaker name
        """
        ydl_opts = {
            "format": "m4a/bestaudio/best",
            "download_ranges": download_range_func([], [(start, end)]),
            "postprocessors": [
                {  # Extract audio using ffmpeg
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
            "outtmpl": f"{self.audio_dir}/{name}/%(id)s.%(ext)s",
            "logger": YTLogger,
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)

    def iterate_poi(self):
        """Iterate through each name and download videos into each speaker folder"""
        for _, row in tqdm(self.df.iterrows()):
            # Parse string as list
            name = row["Name"]
            name = re.sub(
                r"[^A-Za-z0-9 ]+", "", name
            )  # Strip special characters from name
            url = row["Urls"]
            start_time = row["start"]
            end_time = row["end"]

            if url != "":
                self.download_videos(url, name, start_time, end_time)


if __name__ == "__main__":
    poi_filename = os.getenv("REF_AUDIO_CSV")
    audio_dir = os.getenv("REF_AUDIO_DIR")
    clsObj = RefVideoScrapper(poi_filename, audio_dir)
    clsObj.iterate_poi()
