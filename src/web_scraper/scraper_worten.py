"""
Defines the basic the specific scraper make to get the Worten products
"""
import re
import pickle
from random import uniform
from typing import Union, Type, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)

from web_scraper import utils
import web_scraper.scraper_config as spc
from web_scraper.types import Numeric, NumericIter, NestedStrKeyDict
from web_scraper.scraper_base import Scraper
from web_scraper.errors import ScraperBlockedError, NoPopUpError


logger = utils.log_ws(__name__)


class WortenScraper(Scraper):
    def __init__(self,
                 config: Type[spc.WortenSpConfig],
                 load_wait_sec: Union[int, float] = 30,
                 sleep_pattern_sec: Union[Numeric, NumericIter] = (2, 4),
                 ) -> None:
        super().__init__(config, load_wait_sec, sleep_pattern_sec)
        self.config: Type[spc.WortenSpConfig] = config
        self.lvl3_categories: Union[NestedStrKeyDict, dict] = {}
        self.site_html: dict[str, list[str]] = {}

    def get_home_page(self):
        return self.get(self.config.HOME_PAGE)

    def rm_cookies_pop_up(self, method: str = 'raise') -> None:
        """
        Accept cookies in pop up, if it appears
        method:
            * 'ignore' then it will carry if it doesn't find a pop-up window to close
            * 'raise' it will raise and error if no window showed up
        """
        button_xpath = "//*[contains(text(), 'Aceitar Tudo')]"
        extra_load_wait_sec: Numeric = 20

        self.assert_wd_active()
        logger.info("close cookie pop-up (if exists)")

        # wait for pop-up button
        try:
            button = (
                WebDriverWait(self.wd, self.load_wait_sec + extra_load_wait_sec)
                .until(
                    EC.presence_of_element_located((By.XPATH, button_xpath))
                )
            )
        except TimeoutException:
            if method == 'raise':
                raise NoPopUpError("Couldn't find pop-up window")
        else:
            button.click()

    def _create_lvl3_category_xpath(self) -> str:
        """
        Creates a string indicating the xpath of all the products level 3 categories to extract:
            * large home appliances: 'Grandes Eletrodomésticos'
            * small home appliances: 'Pequenos Eletrodomésticos'
            * TVs, video and sound: 'TV, Vídeo e Som'
            * IT and acessories: 'Informática e Acessórios'
        (for more information read: worten_site_layout.md)
        :return: the xpath for categories above (as single string)
        """
        # create parent component
        parent_xpath = [f"contains(text(), '{category}')" for category in self.config.LVL2_CATEGORIES]
        parent_xpath = " or ".join(parent_xpath)
        parent_xpath = f"//div[div/span[{parent_xpath}]]"

        # create sibling component
        sibling_xpath_inclusions = f"contains(@class, '{self.config.LVL3_REF}')"
        sibling_xpath_exclusions = [
            f"not(contains(text(), '{category}'))" for category in self.config.LVL3_EXCLUDED_CATEGORIES
        ]
        sibling_xpath = " and ".join((sibling_xpath_inclusions, *sibling_xpath_exclusions))
        sibling_xpath = f"//following-sibling::ul//a[{sibling_xpath}]"

        return parent_xpath + sibling_xpath

    def _wait_lvl3_categories(self, lvl3_xpath: str) -> None:
        try:
            _ = (
                WebDriverWait(self.wd, self.load_wait_sec)
                .until(
                    EC.presence_of_element_located((By.XPATH, lvl3_xpath))
                )
            )
        except TimeoutException:
            self.wd.save_screenshot(self.config.MAIN_DIR/"screenshots"/"worten_categories.png")
            if "captcha" in self.wd.page_source.lower():
                raise ScraperBlockedError('got Worten captcha')
            raise TimeoutException("Categories page not properly loaded")

    def _parse_lvl3_category_urls(self, lvl3_category_links: str) -> NestedStrKeyDict:
        lvl3_categories = {
            link.get_attribute('text'): {"url": link.get_attribute('href')}
            for link in lvl3_category_links
        }
        urls = [val for info in self.lvl3_categories.values() for val in info.values()]
        logger.info(f"got {len(set(urls))} distinct level 3 category URLs")
        return lvl3_categories

    def find_lvl3_category_urls(self) -> None:
        """
        Goes to the product page and populates categories_to_scrape with the names and
        URLs of the categories (level 3) to scrape
        """
        self.assert_wd_active()
        logger.info("start searching section URLs")

        self.wd.get(self.config.PRODUCT_PAGE_URL)
        lvl3_xpath = self._create_lvl3_category_xpath()
        self._wait_lvl3_categories(lvl3_xpath)

        lvl3_category_links = self.wd.find_elements(By.XPATH, lvl3_xpath)
        self.lvl3_categories = self._parse_lvl3_category_urls(lvl3_category_links)

    def get_lvl3_category(self, base_url: str) -> list:
        """
        :param base_url:
        :return:
        """
        logger.info(f'start extraction {base_url}')
        self.assert_wd_active()
        category_html = []
        p = 1
        self.wd.get(base_url)
        while p <= self.config.MAX_PAGES_PER_SECTION:
            # sleep for a random amount of time to seem more human
            sleep_time = self.sleep()
            # wait for load until the page number is displayed
            try:
                _ = (
                    WebDriverWait(self.wd, self.load_wait_sec)
                    .until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'current'))
                    )
                )
            except TimeoutException:
                total_wait_sec: float = sleep_time + self.load_wait_sec
                logger.info(f"page didn't load after, {total_wait_sec:.3}s")
                break
            # extract page HTML code
            category_html.append(self.wd.page_source)

            # if there is a next page click on it to move forward, if there isn't then
            # it must be the end of the section so exit
            try:
                next_page_link = (
                    WebDriverWait(self.wd, self.load_wait_sec)
                    .until(
                        EC.presence_of_element_located((By.XPATH, '//li[@class="pagination-next"]/a'))
                    )
                )
            except (TimeoutException, NoSuchElementException): # test if only TimeoutException works
                break
            else:
                try:
                    next_page_link.click()
                except ElementNotInteractableException:
                    logger.warning('ElementNotInteractableException on next page click, trying to accept cookies again')
                    self.rm_cookies_pop_up()
                    try:
                        next_page_link.click()
                    except ElementNotInteractableException:
                        logger.warning('ElementNotInteractableException on next page click, stopping category scrape')
                        break
            if p == self.config.MAX_PAGES_PER_SECTION:
                logger.info("the section has more pages then the search limit")
            p += 1
        return category_html

    def _get_pagination_navigation(self) -> Optional[WebElement]:
        pagination_xpath = '//ul[@aria-label="Pagination"]'
        try:
            pagination_elem = (
                WebDriverWait(self.wd, self.load_wait_sec)
                .until(
                    EC.presence_of_element_located((By.XPATH, pagination_xpath))
                )
            )
        except TimeoutException:
            return None
        else:
            return pagination_elem

    @staticmethod
    def _get_last_page(pagination_elem: WebElement) -> Optional[int]:
        try:
            navigation_elems = pagination_elem.find_elements(By.TAG_NAME, "li")
        except NoSuchElementException:
            return None
        else:
            page_txt = [re.sub("[^0-9]", "", elem.text) for elem in navigation_elems]
            page_number = [int(txt) for txt in page_txt if txt]
            return page_number[-1]

    def get_page_count(self) -> Optional[int]:
        """
        Find the last page in a given section
        :return: the last page number
        """
        self.assert_wd_active()
        pagination_elem = self._get_pagination_navigation()
        if pagination_elem is None:
            return None
        return self._get_last_page(pagination_elem)

    def get_site(self, select_categories: Optional[list[str]] = None) -> None:
        """
        Scrapes entire Worten site. It first goes to the product home page which contains
        all the categories of products organised in a hierarchical format.
        :return:
        """
        self.assert_wd_active()
        logger.info("starting Worten full site parsing")
        # got to main page and accept cookies (seems more human to start there)
        self.get_home_page()
        self.rm_cookies_pop_up()

        # get section URLs
        if not self.lvl3_categories:
            self.find_lvl3_category_urls()

        # scrape each section
        for category, info in self.lvl3_categories.items():
            if select_categories and category not in select_categories:
                continue
            logger.info(f"category {category},\nwith URL {info['url']}")
            if self.sample_share < 1 and uniform(0, 1) > self.sample_share:
                logger.info(f"category sampled out, skipping")
                continue
            section_html: list[str] = self.get_lvl3_category(info["url"])
            self.site_html[category] = section_html
            info["pages"] = len(section_html)
            logger.info(f"{len(section_html)} HTML pages downloaded")
        logger.info(f"finished site scrape with sample parameter {self.sample_share}")

    def save(self, name: str) -> None:
        with open(name, 'wb') as file:
            pickle.dump(self.site_html, file)
