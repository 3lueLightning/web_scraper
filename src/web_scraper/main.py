from web_scraper import config
from web_scraper.support import utils
from web_scraper.transform import content_parser
from web_scraper.extract import scraper_worten
from web_scraper.extract.scraper_config import (
    WORTEN_SP_CONFIG_PER_SYSTEM,
    WortenSpConfig
)
from web_scraper.load.persist import Persist


logger = utils.log_ws(__name__)


def run_scraper():
    WORTEN_SP_CONFIG: WortenSpConfig = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]
    logger.info(WORTEN_SP_CONFIG)

    scraper = scraper_worten.WortenScraper(WORTEN_SP_CONFIG)
    if config.HEADLESS_MODE:
        scraper.set_headless()
    scraper.start_chrome()

    persist = Persist(config.DATA_DIR, config.REFERENCE_TIME)
    parser = content_parser.WortenHtmlParser({"date": config.REFERENCE_TIME})
    for category in scraper.get_site(select_categories=["lavar", "secar"]):
        persist.save_section(category)
        site_prods = parser.parse_category(scraper.site_html)
        print(site_prods)  # TODO: persist parsed products


if __name__ == '__main__':
    run_scraper()
