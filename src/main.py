from datetime import datetime

import utils
import constants
import scraper_def
import content_parser
import scraper_constants


logger = utils.log_ws(__name__)

if scraper_constants.MAX_PAGES_PER_SECTION < 50:
    logger.warning(scraper_constants.MAX_PAGES_PER_SECTION)

scraper = scraper_def.WortenScraper()
if constants.HEADLESS_MODE:
    scraper.set_headless()
scraper.activate_sampling(0.05)
logger.info(scraper.display_user_agent())

scraper.get_entire_site()
scraper.quit()
logger.info('Finished scraping Worten')


scrape_metadata = {
    'shop': 'worten',
    'date': '2022/10/10' # datetime.now().strftime("%Y/%m/%d")
}
parser = content_parser.WortenHtmlParser(scrape_metadata)
site_prods = parser.parse_site(scraper.site_html)
logger.info('Finished parsing Worten')
utils.write_to_s3(site_prods)


