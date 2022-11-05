import re
from typing import Any
from datetime import datetime

from bs4 import BeautifulSoup, element

import utils


logger = utils.log_ws(__name__)


class WortenHtmlParser:
    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = self.__set_metadata_defaults(metadata)

    @staticmethod
    def __set_metadata_defaults(metadata: dict[str, Any]):
        metadata_defaults = {}
        if 'date' not in metadata:
            metadata_defaults['date'] = datetime.now().strftime("%Y/%m/%d")
        return dict(metadata, **metadata_defaults)

    @staticmethod
    def __price_decoding(price_main: str, price_dec: str) -> float:
        try:
            price: float = float(f'{price_main}.{price_dec}')
        except ValueError:
            price_main = re.findall(r'\d+', price_main)[0]
            price_dec = re.findall(r'\d+', price_dec)[0]
            price: float = float(f'{price_main}.{price_dec}')
        return price

    @staticmethod
    def parse_container_components(container: element.Tag) -> dict[str, Any]:
        """
        parses a product name in a container
        """
        prod: dict = {}
        # product price
        description_html: element.Tag = container.findChild("div", {"class": "w-product__description"})
        # description_html.findChild(re.compile("^h[1-6]$"), {"class": 'w-product__title'})
        prod['title']: str = description_html.div.h3.text

        # product price
        details_html: element.Tag = container.findChild('div', {"class": "w-product__details"})
        price_main: str = details_html.findChild("span", {"class": "w-product-price__main"}).text
        price_dec: str = details_html.findChild("sup", {"class": "w-product-price__dec"}).text
        prod['price']

        # image url
        image_html: element.Tag = container.findChild('figure', {"class": "w-product__image"})
        prod['img_url'] = f"worten.pt{image_html.img['data-src']}"
        return prod

    def parse_containers(
            self,
            page_html: str) -> list[dict[str, Any]]:
        """
        takes a page's raw HTML and extracts the product containers from it
        """
        # parse webpage
        page_soup: BeautifulSoup = BeautifulSoup(page_html, 'html.parser')
        # select product divs
        containers: element.ResultSet = page_soup.findAll("div", {"class": "w-product__wrapper"})
        return [
            self.parse_container_components(container) for container in containers
        ]

    def parse_site(self, site_html: dict[str, list[str]]) -> list[dict[str, Any]]:
        assert site_html, "no pages scraped"
        site_info: list = []
        for category, page_list in site_html.items():
            logger.info(f"parsing category: {category}")
            metadata: dict[str, Any] = dict(self.metadata, **{"category": category})
            parsed_category: list[dict[str, Any]] = [
                dict(prod, **metadata) for page in page_list
                for prod in self.parse_containers(page)
            ]
            site_info.extend(parsed_category)
        return site_info
