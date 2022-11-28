import re
from typing import Any
from datetime import datetime

from bs4 import BeautifulSoup, element

from web_scraper.support import utils

logger = utils.log_ws(__name__)


class WortenHtmlParser:
    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = self.__set_metadata_defaults(metadata)

    @staticmethod
    def __set_metadata_defaults(metadata: dict[str, Any]):
        metadata_defaults = {}
        if 'date' not in metadata:
            metadata_defaults['date'] = datetime.now().strftime("%Y-%m-%d")
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
    def extract_prod_name(container: element.Tag) -> str:
        description_html: element.Tag = container.findChild("div", {"class": "w-product__description"})
        # description_html.findChild(re.compile("^h[1-6]$"), {"class": 'w-product__title'})
        return description_html.div.h3.text

    def extract_current_price(self, container: element.Tag) -> float:
        details_html: element.Tag = container.findChild('span', {"class": "w-currentPrice iss-current-price"})
        price_main: str = details_html.findChild("span", {"class": "w-product-price__main"}).text
        price_dec: str = details_html.findChild("sup", {"class": "w-product-price__dec"}).text
        return self.__price_decoding(price_main, price_dec)

    def extract_previous_price(self, container: element.Tag) -> float:
        details_html: element.Tag = container.findChild('span', {"class": "w-oldPrice"})
        if details_html:
            price_main: str = details_html.findChild("span", {"class": "w-product-price__main"}).text
            price_dec: str = details_html.findChild("sup", {"class": "w-product-price__dec"}).text
            return self.__price_decoding(price_main, price_dec)

    @staticmethod
    def extract_image_url(container: element.Tag) -> str:
        image_html: element.Tag = container.findChild('figure', {"class": "w-product__image"})
        return f"worten.pt{image_html.img['data-src']}"

    def extract_prod_specs(self, container: element.Tag) -> dict[str, Any]:
        """
        parses a product name in a container
        """
        prod: dict = {
            'name': self.extract_prod_name(container),
            'price': self.extract_current_price(container),
            'img_url': self.extract_image_url(container)
        }
        price_previous = self.extract_previous_price(container)
        if price_previous:
            prod['price_previous'] = price_previous
        return prod

    def try_extract_prod_specs(self, container):
        try:
            return self.extract_prod_specs(container)
        except (ValueError, TypeError) as e:
            logger.warning(e)
            return None

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
        if containers:
            return [
                self.try_extract_prod_specs(container) for container in containers
            ]
        return []

    def parse_site(self, site_html: dict[str, list[str]]) -> list[dict[str, Any]]:
        assert site_html, "no pages to parse"
        site_info: list = []
        for category, page_list in site_html.items():
            logger.info(f"parsing category: {category}")
            metadata: dict[str, Any] = dict(self.metadata, **{"lvl3_category": category})
            parsed_category: list[dict[str, Any]] = [
                dict(prod, **metadata) for page in page_list
                for prod in self.parse_containers(page)
            ]
            site_info.extend(parsed_category)
        logger.info('Finished parsing Worten')
        return site_info
