##############################################################################################
"""
This script will scrape the list of pois from the MY_DEWAN_RAKYAT_URL variable defined in .env file
and save into a CSV file in data/poi_list/green_poi.csv

Usage:
1. Without cached HTML
`python src/process_poi_list/green_list.py `
2. With cached HTML
`python src/process_poi_list/green_list.py -c`

"""
##############################################################################################

import os
import argparse
import requests
from dotenv import load_dotenv

import pandas as pd
from bs4 import BeautifulSoup

CACHE_FOLDER = os.getenv("CACHE_FOLDER")
load_dotenv()

class GreenPOI:
    def __init__(self):
        self.house_of_reps_url = os.getenv("MY_DEWAN_RAKYAT_URL")
        self.csv_file = os.getenv("GREEN_POI_CSV")
        self.html_file = os.getenv("GREEN_POI_HTML")

    def getPageContents(self, url):
        """Make a request to the URL and save the HTML into a text file in cache folder.

        Args:
            url (str): URL to site

        Returns:
            BS parsed html
        """  
        page = requests.get(url)
        with open(self.html_file, "w") as f:
            f.write(page.text)
        parsed_contents = BeautifulSoup(page.text, "html.parser")
        return parsed_contents

    def parseDetails(self, soupText):
        """Parse the HTML and search for DOM to construct the DataFrame

        Args:
            soupText : BS parsed HTML

        Returns:
            pd.DataFrame: DataFrame
        """
        df = pd.DataFrame(columns=["Name", "Party", "Constituency", "Province"])
        results = soupText.find_all(class_="list tiles member-of-parliament")
        for row in results:
            list_res = row.findAll("li")
            for list_item in list_res:
                name = list_item.find(class_="first-name").text
                party = (
                    list_item.find(class_="caucus").text if list_item.find(class_="caucus") else None
                )
                constituency = (
                    list_item.find(class_="constituency").text if list_item.find(class_="constituency") else None
                )
                province = (
                    list_item.find(class_="province").text if list_item.find(class_="province") else None
                )
                tmp_df = pd.DataFrame([{"Name": name, "Party": party, "Constituency": constituency, "Province": province}])
                df = pd.concat([df, tmp_df], axis=0, ignore_index=True)
        return df

    def getActual(self, cache):
        """Helper function to read from cached file or make a request to URL

        Args:
            cache (boolean): Boolean variable from argparse. If true, read from .txt else request from URL

        Returns:
            pd.DataFrame: DataFrame
        """   
        if cache:
            try:
                with open(self.html_file, "r") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    df = self.parseDetails(soup)
            except:
                parsed_contents = self.getPageContents(self.house_of_reps_url)     
                df = self.parseDetails(parsed_contents)          
        else:   # Check if cache folder contains html
            parsed_contents = self.getPageContents(self.house_of_reps_url)
            df = self.parseDetails(parsed_contents)
        return df

    def write_to_csv(self, df):
        df.to_csv(self.csv_file, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cache", action="store_true", help="override cached data")
    args = parser.parse_args()

    greenclsObj = GreenPOI()
    df = greenclsObj.getActual(args.cache)
    greenclsObj.write_to_csv(df)

        