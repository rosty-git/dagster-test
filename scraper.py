import json
import typing
import pathlib
from collections import defaultdict

import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


class ScrapperDagster:
    """
    Scrapper class for collecting data from web site which you would like
    """
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")

    def __init__(self, config: dict) -> None:
        self.config = config
        self.urls = []
        self.scrape_result = {}
        self.driver = webdriver.Chrome(executable_path="chromedriver_win32/chromedriver.exe", options=self.options)

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
                    elif prop == 'title':
                        vars, prices = self._get_variations_item(item.find(class_=prop))
                        if isinstance(vars[0], int):
                            items['memories'].append(vars)
                        else:
                            items['colors'].append(vars)
                        items['price'].append(prices)
                    else:
                        items[prop].append(element.text)

            self.scrape_result[url.split('/')[-1]] = items
        self.driver.close()

    def _get_variations_item(self, element: typing.Any) -> tuple[list]:
        try:
            url = config['URLS']['BASE_URL'] + element.attrs['onclick'].split('\'')[1]
        except:
            url = config['URLS']['BASE_URL'] + element.attrs['href']

        self.driver.get(url)
        try:
            mem_vars = list(map(int, self.driver.find_element(By.CLASS_NAME, "swatches").text.split(" ")))
        except:
            return [s.strip() for s in self.driver.find_elements(By.CLASS_NAME, "dropdown")[1].text.split("\n")][1:-1], \
                self.driver.find_element(By.CLASS_NAME, "price").text

        prices = []
        for btn in self.driver.find_elements(By.CSS_SELECTOR, ".btn"):
            btn.click()
            prices.append(self.driver.find_element(By.CLASS_NAME, "price").text)
        return mem_vars, prices

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