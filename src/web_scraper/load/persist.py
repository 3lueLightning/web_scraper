import pickle

from datetime import datetime

from web_scraper import config


class Persist:
    def __init__(
            self,
            data_folder: str) -> None:
        self.created_at = datetime.now().strftime("%Y%m%d_%H%S")
        self.data_folder = data_folder / self.created_at

    def save_pickle(self, obj, name, mode='w'):
        with open(self.data_folder / name, mode) as file:
            pickle.dump(obj, file)

    def load_pickle(self, name, mode='r'):
        with open(self.data_folder / name, mode) as file:
            return pickle.load(file)
