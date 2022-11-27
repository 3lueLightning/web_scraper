"""
Test the base scraper, parent class of the Worten scraper
"""

def test_example_com_connection(base_scraper)-> None:
    assert base_scraper.sanity_test(), "Failed to scrape Example.com"
