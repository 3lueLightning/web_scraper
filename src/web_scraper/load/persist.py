import pickle

from datetime import datetime
from typing import Optional
from pathlib import Path
from enum import Enum

from web_scraper.support import utils


logger = utils.log_ws(__name__)

class DataFolders(Enum):
    RAW = "raw"
    PROCESSED = "processed"
    #METADATA = 'metadata'


class Persist:
    def __init__(
            self,
            data_folder: Path,
            created_at: str) -> None:
        if created_at:
            self.time_ref = created_at
        else:
            self.time_ref = datetime.now().strftime("%Y%m%d_%H%S")
        self.data_folder = data_folder / self.time_ref
        self.raw_data = self.data_folder / DataFolders.RAW.value
        #self.metadata = self.data_folder / DataFolders.METADATA.value
        #self.processed_data = self.data_folder / DataFolders.PROCESSED.value
        self._create_dirs()

    def _create_dirs(self):
        self.raw_data.mkdir(exist_ok=True, parents=True)

    def save_section(self, section_scrape: Optional[dict]) -> None:
        if section_scrape is None:
            logger.warning("no section_scrape to save")
            return
        name = "_".join(
            [section_scrape["section_specs"][f"category_lvl{i}"] for i in range(1, 4)]
        ) + ".pkl"
        with open(self.raw_data / name, 'wb') as file:
            pickle.dump(section_scrape, file)

    def load_section(self, name) -> None:
        with open(self.raw_data / name, 'rb') as file:
            return pickle.load(file)

    def extracted_urls(self) -> list:
        if self.raw_data.glob('*.pkl'):
            urls = [
                self.load_section(file_name)['section_specs']['base_url']
                for file_name in self.raw_data.glob('*.pkl')
            ]
        else:
            urls = []
        return urls


