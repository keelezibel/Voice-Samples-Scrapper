##############################################################################################
"""
This script will scrape the list of pois from the SG_MP_URL variable defined in .env file
and save into a CSV file in data/poi_list/blue_poi.csv

Usage:
1. Without cached HTML
`python src/process_poi_list/blue_list.py `
2. With cached HTML
`python src/process_poi_list/blue_list.py -c`

"""
##############################################################################################

import os
import argparse
import requests
from dotenv import load_dotenv
from turtle import clear
import pandas as pd
from bs4 import BeautifulSoup

load_dotenv()


class BluePOI:
    def __init__(self):
        self.mp_url = os.getenv("SG_MP_URL")
        self.csv_file = os.getenv("BLUE_POI_CSV")
        self.html_file = os.getenv("BLUE_POI_HTML")

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
        df = pd.DataFrame(columns=["Name", "Constituency"])
        results = soupText.find_all(class_="list")
        for row in results:
            list_res = row.findAll("li")
            for list_item in list_res:
                name = list_item.find(
                    class_="col-md-8 col-xs-12 mp-sort-name"
                ).text.strip()
                constituency = (
                    list_item.find(
                        class_="col-md-6 col-xs-11 mp-sort constituency"
                    ).text.strip()
                    if list_item.find(class_="col-md-6 col-xs-11 mp-sort constituency")
                    else None
                )
                photo_url = f"https://www.parliament.gov.sg{list_item.find(class_='col-md-4 col-xs-8').findAll('img')[0]['src']}"
                tmp_df = pd.DataFrame(
                    [
                        {
                            "Name": name,
                            "Constituency": constituency,
                            "PhotoURL": photo_url,
                        }
                    ]
                )
                df = pd.concat([df, tmp_df], axis=0, ignore_index=True)

                # Try to get photo based on photo_url
                try:
                    data = requests.get(photo_url).content
                    output_path = os.path.join(
                        os.getenv("DATA_FOLDER"), os.getenv("REF_IMAGES")
                    )
                    with open(f"{output_path}/{name}.png", "wb") as f:
                        f.write(data)
                except Exception as e:
                    print("Unable to download image")
                    print(e)
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
                parsed_contents = self.getPageContents(self.mp_url)
                df = self.parseDetails(parsed_contents)
        else:  # Check if cache folder contains html
            parsed_contents = self.getPageContents(self.mp_url)
            df = self.parseDetails(parsed_contents)
        return df

    def write_to_csv(self, df):
        df.to_csv(self.csv_file, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--cache", action="store_true", help="override cached data"
    )
    args = parser.parse_args()

    blueclsObj = BluePOI()
    df = blueclsObj.getActual(args.cache)
    blueclsObj.write_to_csv(df)
