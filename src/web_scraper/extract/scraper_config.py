from abc import ABC
from dataclasses import dataclass

from web_scraper import config
from web_scraper.support.utils import default_field

# your user agent should be the same as the real Chrome, can find your installation's Chrome with this command
# echo navigator.userAgent | /opt/google/chrome/chrome --headless --repl
# or if you install jq:
# echo navigator.userAgent | /opt/google/chrome/chrome --headless --repl 2> /dev/null | sed 's/^>>> //' | jq -r .result.value
# and replace it in USER_AGENT


@dataclass(frozen=True)
class WortenSearchConfig:
    HOME_PAGE: str = "https://www.worten.pt"
    PRODUCT_PAGE_URL: str = 'https://www.worten.pt/diretorio-de-categorias'
    N_ITEMS_WORTEN: int = 48
    LVL2_CATEGORIES: list[str] = default_field(['Eletrodomésticos', 'TV, Vídeo e Som', 'Informática e Acessórios'])
    LVL3_REF: str = 'submenu-third-level'
    LVL3_EXCLUDED_CATEGORIES: list[str] = default_field(['Ver Todos', 'Ajuda-me a escolher'])
    MAX_PAGES_PER_SECTION: int = 2#5
    N_MAX_SECTION_FAIL = 100


@dataclass(frozen=True)
class ScraperConfig(ABC):
    DRIVER_PATH: str
    USER_AGENT: str


class WortenSpConfig(WortenSearchConfig, ScraperConfig):
    pass


class LocalhostWSpConfig(WortenSpConfig):
    DRIVER_PATH: str = config.MAIN_DIR / 'drivers' / 'chromedriver_mac64_10605249' #_mod
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"


class DockerWSpConfig(WortenSpConfig):
    DRIVER_PATH: str = '/usr/local/bin/chromedriver'
    USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.68 Safari/537.36"


WORTEN_SP_CONFIG_PER_SYSTEM: dict = {
    'localhost': LocalhostWSpConfig(),
    'docker': DockerWSpConfig()
}