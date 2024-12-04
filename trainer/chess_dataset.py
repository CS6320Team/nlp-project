import os

from datasets import DatasetDict, Dataset


def load_dataset(data_dir: str, data_format: str) -> DatasetDict:
    if data_format not in ['multi', 'single']:
        raise ValueError(f"Invalid data format: {data_format}")

    data_dict = {}
    for data_type in ['train', 'valid', 'test']:
        input_file = os.path.join(data_dir, f"{data_type}.che-eng.{data_format}.che")
        label_file = os.path.join(data_dir, f"{data_type}.che-eng.{data_format}.en")

        if not os.path.exists(input_file) or not os.path.exists(label_file):
            raise ValueError(f"Data files not found for data type: {data_type} and format: {data_format}")

        with open(input_file, 'r', encoding='utf-8') as f_in, open(label_file, 'r', encoding='utf-8') as f_lbl:
            inputs = f_in.read().splitlines()
            labels = f_lbl.read().splitlines()

        assert len(inputs) == len(labels), "Input and label files have different lengths!"

        data_dict[data_type] = Dataset.from_dict({
            'moves': inputs,
            'commentary': labels
        })

    return DatasetDict(data_dict)


def sample_dataset(data_set: DatasetDict, sample_percentage: float) -> DatasetDict:
    if sample_percentage <= 0 or sample_percentage > 1:
        raise ValueError(f"Invalid sample percentage: {sample_percentage}")
    sampled_data = {}
    for data_type in data_set.keys():
        sampled_data[data_type] = data_set[data_type].train_test_split(train_size=sample_percentage)['train']
    return DatasetDict(sampled_data)
