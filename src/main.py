"""
Developing:
docker build -t worten_scraper:0.1 .
docker run -it -v ~/Dev/web_scraper_project/web_scraper/src:/home/web_scraper/src worten_scraper:0.1 /bin/bash
python src/main.py
or
docker run -d worten_scraper:0.1

docker run -it worten_scraper:0.1 /bin/bash
"""

import utils
import constants
import scraper_def
import content_parser
from scraper_constants import WORTEN_SP_CONFIG_PER_SYSTEM


logger = utils.log_ws(__name__)

WORTEN_SP_CONFIG = WORTEN_SP_CONFIG_PER_SYSTEM[constants.MODE]

logger.info(WORTEN_SP_CONFIG)
if WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION < 50:
    logger.warning(WORTEN_SP_CONFIG.MAX_PAGES_PER_SECTION)

scraper = scraper_def.WortenScraper(WORTEN_SP_CONFIG)
if constants.HEADLESS_MODE:
    scraper.set_headless()
scraper.start_chrome()

scraper.activate_sampling(0.03)
scraper.get_entire_site()
scraper.quit()


scrape_metadata = {'shop': 'worten'}
parser = content_parser.WortenHtmlParser(scrape_metadata)
site_prods = parser.parse_site(scraper.site_html)
logger.info('Finished parsing Worten')
utils.write_to_s3(site_prods)
logger.info('The End')
