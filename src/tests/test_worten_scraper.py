"""
Unit tests for the Worten Scraper
"""

def test_get_page_count(worten_scraper) -> None:
    section_page_count = [
        ('https://www.worten.pt/tv-video-e-som/tvs/tv-media-polegada', 8),
        ('https://www.worten.pt/grandes-eletrodomesticos/maquinas-de-roupa/maquinas-de-lavar-roupa', 3),
        ('https://www.worten.pt/search?query=kit+mãos+livres+bluetooth', 1)
    ]
    for section_name, n_pages_ref in section_page_count:
        worten_scraper.get(section_name)
        n_pages = worten_scraper.get_page_count()
        assert n_pages == n_pages_ref, f"expected {n_pages_ref} for {section_name} got {n_pages} instead"


def test_find_lvl3_category_urls(worten_scraper) -> None:
    worten_scraper.find_lvl3_category_urls()
    lvl3_categories = worten_scraper.lvl3_categories
    assert len(lvl3_categories.keys()) > 0, "no lvl3 categories returned"
    urls = [category["url"] for category in lvl3_categories.values() if category.get("url")]
    assert len(urls) == len(lvl3_categories.keys()), "there are not as many urls as categories"
