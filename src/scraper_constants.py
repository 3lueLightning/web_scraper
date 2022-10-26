BROWSER_DRIVER_PATH = '/Users/diogo/Dev/web_scraper_project/web_scraper/chromedriver_mac64_10605249' #_mod
#BROWSER_DRIVER_PATH = '/usr/local/bin/chromedriver'

POPULAR_USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0"
  "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; Trident/5.0)"
  "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0; MDDCJS)"
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
  "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"
]

# For local testing
POPULAR_USER_AGENTS = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"]

# For Docker
POPULAR_USER_AGENTS = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36']

# WORTEN specific parameters
HOME_PAGE = "https://www.worten.pt"
PRODUCT_PAGE_URL = 'https://www.worten.pt/diretorio-de-categorias'
N_ITEMS_WORTEN = 48
LVL2_CATEGORIES = ['Eletrodomésticos', 'TV, Vídeo e Som', 'Informática e Acessórios']
LVL3_REF = 'submenu-third-level'
LVL3_EXCLUDED_CATEGORIES = ['Ver Todos', 'Ajuda-me a escolher']
MAX_PAGES_PER_SECTION = 4 # 100
