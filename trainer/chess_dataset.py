import os

from torch.utils.data import Dataset


class T5ChessDataset(Dataset):
    def __init__(self,
                 data_dir: str,
                 data_type: str,
                 tokenizer,
                 max_input: int = 544,
                 max_output: int = 256,
                 prefix: str = "Generate commentary: "):

        self.tokenizer = tokenizer
        self.max_input = max_input
        self.max_output = max_output

        if data_type not in {'train', 'valid', 'test'}:
            raise ValueError(f"Invalid data type: {data_type}")

        input_file = os.path.join(data_dir, f"{data_type}.che-eng.multi.che")
        target_file = os.path.join(data_dir, f"{data_type}.che-eng.multi.en")

        if not os.path.exists(input_file) or not os.path.exists(target_file):
            raise ValueError(f"Data files not found for data type: {data_type}")

        with open(input_file, "r") as f:
            self.input_texts = [prefix + line.strip() for line in f.readlines()]

        with open(target_file, "r") as f:
            self.target_texts = [line.strip() for line in f.readlines()]

        if len(self.input_texts) != len(self.target_texts):
            raise ValueError("Input and target text files have different lengths.")

    def __len__(self):
        return len(self.input_texts)

    def __getitem__(self, idx):
        inputs = self.tokenizer(
            self.input_texts[idx],
            max_length=self.max_input,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        targets = self.tokenizer(
            self.target_texts[idx],
            max_length=self.max_output,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': targets['input_ids'].squeeze()
        }
