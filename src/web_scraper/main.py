from web_scraper import config
from web_scraper.support import utils
from web_scraper.transform import content_parser
from web_scraper.extract import scraper_worten
from web_scraper.extract.scraper_config import (
    WORTEN_SP_CONFIG_PER_SYSTEM,
    WortenSpConfig
)


logger = utils.log_ws(__name__)


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


def run_scraper():
    WORTEN_SP_CONFIG: WortenSpConfig = WORTEN_SP_CONFIG_PER_SYSTEM[config.MODE]

    logger.info(WORTEN_SP_CONFIG)
    if WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION < 50:
        logger.warning(WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION)

    scraper = scraper_worten.WortenScraper(WORTEN_SP_CONFIG)
    if config.HEADLESS_MODE:
        scraper.set_headless()
    scraper.start_chrome()

    """
    import pickle
    with open(config.MAIN_DIR / 'data' / 'categories_scrape.pkl', 'rb') as file:
        previous_categories_scrape = pickle.load(file)
    previous_categories = [elem['section_specs']['name'] for elem in previous_categories_scrape]
    import pdb; pdb.set_trace()
    """

    categories_scrape = []
    for category in scraper.get_site():
        categories_scrape.append(category)

    import pickle
    with open(config.MAIN_DIR / 'data' / 'categories_scrape.pkl', 'wb') as file:
        pickle.dump(categories_scrape, file)

    scraper.quit()


if __name__ == '__main__':
    run_scraper()
