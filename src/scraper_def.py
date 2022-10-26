import time
from typing import Union
from random import randint, uniform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.remote.webelement import WebElement

import utils
import scraper_constants
from utils import Numeric, NumericIter


logger = utils.log_ws(__name__)

# trying to hide webscraper
# https://www.php8legs.com/en/php-web-scraper/51-how-to-avoid-selenium-webdriver-from-being-detected-as-bot-or-web-spider


class Scraper:
    def __init__(
            self,
            load_wait_seconds: Numeric = 30,
            sleep_pattern_seconds: NumericIter = (2, 15),
            ) -> None:
        self.browser_driver_path = scraper_constants.BROWSER_DRIVER_PATH
        self.chrome_options = webdriver.ChromeOptions()
        # disable "chrome is being controlled by automated testing software" message
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.set_user_agent()
        self.wd = self.start_chrome()
        self.html_content = {}
        self.load_wait_seconds = load_wait_seconds
        self.sleep_pattern_seconds = sleep_pattern_seconds

    # TODO: fix property
    @property
    def sleep_pattern(self) -> Union[int, float, list[Union[int, float]], tuple[Union[int, float]]]:
        print("getter")
        return self.sleep_pattern_seconds

    # TODO: fix property
    @sleep_pattern.setter
    def sleep_pattern(self, x) -> None:
        print("setter")
        assert (
            isinstance(x, (int, float))
            or (isinstance(x, (list, tuple)) and len(x) == 2)
        ), "if sleep_pattern_seconds is a list or tuple it must be of length 2"
        self.sleep_pattern_seconds = x

    def set_user_agent(self) -> None:
        """
        Randomly pick a user agent name out of a list of popular ones.
        """
        i = randint(0, len(scraper_constants.POPULAR_USER_AGENTS) - 1)
        user_agent = scraper_constants.POPULAR_USER_AGENTS[i]
        self.chrome_options.add_argument("user-agent=" + user_agent)

    def display_user_agent(self) -> str:
        """
        Displays the browser's user agent if the browser was launched.
        :return: the user agent name or that "no webdriver started"
        """
        return self.wd.execute_script("return navigator.userAgent")

    def set_headless(self) -> None:
        """
        Configures chrome to be in headless mode (essential to run scraper in server)
        """
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')

    def start_chrome(self) -> webdriver.Chrome:
        """
        Launches Chrome with the specified configuration
        """
        return webdriver.Chrome(self.browser_driver_path, options=self.chrome_options)

    def get(self, *args, **kwargs):
        self.wd.get(*args, **kwargs)

    def quit(self) -> None:
        self.wd.quit()

    def sleep(self) -> float:
        if isinstance(self.sleep_pattern_seconds, (int, float)):
            sleep_time = self.sleep_pattern_seconds
        elif isinstance(self.sleep_pattern_seconds, (list, tuple)):
            sleep_time = uniform(
                self.sleep_pattern_seconds[0],
                self.sleep_pattern_seconds[1]
            )
        time.sleep(sleep_time)
        return sleep_time


