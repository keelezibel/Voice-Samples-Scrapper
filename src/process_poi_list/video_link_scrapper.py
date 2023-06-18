##############################################################################################
"""
This script will read the poi CSV and query the YT URLs with each POI name as the query term

python process_poi_list/video_link_scrapper.py --file poi_list.csv
"""
##############################################################################################

import os
import datetime
import scrapetube
import argparse
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

BASE_YOUTUBE_URL = "https://www.youtube.com/watch?v="


class VideoLinkScrapper:
    def __init__(self, poi_filename, min_duration, max_duration, nrecords=50):
        """Initializes the class to scrape youtube links

        Args:
            poi_filename (str): filepath of poi csv
            min_duration (int): minimum allowable length of the audio (mins)
            max_duration (int): maximum allowable length of the audio (mins)
            nrecords (int, optional): Number of YT links to pull. Defaults to 50.
        """
        self.poi_filename = os.path.join(os.getenv("POI_FOLDER"), poi_filename)
        self.df = None
        self.outfile = os.path.join(
            os.getenv("POI_FOLDER"),
            os.path.basename(poi_filename).split(".")[0] + "_withurls.csv",
        )
        self.nrecords = nrecords
        self.max_duration = max_duration
        self.min_duration = min_duration

    def read_poi_file(self):
        """Read in CSV file into a DataFrame"""
        self.df = pd.read_csv(self.poi_filename)

    def get_seconds(self, duration):
        """Convert duration to seconds

        Args:
            duration (str): String rep of time

        Returns:
            int: duration in seconds
        """
        if ":" not in duration:
            return None

        num_parts = duration.split(":")
        if len(num_parts) == 3:
            return int(
                str(
                    (
                        datetime.datetime.strptime(duration, "%H:%M:%S")
                        - datetime.datetime(1900, 1, 1)
                    ).total_seconds()
                ).split(".")[0]
            )
        else:
            return int(
                str(
                    (
                        datetime.datetime.strptime(duration, "%M:%S")
                        - datetime.datetime(1900, 1, 1)
                    ).total_seconds()
                ).split(".")[0]
            )

    def process_urls(self):
        """Iterte through each name and query YT for the links via scrapetube"""
        poi_names = self.df["Name"]
        url_col = []
        for name in tqdm(poi_names):
            videos = scrapetube.get_search(
                name, limit=self.nrecords, sort_by="relevance"
            )

            video_urls = []
            for video in videos:
                if (
                    "thumbnailOverlays" in video
                    and "thumbnailOverlayTimeStatusRenderer"
                    in video["thumbnailOverlays"][0]
                ):
                    duration = video["thumbnailOverlays"][0][
                        "thumbnailOverlayTimeStatusRenderer"
                    ]["text"]["simpleText"]
                else:
                    continue

                seconds = self.get_seconds(duration)

                if (
                    seconds
                    and int(seconds) >= self.min_duration
                    and int(seconds) <= self.max_duration
                ):
                    video_urls.append(BASE_YOUTUBE_URL + video["videoId"])

            if url_col:
                url_col.extend([video_urls])
            else:
                url_col = [video_urls]
        # Append new column to dataframe
        self.df["Urls"] = url_col

    def export_df(self):
        self.df.to_csv(self.outfile, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()

    poi_filename = args.file
    clsObj = VideoLinkScrapper(
        poi_filename,
        min_duration=60 * 1,
        max_duration=60 * 10,
        nrecords=15,
    )
    clsObj.read_poi_file()
    clsObj.process_urls()
    clsObj.export_df()
