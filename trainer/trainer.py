from typing import List

import torch
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
)

from chess_dataset import T5ChessDataset


class T5ChessTrainer:
    def __init__(self, model_name: str = 't5-small', special_tokens: List[str] = None, model_dir: str = None):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name, additional_special_tokens=special_tokens)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if model_dir:
            self.model = T5ForConditionalGeneration.from_pretrained(model_dir)
        else:
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)

    def train(self, data_dir: str, output_dir: str, batch_size: int = 8, num_epochs: int = 3):

        # todo: improve this
        train_dataset = T5ChessDataset(data_dir=data_dir, data_type="train", tokenizer=self.tokenizer)
        val_dataset = T5ChessDataset(data_dir=data_dir, data_type="valid", tokenizer=self.tokenizer)

        # todo: use adafactor optimizer and use config
        training_args = Seq2SeqTrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            resume_from_checkpoint=output_dir,
            restore_callback_states_from_checkpoint=True,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            eval_steps=300,
            save_steps=200,
            save_total_limit=2,
            logging_dir=f"{output_dir}/logs",
            logging_steps=100,
            learning_rate=3e-4,
            weight_decay=0.01,
            fp16=True,
            report_to="tensorboard",
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )

        trainer.train()

        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)


def main():
    # todo: use config
    special_tokens = ["<EOC>", "<EOP>", "<EOM>", "<EOMH>"]
    generator = T5ChessTrainer(model_name='t5-small', special_tokens=special_tokens)
    generator.train(
        data_dir="../scraper/preprocessed_files",
        output_dir="./chess_commentary_model",
        batch_size=12,
        num_epochs=5
    )


if __name__ == "__main__":
    main()
