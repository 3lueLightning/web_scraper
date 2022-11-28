"""
Custom errors definition
"""

from selenium.common.exceptions import NoSuchElementException

class ScraperBlockedError(Exception):
    pass

class NoPopUpError(NoSuchElementException):
    pass
