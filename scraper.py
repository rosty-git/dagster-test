import json
import typing
import pathlib
from collections import defaultdict

import requests
import pandas as pd
from bs4 import BeautifulSoup


class ScrapperDagster:
    """
    Scrapper class for collecting data from web site which you would like
    """
    def __init__(self, config: dict) -> None:
        self.config = config
        self.urls = []
        self.scrape_result = {}

    def save(self, path_dir: typing.Union[pathlib.Path, str] = None, file_type: str = 'csv') -> None:
        for name, lst in self.scrape_result.items():
            df = pd.DataFrame(lst)
            df.to_csv(f"{str(path_dir)}/{name}.{file_type}", index=False)

    def scrape(self) -> None:
        self._append_extra_url(config['URLS']['POPUP'])
        self._nested_categories(config['URLS']['HOME'])

        for url in self.urls:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')

            items = defaultdict(list)
            for item in soup.find_all(config['ITEMS']['tag'], class_=config['ITEMS']['name']):
                for prop in config["PROPS"]:
                    element = item.find(class_=prop)
                    if prop == 'ratings':
                        review, rate = self._parsing_data_rating(element)
                        items['reviews'].append(int(review[:review.find(" ")]))
                        items['ratings'].append(int(rate))
                    else:
                        items[prop].append(element.text)

            self.scrape_result[url.split('/')[-1]] = items

    def _parsing_data_rating(self, element: typing.Any) -> list:
        props = []
        for p_elem in element.find_all('p'):
            if 'data-rating' in p_elem.attrs:
                props.append(p_elem.attrs['data-rating'])
            else:
                props.append(p_elem.text)
        return props

    def _nested_categories(self, url: str) -> None:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        sidebar = soup.find(config['SIDEBAR']['tag'], class_=config['SIDEBAR']['name'])

        for link in sidebar.find_all('a'):
            try:
                href = link.attrs['href']
            except:
                continue

            if href.startswith('/'):
                new_url = config['URLS']['BASE_URL'] + href
                if new_url not in self.urls:
                    self.urls.append(new_url)
                    self._nested_categories(new_url)
    
    def _append_extra_url(self, url: str):
        self.urls.append(url)


if __name__ == "__main__":
    config = json.load(open('config.json'))
    scrap = ScrapperDagster(config)
    scrap.scrape()
    scrap.save(path_dir="./output")