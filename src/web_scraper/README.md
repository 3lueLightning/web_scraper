Developing:  
docker build -t worten_scraper:0.1 .  
docker run -it -v ~/Dev/web_scraper_project/web_scraper/src:/home/web_scraper/src worten_scraper:0.1 /bin/bash  
python src/main.py  
or  
docker run -d worten_scraper:0.1  

docker run -it worten_scraper:0.1 /bin/bash  



Improvements:
use

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

instead of 
```python
self.wd = webdriver.Chrome(self.config.DRIVER_PATH, options=self.chrome_options)
```

but watch out, you have to make sure you set the user agent properly afterwards