"""
Unit tests for the Worten Scraper
"""
import pytest

@pytest.mark.parametrize(
    ('section_name', 'n_pages_ref'),
    [
        ('https://www.worten.pt/tv-video-e-som/tvs/tv-media-polegada', 8),
        ('https://www.worten.pt/grandes-eletrodomesticos/maquinas-de-roupa/maquinas-de-lavar-roupa', 3),
        ('https://www.worten.pt/search?query=kit+mãos+livres+bluetooth', 1)
    ]
)
def test_count_pages(worten_scraper, section_name, n_pages_ref) -> None:
    worten_scraper.get(section_name)
    n_pages = worten_scraper.count_pages()
    assert n_pages == n_pages_ref, f"expected {n_pages_ref} for {section_name} got {n_pages} instead"


def test_find_lvl3_category_urls(worten_scraper) -> None:
    worten_scraper.find_lvl3_category_urls()
    lvl3_categories = worten_scraper.lvl3_categories
    assert len(lvl3_categories.keys()) > 0, "no lvl3 categories returned"
    urls = [category["url"] for category in lvl3_categories.values() if category.get("url")]
    assert len(urls) == len(lvl3_categories.keys()), "there are not as many urls as categories"


def test_site_scrape(worten_scraper) -> None:
    select_categories_pages = [
        ("Máquinas", 3),
        ("Mini Bar", 1),
        ("Máquinas Automáticas", 5)
    ]
    select_categories = [name for name, _ in select_categories_pages]
    category_scrapes: list = []
    for category in worten_scraper.get_site(select_categories):
        category_scrapes.append(category)

    categories_html = [category["html"] for category in category_scrapes]
    assert len(category_scrapes) == len(select_categories), \
        "the number of categories in not the expected one"

    pages_html = [html for elem in categories_html for html in elem]
    assert all(
        [html_0 != html_1 for html_0, html_1 in zip(pages_html[:-1], pages_html[1:])]
    ), "some html pages are identical"

    n_pages = [category["section_specs"]['n_pages'] for category in category_scrapes]
    n_pages_scraped = [category['metadata']['n_pages_scraped'] for category in category_scrapes]
    assert [
        n1 == n2 == len(html) == ref[1]
        for n1, n2, html, ref in zip(n_pages, n_pages_scraped, pages_html, select_categories_pages)
    ], "the number of pages in the section, pages scraped (in metadata) and html pages is different"
