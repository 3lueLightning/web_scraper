"""
Defines the basic the specific scraper make to get the Worten products
"""
import re
from random import uniform
from datetime import datetime
from typing import Union, Type, Optional, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)

from web_scraper.support import utils
import web_scraper.extract.scraper_config as spc
from web_scraper.support.types import (
    Numeric,
    NumericIter,
    StrDict,
    ListStrDict
)
from web_scraper.extract.scraper_base import Scraper
from web_scraper.support.errors import ScraperBlockedError, NoPopUpError


logger = utils.log_ws(__name__)


class WortenScraper(Scraper):
    def __init__(self,
                 config: Type[spc.WortenSpConfig],
                 load_wait_sec: Union[int, float] = 30,
                 sleep_pattern_sec: Union[Numeric, NumericIter] = (2, 4),
                 ) -> None:
        super().__init__(config, load_wait_sec, sleep_pattern_sec)
        self.config: Type[spc.WortenSpConfig] = config
        self.lvl3_categories: Optional[ListStrDict] = None
        self.sections_failed = []

    def get_home_page(self):
        return self.get(self.config.HOME_PAGE)

    def rm_cookies_pop_up(self, method: str = 'ignore') -> None:
        """
        Accept cookies in pop up, if it appears
        method:
            * 'ignore' then it will carry if it doesn't find a pop-up window to close
            * 'raise' it will raise and error if no window showed up
        """
        button_xpath = "//*[contains(text(), 'Aceitar Tudo')]"
        extra_load_wait_sec: Numeric = 20

        self.assert_wd_active()
        assert method in ['ignore', 'raise']
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
            page_txt = [re.sub('[^0-9]', '', elem.text) for elem in navigation_elems]
            page_number = [int(txt) for txt in page_txt if txt]
            return page_number[-1]

    def count_pages(self) -> Optional[int]:
        """
        Find the last page in a given section
        :return: the last page number
        """
        self.assert_wd_active()
        pagination_elem = self._get_pagination_navigation()
        if pagination_elem is None:
            return None
        return self._get_last_page(pagination_elem)

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

    def _parse_lvl3_category_urls(
            self,
            lvl3_category_links: list[WebElement]) -> ListStrDict:
        lvl3_categories = [
            {
                "url": link.get_attribute('href'),
                "category_lvl1": link.get_attribute('href').split("/")[-3],
                "category_lvl2": link.get_attribute('href').split("/")[-2],
                "category_lvl3": link.get_attribute('href').split("/")[-1],
                "lvl3_display_name": link.get_attribute('text')
            }
            for link in lvl3_category_links
        ]
        logger.info(f"got {len(lvl3_categories)} distinct level 3 categories")
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

        lvl3_category_links: list[WebElement] = self.wd.find_elements(By.XPATH, lvl3_xpath)
        self.lvl3_categories: ListStrDict = self._parse_lvl3_category_urls(lvl3_category_links)

    def _check_page_loaded(self) -> bool:
        current_page_class_name = 'current'

        # sleep for a random amount of time to seem more human
        sleep_time = self.sleep()
        # wait for load until the page number is displayed
        try:
            _ = (
                WebDriverWait(self.wd, self.load_wait_sec)
                .until(
                    EC.presence_of_element_located((By.CLASS_NAME, current_page_class_name))
                )
            )
        except TimeoutException:
            total_wait_sec: Numeric = sleep_time + self.load_wait_sec
            logger.info(f"page didn't load after, {total_wait_sec:.3}s")
            return False
        return True

    def _find_next_page_link(self) -> Optional[WebElement]:
        """
        If there is a next page click on it to move forward, if there isn't then
        it must be the end of the section return nothing
        :return: a link to the next page (if exists)
        """
        next_page_xpath = '//li[@class="pagination-next"]/a'
        try:
            next_page_link: WebElement = (
                WebDriverWait(self.wd, self.load_wait_sec)
                .until(
                    EC.presence_of_element_located((By.XPATH, next_page_xpath))
                )
            )
        except (TimeoutException, NoSuchElementException):  # test if only TimeoutException works
            return
        return next_page_link

    def _click_next_page_link(self, next_page_link: WebElement) -> bool:
        n_click_attempts = 2
        for attempt in range(1, n_click_attempts + 1):
            try:
                next_page_link.click()
            except ElementNotInteractableException:
                logger.warning(f'ElementNotInteractableException on next page click, {attempt=}')
                self.rm_cookies_pop_up()
            else:
                return True
        return False

    def _move_next_page(self) -> bool:
        """
        Try to move to the next page as long as there is link to do so other return nothing
        :return: True if it managed to move to the next page, False otherwise
        """
        next_page_link = self._find_next_page_link()
        if next_page_link is None:
            return False
        return self._click_next_page_link(next_page_link)

    def get_section(self, base_url: str, specs: Optional[dict] = None) -> dict[str, Any]:
        """
        Starts on the base_url page and then clicks on the next page button to iterate
        through all pages. It stops when the button disappears, meaning we reached the
        end of the section (can be a category or any group of pages).
        :param base_url: first page of a section
        :param specs: additional information about the section that will be added
            to "section_specs"
        :return: a dictionary of the with:
            * html: a list where each element is the raw html from a page in the section
            * section_specs: characteristics of the section being scraped
            * metadata: info about the scrape itself
        """
        logger.info(f'start extraction {base_url}')
        self.assert_wd_active()
        self.wd.get(base_url)
        n_pages = self.count_pages()
        logger.info(f"{n_pages=} to scrape")
        section_scrape: dict[str, Any] = {
            "html": [],
            "section_specs": {"base_url": base_url, "n_pages": n_pages},
            "metadata": {"datetime": datetime.now(), "n_pages_scraped": 0}
        }
        if specs:
            section_specs_keys = list(section_scrape["section_specs"].keys())
            keys_in_specs = [key in specs for key in section_specs_keys]
            assert not any(keys_in_specs), \
                f"specs cannot contain any of this keys: {section_specs_keys}"
            section_scrape["section_specs"].update(specs)
        p = 0
        while p <= self.config.MAX_PAGES_PER_SECTION:
            if not self._check_page_loaded():
                break
            p += 1
            # extract page HTML code
            section_scrape["html"].append(self.wd.page_source)
            # TODO: is the are way to separate the moving function from the validation
            #  that it indeed moved to the next page?
            if not self._move_next_page():
                break
            if p == self.config.MAX_PAGES_PER_SECTION:
                logger.info("the section has more pages then the search limit")
        section_scrape["metadata"]["n_pages_scraped"] = p
        logger.info(f"scraped {p}/{n_pages} pages")
        return section_scrape

    def try_get_section(
            self,
            base_url: str,
            specs: Optional[StrDict] = None) -> Optional[dict[str, Any]]:
        logger.info("start extraction")
        try:
            return self.get_section(base_url, specs)
        except WebDriverException as e:
            logger.warning(f"{e} prevented section scrape")
            failed = {"base_url": base_url}
            if specs:
                failed.update(specs)
            self.sections_failed.append(failed)
            if len(self.sections_failed) > self.config.N_MAX_SECTION_FAIL:
                raise ValueError('exceeded maximum amount of section failures')
            return

    def _filter_category(
            self,
            category_name: str,
            select_categories: Optional[list[str]]) -> bool:
        if select_categories:
            select_categories = [name.lower() for name in select_categories]
        if select_categories and category_name.lower() not in select_categories:
            logger.info("category not selected")
            return True
        if self.sample_share < 1 and uniform(0, 1) > self.sample_share:
            logger.info("category sampled out, skipping")
            return True
        return False

    def _filter_url(
            self,
            url: str,
            excluded_urls: Optional[list[str]]) -> bool:
        if excluded_urls and url in excluded_urls:
            logger.info("URL in exclusion list")
            return True
        else:
            return False

    def get_site(
            self,
            select_categories: Optional[list[str]] = None,
            excluded_urls: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Scrapes entire Worten site. It first goes to the product home page which contains
        all the categories of products organised in a hierarchical format.
        :return:
        """
        # TODO: select_categories should have an option that contains a tuple that indicating
        #  both the lvl2 and lvl3 categories in case there are 2 lvl3 categories with same name
        #  in 2 different lvl2 categories
        self.assert_wd_active()
        logger.info("starting Worten full site parsing")
        # got to main page and accept cookies (seems more human to start there)
        self.get_home_page()
        self.rm_cookies_pop_up()

        # get section URLs
        if not self.lvl3_categories:
            self.find_lvl3_category_urls()

        # scrape each page of each section
        for category in self.lvl3_categories:
            name: str = category['lvl3_display_name']
            logger.info(f"category {name}")
            if self._filter_category(name, select_categories):
                continue
            if self._filter_url(category["url"], excluded_urls):
                continue
            category_specs: StrDict = {
                key: val for key, val in category.items()
                if key not in ["url", 'n_pages']
            }
            yield self.try_get_section(category["url"], category_specs)
