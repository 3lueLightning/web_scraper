import pytest

from web_scraper import (
    config,
    scraper_base,
    scraper_worten,
)
from web_scraper.scraper_config import (
    WORTEN_SP_CONFIG_PER_SYSTEM,
    WortenSpConfig
)


@pytest.fixture
def base_scraper() -> scraper_worten.WortenScraper:
    WORTEN_SP_CONFIG: WortenSpConfig = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]
    scraper = scraper_base.Scraper(WORTEN_SP_CONFIG)
    scraper.set_headless()
    scraper.start_chrome()
    return scraper


@pytest.fixture
def worten_scraper() -> scraper_worten.WortenScraper:
    WORTEN_SP_CONFIG: WortenSpConfig = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]
    scraper = scraper_worten.WortenScraper(WORTEN_SP_CONFIG)
    scraper.set_headless()
    scraper.start_chrome()
    scraper.get_home_page()
    scraper.rm_cookies_pop_up()
    return scraper
