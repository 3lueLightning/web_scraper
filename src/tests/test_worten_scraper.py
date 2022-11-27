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
