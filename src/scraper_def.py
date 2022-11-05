import time
from random import uniform
from typing import Union, Type, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.remote.webelement import WebElement

import utils
import scraper_constants as spc
from utils import Numeric, NumericIter


logger = utils.log_ws(__name__)

# trying to hide webscraper
# https://www.php8legs.com/en/php-web-scraper/51-how-to-avoid-selenium-webdriver-from-being-detected-as-bot-or-web-spider


class ScraperBlockedError(Exception):
    pass


class Scraper:
    def __init__(
            self,
            config: Type[spc.ScraperConfig],
            load_wait_seconds: Numeric = 30,
            sleep_pattern_seconds: Union[Numeric, NumericIter] = (2, 15),
            ) -> None:
        self.config: Type[spc.ScraperConfig] = config
        self.load_wait_seconds: Numeric = load_wait_seconds
        self.sleep_pattern_seconds: Union[Numeric, NumericIter] = sleep_pattern_seconds

        self.chrome_options: webdriver.ChromeOptions = self.__set_chrome_options()
        self.wd: Optional[webdriver.Chrome] = None

    def __set_chrome_options(self) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        # disable "chrome is being controlled by automated testing software" message
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # if you don't set a user Agent the sites identify straight away that it's a crawler
        options.add_argument(f"user-agent={self.config.USER_AGENT}")
        return options

    # TODO: define this as a property
    def display_user_agent(self) -> str:
        """
        Displays the browser's user agent if the browser was launched.
        :return: the user agent name or that "no webdriver started"
        """
        self.assert_wd_active()
        return self.wd.execute_script("return navigator.userAgent")

    def assert_wd_active(self) -> None:
        assert self.wd, "you must run the method start_chrome first"

    def set_headless(self) -> None:
        """
        Configures chrome to be in headless mode (essential to run scraper in server)
        """
        assert self.wd is None, "set_headless must be ran before start_chrome"
        # Headless mode doesn't open a browser window when crawling the web
        self.chrome_options.add_argument('--headless')
        # These options are required to run the scraper on a server
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        # In Docker dev-shm is too small and the scraper will crash for big sites
        # unless this option is active
        self.chrome_options.add_argument('--disable-dev-shm-usage')

    def start_chrome(self) -> None:
        """
        Launches Chrome with the specified configuration
        """
        self.wd = webdriver.Chrome(self.config.DRIVER_PATH, options=self.chrome_options)

    def get(self, *args, **kwargs):
        self.assert_wd_active()
        self.wd.get(*args, **kwargs)

    def quit(self) -> None:
        self.assert_wd_active()
        self.wd.quit()

    def sleep(self) -> float:
        try:
            sleep_time: Numeric = uniform(
                self.sleep_pattern_seconds[0],
                self.sleep_pattern_seconds[1]
            )
        except (TypeError, IndexError):
            sleep_time: Numeric = self.sleep_pattern_seconds
        time.sleep(sleep_time)
        return sleep_time

    def sanity_testing(self, quit_after: bool = True) -> str:
        self.get('http://example.com/')
        title: str = self.wd.find_element(By.XPATH, '//h1').text
        if quit_after:
            self.quit()
        return title


class WortenScraper(Scraper):
    def __init__(self,
                 config: Type[spc.WortenSpConfig],
                 load_wait_seconds: Union[int, float] = 30,
                 sleep_pattern_seconds: Union[Numeric, NumericIter] = (10, 33),
                 ) -> None:
        super().__init__(config, load_wait_seconds, sleep_pattern_seconds)
        self.config: Type[spc.WortenSpConfig] = config
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
        self.assert_wd_active()
        logger.info("scrape: close cookie pop-up (if exists)")
        # find button
        try:
            button = self.wd.find_element(By.XPATH, "//*[contains(text(), 'Aceitar Tudo')]")
        except NoSuchElementException:
            pass
        else:
            # click to accept cookies
            button.click()

    def _create_lvl3_product_xpath(self) -> str:
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

    def find_section_urls(self) -> None:
        """
        Goes to the product page and populates categories_to_scrape with the names and
        URLs of the categories (level 3) to scrape
        """
        self.assert_wd_active()
        logger.info("scrape: start searching section URLs")
        self.wd.get(self.config.PRODUCT_PAGE_URL)
        lvl3_xpath = self._create_lvl3_product_xpath()
        try:
            _ = (
                WebDriverWait(self.wd, self.load_wait_seconds)
                .until(
                    EC.presence_of_element_located((By.XPATH, lvl3_xpath))
                )
            )
        except TimeoutException:
            #self.wd.save_screenshot(constants.MAIN_DIR / "screenshots/worten_categories.png")
            if "captcha" in self.wd.page_source.lower():
                raise ScraperBlockedError('got Worten captcha')
            raise TimeoutException("Categories page no properly loaded")

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
        self.assert_wd_active()
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
        logger.info('scrape: start section extraction')
        self.assert_wd_active()
        section_html = []
        p = 1
        self.wd.get(section_url)
        while p < self.config.MAX_PAGES_PER_SECTION:
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
            if p == self.config.MAX_PAGES_PER_SECTION:
                logger.info("scrape: the section has more pages then the search limit")
            p += 1
        return section_html

    def get_entire_site(self) -> None:
        """
        Scrapes entire Worten site. It first goes to the product home page which contains
        all the categories of products organised in a hierarchical format.
        :return:
        """
        self.assert_wd_active()
        logger.info("scrape: starting Worten full site parsing")
        # got to main page and accept cookies (seems more human to start there)
        self.get(self.config.HOME_PAGE)
        self.accept_cookies()

        # get section URLs
        if not self.categories_to_scrape:
            self.find_section_urls()

        # scrape each section
        for category, info in self.categories_to_scrape.items():
            logger.info(f"scrape: category {category},\nwith URL {info['url']}")
            if self.sample_share < 1 and uniform(0, 1) > self.sample_share:
                logger.info(f"scrape: category sampled out, skipping")
                continue
            section_html: list[str] = self.get_section(info["url"])
            self.site_html[category] = section_html
            info["pages"] = len(section_html)
            logger.info(f"scrape: {len(section_html)} HTML pages download")
        logger.info(f"scrape: finished site scrape with sample parameter {self.sample_share}")
