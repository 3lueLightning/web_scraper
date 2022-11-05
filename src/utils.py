import csv
import json
import copy
import logging

from pathlib import Path
from dataclasses import field
from typing import Union, Any

import boto3

import constants


# Data type definitions
Numeric = Union[int, float]
# Numeric iterable type
NumericIter = Union[Numeric, list[Numeric], tuple[Numeric]]


class SetLogger:
    """
    Creates logger attribute with 2 optional handlers:
        * one to log to the console
        * one to log to a file
    :param name: logger name (typically __name__)
    :param level: general logger level
    """
    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self.name: str = name
        self.logger_lvl: int = level
        self.logger: logging.Logger = self._set_logger()

    @staticmethod
    def _set_format(handler: logging.Handler) -> None:
        formatter: logging.Formatter = logging.Formatter(
            fmt='{asctime} - {name} - {levelname}: {message}',
            datefmt="%Y/%m/%d %H:%M:%S",
            style="{"
        )
        handler.setFormatter(formatter)

    def _set_logger(self) -> logging.Logger:
        logger: logging.Logger = logging.getLogger(self.name)
        logger.setLevel(self.logger_lvl)
        return logger

    def to_console(self, level: int = logging.INFO) -> None:
        ch: logging.Handler = logging.StreamHandler()
        ch.setLevel(level)
        # add formatter to ch
        self._set_format(ch)
        # add ch to logger
        self.logger.addHandler(ch)

    def to_file(self, name: Union[str, Path], level: int = logging.INFO):
        fh: logging.Handler = logging.FileHandler(name)
        fh.setLevel(level)
        # add formatter to ch
        self._set_format(fh)
        # add ch to logger
        self.logger.addHandler(fh)


def log_ws(name: str) -> logging.Logger:
    logger = SetLogger(name, constants.LOG_LVL)
    logger.to_console(constants.LOG_LVL)
    logger.to_file(constants.LOG_FN, constants.LOG_LVL)
    return logger.logger


def get_aws_credentials(file_name: str) -> dict[str, str]:
    with open(file_name) as file:
        csv_reader = csv.DictReader(file, delimiter=',')
        credentials = next(csv_reader)
    return credentials


def write_to_s3(data: Any) -> dict[str, Any]:
    aws_credentials = get_aws_credentials(constants.MAIN_DIR / 'web_scraper_accessKeys.csv')

    #Creating Session With Boto3.
    session = boto3.Session(
        aws_access_key_id=aws_credentials['Access key ID'],
        aws_secret_access_key=aws_credentials['Secret access key']
    )
    #Creating S3 Resource From the Session.
    s3 = session.resource('s3')
    s3_object = s3.Object('shop-scrape', 'worten_products')
    response = s3_object.put(Body=json.dumps(data))
    return response


def default_field(x: Any):
    return field(default_factory=lambda: copy.copy(x))
