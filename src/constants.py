import logging
from pathlib import Path

HEADLESS_MODE = True  # False
# select either of: 'localhost', 'docker', 'aws'
MODE = 'docker'  # 'localhost'

POSSIBLE_MAIN_DIR = {
    'localhost': Path('/Users/diogo/Dev/web_scraper_project/web_scraper'),
    'docker': Path('/home/web_scraper'),
}
MAIN_DIR = POSSIBLE_MAIN_DIR[MODE]

LOG_LVL = logging.INFO
LOG_FN = MAIN_DIR / 'scraper.log'
