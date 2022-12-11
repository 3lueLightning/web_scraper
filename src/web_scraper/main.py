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
    urls_pre_extracted = persist.extracted_urls()
    for category in scraper.get_site(excluded_urls=urls_pre_extracted):
        persist.save_section(category)

    scraper.quit()


if __name__ == '__main__':
    run_scraper()



"""
def run_scraper_old():
    WORTEN_SP_CONFIG: WortenSpConfig = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]

    logger.info(WORTEN_SP_CONFIG)
    if WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION < 50:
        logger.warning(WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION)

    scraper = scraper_worten.WortenScraper(WORTEN_SP_CONFIG)
    if config.HEADLESS_MODE:
        scraper.set_headless()
    scraper.start_chrome()
    scraper.get_site()
    scraper.quit()
    scraper.save(config.MAIN_DIR / 'data' / 'site_html.pkl')

    scrape_metadata = {'shop': 'worten'}
    parser = content_parser.WortenHtmlParser(scrape_metadata)
    site_prods = parser.parse_site(scraper.site_html)
    utils.write_to_s3(site_prods)
    logger.info('The End')
"""