##############################################################################################
"""
This script will read the CSV containing the POIs and create the folders to store their 
reference audio.
"""
##############################################################################################

import os
import re
import shutil
import ast
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class CreatePOIFolder:
    def __init__(self, poi_filenames_list, dst_dir):
        """Initialize a class to scrape the actual videos

        Args:
            poi_filename (list): filepath to the POIs csv
            dst_dir(str): Directory to store the ref audio files
        """
        self.poi_filenames_list = poi_filenames_list
        self.dst_dir = dst_dir

    def read_poi_file(self):
        """Read in the CSV file"""
        poi_list = []
        for f in self.poi_filenames_list:
            df = pd.read_csv(f)
            poi_list.extend(df["Name"].tolist())
        return poi_list

    def create_folders(self):
        """Create target folder to store audio clips for each name

        Args:
            name (str): Name of each POI
        """
        poi_list = self.read_poi_file()

        for poi in poi_list:
            target_dir = os.path.join(self.dst_dir, poi)
            os.makedirs(target_dir, exist_ok=True)


if __name__ == "__main__":
    poi_filename = os.getenv("GREEN_POI_CSV")
    poi_manual_filename = os.getenv("MANUAL_GREEN_POI_CSV")
    poi_filenames_list = [poi_filename, poi_manual_filename]

    clsObj = CreatePOIFolder(poi_filenames_list, dst_dir=os.getenv("REF_AUDIO_DIR"))
    clsObj.create_folders()
