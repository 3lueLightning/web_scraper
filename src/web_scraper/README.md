Developing:  
docker build -t worten_scraper:0.1 .  
docker run -it -v ~/Dev/web_scraper_project/web_scraper/src:/home/web_scraper/src worten_scraper:0.1 /bin/bash  
python src/main.py  
or  
docker run -d worten_scraper:0.1  

docker run -it worten_scraper:0.1 /bin/bash  