class WortenScraper(Scraper):
    def __init__(self,
                 load_wait_seconds: Union[int, float] = 30,
                 sleep_pattern_seconds: Union[Numeric, NumericIter] = (10, 33),
                 ) -> None:
        super().__init__(load_wait_seconds, sleep_pattern_seconds)
        self.categories_to_scrape: dict[str, dict[str, Union[str, int]]] = {}
        self.site_html: dict[str, list[str]] = {}
        self.sample_share: Numeric = 1

    def activate_sampling(self, share: float) -> None:
        """
        Select the probability with which each part of the site will be scraped.
        Useful for testing purposes
        :param share: which percentage between 0 and 1 to scrape
        """
        self.sample_share = share

    def accept_cookies(self) -> None:
        """
        Accept cookies in pop up, if it appears
        """
        logger.info("scrape: close cookie pop-up (if exists)")
        # find button
        try:
            button = self.wd.find_element(By.XPATH, "//*[contains(text(), 'Aceitar Tudo')]")
        except NoSuchElementException:
            pass
        else:
            # click to accept cookies
            button.click()

    @staticmethod
    def _create_lvl3_product_xpath() -> str:
        """
        Creates a string indicating the xpath of all the products level 3 categories to extract

        All items in the products page are organised in a hierarchical category system
        (in 3 levels going from more general to more specific)
        This XPATH captures the most specific level 'third-level', except 'Ver Todos'.
        'Ver Todos' was excluded because it encompasses all the product in a category level 2.
        It would be a more convenient way of accessing all items if only it was present everywhere
        however only some level 2 categories have it. So to avoid scraping all the items of a given
        level 2 category twice, we exclude it.
        ex class: 'header__submenu-third-level-sitemap qa-header__submenu-third-level--'
        //a[contains(@class, 'submenu-third-level') and not(contains(text(), 'Ver Todos'))]

        However, we don't want all the class level 2 items as we are only interested in electronic items
        So we restrict to:
            * large home appliances: 'Grandes Eletrodomésticos'
            * small home appliances: 'Pequenos Eletrodomésticos'
            * TVs, video and sound: 'TV, Vídeo e Som'
            * IT and acessories: 'Informática e Acessórios'
        //div[contains(@class, 'submenu-second-level') and contains(/div/span/text(), 'Eletrodomésticos')]
        However, it was actually sufficient only to use:
        //div[div/span[contains(text(), 'Eletrodomésticos') or contains(text(), 'TV, Vídeo e Som') or contains(text(), 'Informática e Acessórios')]]

        Now, we want all the categories level 3 that are on the unordered list (ul) which is the
        only sibling of the category selected above, which is indicated by `following-sibling::ul`
        So the final XPATH becomes:
        //div[div/span[contains(text(), 'Eletrodomésticos') or contains(text(), 'TV, Vídeo e Som') or contains(text(), 'Informática e Acessórios')]]//following-sibling::ul//a[contains(@class, 'submenu-third-level') and not(contains(text(), 'Ver Todos')) and not(contains(text(), 'Ajuda-me a escolher'))]

        :return: the xpath of all the products level 3 categories to extract
        """
        # create parent component
        parent_xpath = [f"contains(text(), '{category}')" for category in scraper_constants.LVL2_CATEGORIES]
        parent_xpath = " or ".join(parent_xpath)
        parent_xpath = f"//div[div/span[{parent_xpath}]]"

        # create sibling component
        sibling_xpath_inclusions = f"contains(@class, '{scraper_constants.LVL3_REF}')"
        sibling_xpath_exclusions = [
            f"not(contains(text(), '{category}'))" for category in scraper_constants.LVL3_EXCLUDED_CATEGORIES
        ]
        sibling_xpath = " and ".join((sibling_xpath_inclusions, *sibling_xpath_exclusions))
        sibling_xpath = f"//following-sibling::ul//a[{sibling_xpath}]"

        return parent_xpath + sibling_xpath

    def find_section_urls(self) -> None:
        """
        Goes to the product page and populates categories_to_scrape with the names and
        URLs of the categories (level 3) to scrape
        """
        logger.info("scrape: start searching section URLs")
        self.wd.get(scraper_constants.PRODUCT_PAGE_URL)
        lvl3_xpath = self._create_lvl3_product_xpath()
        _ = (
            WebDriverWait(self.wd, self.load_wait_seconds)
            .until(
                EC.presence_of_element_located((By.XPATH, lvl3_xpath))
            )
        )
        lvl3_product_links = self.wd.find_elements(By.XPATH, lvl3_xpath)
        self.categories_to_scrape = {
            link.get_attribute('text'): {"url": link.get_attribute('href')}
            for link in lvl3_product_links
        }
        logger.info("scrape: finished searching section URLs")

    def section_last_page_num(self) -> int:
        """
        Find the last page in a given section
        :return: the last page number
        """
        # TODO: consider handling a TimeoutException thrown if 'pagination-last'
        #  can't be retrieved
        pagination_last_elem = (
            WebDriverWait(self.wd, self.load_wait_seconds)
            .until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pagination-last'))
            )
        )
        return int(pagination_last_elem.text)

    def get_section(self, section_url: str) -> list:
        """
        :param section_url:
        :return:
        """
        section_html = []
        p = 1
        self.wd.get(section_url)
        while p < scraper_constants.MAX_PAGES_PER_SECTION:
            # sleep for a random amount of time to seem more human
            sleep_time = self.sleep()
            # wait for load until the page number is displayed
            try:
                _ = (
                    WebDriverWait(self.wd, self.load_wait_seconds)
                    .until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'current'))
                    )
                )
            except TimeoutException:
                total_wait_seconds: float = sleep_time + self.load_wait_seconds
                logger.info(f"scrape: page didn't load after, {total_wait_seconds:.3}s")
                break
            # extract page HTML code
            section_html.append(self.wd.page_source)

            # if there is a next page click on it to move forward, if there isn't then
            # it must be the end of the section so exit
            try:
                next_page_link = self.wd.find_element(By.XPATH, '//li[@class="pagination-next"]/a')
            except NoSuchElementException:
                break
            else:
                next_page_link.click()
            if p == scraper_constants.MAX_PAGES_PER_SECTION:
                logger.info("scrape: the section has more pages then the search limit")
            p += 1
        return section_html

    def get_entire_site(self) -> None:
        # got to main page and accept cookies (seems more human to start there)
        start_url = scraper_constants.HOME_PAGE
        self.get(start_url)
        self.accept_cookies()

        # get section URLs
        if not self.categories_to_scrape:
            self.find_section_urls()

        # scrape each section
        for category, info in self.categories_to_scrape.items():
            logger.info(f"scrape: category {category},\nwith URL {info['url']}")
            if self.sample_share < 1 and uniform(0, 1) > self.sample_share:
                logger.info(f"category sampled out")
                continue
            section_html: list[str] = self.get_section(info["url"])
            self.site_html[category] = section_html
            info["pages"] = len(section_html)
            logger.info(f"scrape: {len(section_html)} HTML pages download")
        logger.info(f"scrape: finished site scrape with sample parameter {self.sample_share}")

