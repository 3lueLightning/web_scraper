"""
Defines the basic Scraper class

It implements so of the ideas in this link about masking a web scraper
https://www.php8legs.com/en/php-web-scraper/51-how-to-avoid-selenium-webdriver-from-being-detected-as-bot-or-web-spider
"""
import time
from random import uniform
from typing import Union, Type, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By

from web_scraper import utils
import web_scraper.scraper_config as spc
from web_scraper.utils import Numeric, NumericIter


logger = utils.log_ws(__name__)


class ScraperBlockedError(Exception):
    pass


class Scraper:
    """
    Base Scraper class
    """
    def __init__(
            self,
            config: Type[spc.ScraperConfig],
            load_wait_seconds: Numeric = 30,
            sleep_pattern_seconds: Union[Numeric, NumericIter] = (2, 4),
            ) -> None:
        self.config: Type[spc.ScraperConfig] = config
        self.load_wait_seconds: Numeric = load_wait_seconds
        self.sleep_pattern_seconds: Union[Numeric, NumericIter] = sleep_pattern_seconds

        self.chrome_options: webdriver.ChromeOptions = self.__set_chrome_options()
        self.wd: Optional[webdriver.Chrome] = None
        self.sample_share: Numeric = 1

    def __set_chrome_options(self) -> webdriver.ChromeOptions:
        """
        Basic chrome configurations that should always be set
        :return: options to pass on browser setup
        """
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
        """
        Throttling the scraper either for a specific time or
        for a random time between a given range to emulate a human
        :return: the time it slept
        """
        try:
            sleep_time: Numeric = uniform(
                self.sleep_pattern_seconds[0],
                self.sleep_pattern_seconds[1]
            )
        except (TypeError, IndexError):
            sleep_time: Numeric = self.sleep_pattern_seconds
        time.sleep(sleep_time)
        return sleep_time

    def activate_sampling(self, share: float) -> None:
        """
        Select the probability with which each part of the site will be scraped.
        Useful for testing purposes
        :param share: which percentage between 0 and 1 to scrape
        """
        self.sample_share = share

    def sanity_testing(self) -> bool:
        """
        Validate that the scraper is functioning by checking that it
        got the correct title from example.com
        :return: True if it got the correct title false otherwise
        """
        self.get('http://example.com/')
        title: str = self.wd.find_element(By.XPATH, '//h1').text
        return title == 'Example Domain'
