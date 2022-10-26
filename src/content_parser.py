from typing import Any

from bs4 import BeautifulSoup, element

import utils


logger = utils.log_ws(__name__)


class WortenHtmlParser:
    def __init__(self, metada: dict[str, Any]) -> None:
        self.metadata = metada

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
        prod['price']: float = float(f'{price_main}.{price_dec}')

        # image url
        #if prod['title'] == 'Máquina de Café MELITTA CI Touch (15 bar - Níveis de Moagem: 5)':
        #    import pdb; pdb.set_trace()
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
