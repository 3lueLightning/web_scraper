import csv
import json
import copy
import logging

from pathlib import Path
from dataclasses import field
from typing import Union, Any
from datetime import datetime

import boto3

from web_scraper import config


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
    logger = SetLogger(name, config.LOG_LVL)
    logger.to_console(config.LOG_LVL)
    logger.to_file(config.LOG_FN, config.LOG_LVL)
    return logger.logger


def get_aws_credentials(file_name: str) -> dict[str, str]:
    with open(file_name) as file:
        csv_reader = csv.DictReader(file, delimiter=',')
        credentials = next(csv_reader)
    return credentials


def write_to_s3(data: Any) -> tuple[str, dict[str, Any]]:
    aws_credentials = get_aws_credentials(config.MAIN_DIR / 'web_scraper_accessKeys.csv')

    #Creating Session With Boto3.
    session = boto3.Session(
        aws_access_key_id=aws_credentials['Access key ID'],
        aws_secret_access_key=aws_credentials['Secret access key']
    )
    #Creating S3 Resource From the Session.
    s3 = session.resource('s3')
    datetime_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    obj_name = f'worten_products{datetime_now}'
    s3_object = s3.Object('shop-scrape', obj_name)
    response = s3_object.put(Body=json.dumps(data))
    return obj_name, response


def read_from_s3(obj_name: str) -> dict[str, Any]:
    aws_credentials = get_aws_credentials(config.MAIN_DIR / 'web_scraper_accessKeys.csv')

    #Creating Session With Boto3.
    session = boto3.Session(
        aws_access_key_id=aws_credentials['Access key ID'],
        aws_secret_access_key=aws_credentials['Secret access key']
    )
    #Creating S3 Resource From the Session.
    s3 = session.resource('s3')
    s3_object = s3.Object('shop-scrape', obj_name)
    response = s3_object.get()['Body'].read().decode('utf-8')
    return json.loads(response)


def default_field(x: Any):
    return field(default_factory=lambda: copy.copy(x))
