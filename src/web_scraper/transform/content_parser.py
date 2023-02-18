import re
from typing import Any
from datetime import datetime

from bs4 import BeautifulSoup, element

from web_scraper.support import utils
from web_scraper.extract.scraper_base import SectionScrape

logger = utils.log_ws(__name__)


class WortenHtmlParser:
    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = self._set_metadata_defaults(metadata)

    @staticmethod
    def _set_metadata_defaults(metadata: dict[str, Any]):
        metadata_defaults = {}
        if 'date' not in metadata:
            metadata_defaults['date'] = datetime.now().strftime("%Y-%m-%d")
        return dict(metadata, **metadata_defaults)

    @staticmethod
    def _price_decoding(price_main: str, price_dec: str) -> float:
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
        return self._price_decoding(price_main, price_dec)

    def extract_previous_price(self, container: element.Tag) -> float:
        details_html: element.Tag = container.findChild('span', {"class": "w-oldPrice"})
        if details_html:
            price_main: str = details_html.findChild("span", {"class": "w-product-price__main"}).text
            price_dec: str = details_html.findChild("sup", {"class": "w-product-price__dec"}).text
            return self._price_decoding(price_main, price_dec)

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

    def parse_category(self, category: SectionScrape) -> list[dict[str, Any]]:
        assert category, "no pages to parse"
        specs = category.section_specs
        category_lvl3 = specs['category_lvl3']
        logger.info(f"parsing category: {category_lvl3}")

        parsed_category: list = []
        category_lvls = {f"category_lvl{i}": specs[f"category_lvl{i}"] for i in range(1, 4)}
        extra: dict[str, Any] = dict(self.metadata, **category_lvls)
        for page_html in category.html:
            parsed_page_html = self.parse_containers(page_html)
            parsed_page = dict({'html': parsed_page_html}, **extra)
            parsed_category.extend(parsed_page)
        logger.info('Finished parsing Worten')
        return parsed_category
