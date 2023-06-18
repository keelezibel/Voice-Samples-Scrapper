##############################################################################################
"""
This script will read the CSV containing the YT links and download only the audio related to 
each video. The vdieos and audios are saved in data/videos/<poi>

python process_poi_list/video_scrapper.py --file poi_list_withurls.csv
"""
##############################################################################################

import os
import re
import argparse
import shutil
import ast
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

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


class VideoScrapper:
    def __init__(self, poi_filename, video_dir):
        """Initialize a class to scrape the actual videos

        Args:
            poi_filename (str): filepath to the csv with URLs
            video_dir(str): Directory to store the video and audio files
        """
        self.poi_filename = poi_filename
        self.df = None
        self.video_dir = video_dir

    def read_poi_file(self):
        """Read in the CSV file"""
        self.df = pd.read_csv(self.poi_filename)

    def download_videos(self, url, name):
        """Specify the yt-dlp parameters

        Args:
            url (str): URL to retrieve videl
            name (str): speaker name
        """
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=mp4]/mp4+best[height<=480], m4a/bestaudio/best",
            "postprocessors": [
                {  # Extract audio using ffmpeg
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
            "postprocessor_args": ["-ar", "16000", "-ac", "1"],
            "outtmpl": f"{self.video_dir}/{name}/%(id)s.%(ext)s",
            "keepvideo": True,
            "logger": YTLogger,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(url)
        except Exception as e:
            print(e)
            return

    def create_directory(self, name):
        """Create target folder to store audio clips for each name

        Args:
            name (str): Name of each POI
        """
        target_video_dir = os.path.join(self.video_dir, name)
        if os.path.exists(target_video_dir):  # If directory exists, dont do anything
            return False
        os.makedirs(target_video_dir, exist_ok=True)
        return True

    def process_urls(self):
        """Iterate through each name and download videos into each speaker folder"""
        for _, row in tqdm(self.df.iterrows(), total=self.df.shape[0]):
            # Parse string as list
            name = row["Name"]
            name = re.sub(
                r"[^A-Za-z0-9 ]+", "", name
            )  # Strip special characters from name
            urls = ast.literal_eval(row["Urls"])

            new_poi_flag = self.create_directory(name)  # Create folder for each POI
            if new_poi_flag:
                self.download_videos(urls, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()

    poi_filename = os.path.join(os.getenv("POI_FOLDER"), args.file)
    clsObj = VideoScrapper(
        poi_filename,
        video_dir=os.path.join(os.getenv("DATA_FOLDER"), os.getenv("VIDEO_FOLDER")),
    )
    clsObj.read_poi_file()
    clsObj.process_urls()
