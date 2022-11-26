from web_scraper import (
    utils,
    config,
    worten_scraper,
    content_parser
)
from web_scraper.scraper_config import WORTEN_SP_CONFIG_PER_SYSTEM


logger = utils.log_ws(__name__)


def run_scraper():
    WORTEN_SP_CONFIG = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]

    logger.info(WORTEN_SP_CONFIG)
    if WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION < 50:
        logger.warning(WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION)

    scraper = worten_scraper.WortenScraper(WORTEN_SP_CONFIG)
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


if __name__ == '__main__':
    run_scraper()