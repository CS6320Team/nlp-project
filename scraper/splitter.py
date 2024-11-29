import json
import random
from pathlib import Path

import yaml


class LinkSplitter:
    def __init__(self, config_path):
        self.config = yaml.safe_load(Path(config_path).read_text())
        self.link_indices = self._load_link_indices()
        self.train_ratio = self.config['train_ratio']
        self.valid_ratio = self.config['val_ratio']
        self.random_seed = self.config['random_seed']

    def _load_link_indices(self) -> list[int]:
        """Load URLs from saved files."""
        try:
            with open(self.config['saved_links_path'], 'r') as f:
                link_size = len(json.load(f))
                return list(range(link_size))
        except FileNotFoundError:
            return []

    def split_and_save_links(self) -> None:
        train_links, valid_links, test_links = self.split_links()
        self.save_split_links(train_links, valid_links, test_links)

    def split_links(self) -> tuple[list[int], list[int], list[int]]:
        random.seed(self.random_seed)
        random.shuffle(self.link_indices)

        train_length = int(self.train_ratio * len(self.link_indices))
        valid_length = int(self.valid_ratio * len(self.link_indices))

        train_links = [self.link_indices[i] for i in range(train_length)]
        valid_links = [self.link_indices[i] for i in range(train_length, valid_length + train_length)]
        test_links = [self.link_indices[i] for i in range(valid_length + train_length, len(self.link_indices))]

        return train_links, valid_links, test_links

    def save_split_links(self, train_links, valid_links, test_links):
        split_data = {
            'train': train_links,
            'valid': valid_links,
            'test': test_links
        }
        with open(self.config['split_data_path'], 'w') as f:
            json.dump(split_data, f, indent=2)


def main():
    splitter = LinkSplitter("./config.yaml")
    splitter.split_and_save_links()


if __name__ == "__main__":
    main()
