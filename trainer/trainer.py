import os
from dataclasses import dataclass, field
from typing import List

import evaluate
import nltk
import torch
from datasets import DatasetDict
from transformers import (
    T5Tokenizer, DataCollatorForSeq2Seq,
    T5ForConditionalGeneration, Seq2SeqTrainingArguments, Seq2SeqTrainer
)

from chess_dataset import load_dataset


@dataclass
class T5ChessTrainerArgs:
    model_name: str = "google/flan-t5-small"
    special_tokens: List[str] = field(default_factory=lambda: ["<EOC>", "<EOP>", "<EOM>", "<EOMH>"])
    model_dir: str = "./chess_model"
    prefix: str = "Generate chess commentary: "
    num_epochs: int = 5
    max_input_length: int = 640
    max_output_length: int = 256
    input_column: str = "moves"
    target_column: str = "commentary"


class T5ChessTrainer:
    def __init__(self, args: T5ChessTrainerArgs):
        self.args = args
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        if os.path.exists(args.model_dir):
            self.model = T5ForConditionalGeneration.from_pretrained(args.model_dir)
        else:
            self.model = T5ForConditionalGeneration.from_pretrained(args.model_name)
        self.model.to(self.device)
        self.model.generation_config.max_new_tokens = args.max_output_length
        self.model.generation_config.min_new_tokens = 10

        # load tokenizer
        self.tokenizer = T5Tokenizer.from_pretrained(
            args.model_name,
            additional_special_tokens=args.special_tokens,
            legacy=False
        )

        self.rouge_metric = evaluate.load("rouge")

    def preprocess(self, examples):
        inputs = [f"{self.args.prefix.strip()} {doc.strip()}" for doc in examples[self.args.input_column]]
        model_inputs = self.tokenizer(inputs, max_length=self.args.max_input_length, truncation=True)
        labels = self.tokenizer(
            text_target=examples[self.args.target_column],
            max_length=self.args.max_output_length,
            truncation=True
        )
        model_inputs["labels"] = [
            [(l if l != self.tokenizer.pad_token_id else -100) for l in label] for label in labels["input_ids"]
        ]
        return model_inputs

    # todo: fix
    def rouge_eval(self, predictions, references):
        rouge_output = self.rouge_metric.compute(
            predictions=predictions,
            references=references,
            use_stemmer=True
        )
        return rouge_output

    def train(self, data_set: DatasetDict):
        tokenized_dataset = data_set.map(
            self.preprocess,
            batched=True,
            num_proc=8,
            remove_columns=[self.args.input_column, self.args.target_column]
        )

        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            pad_to_multiple_of=8,
            label_pad_token_id=-100
        )

        training_args = Seq2SeqTrainingArguments(
            output_dir=self.args.model_dir,
            num_train_epochs=self.args.num_epochs,
            per_device_train_batch_size=12,
            per_device_eval_batch_size=12,
            eval_strategy="steps",
            optim="adafactor",
            learning_rate=1e-4,
            weight_decay=1e-2,
            save_total_limit=2,
            eval_steps=1500,
            save_steps=1500,
            logging_steps=100,
            logging_dir=f"{self.args.model_dir}/logs",
            predict_with_generate=True,
            bf16=True,
            report_to="tensorboard",
            load_best_model_at_end=True,
            resume_from_checkpoint=self.args.model_dir,
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset["train"],
            eval_dataset=tokenized_dataset["valid"],
            data_collator=data_collator,
        )

        trainer.train()

        self.model.save_pretrained(self.args.model_dir)
        self.tokenizer.save_pretrained(self.args.model_dir)

        trainer.save_model(self.args.model_dir)

    def generate(self, moves: str):
        input_text = f"{self.args.prefix.strip()} {moves.strip()}"

        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=self.args.max_input_length
        )

        inputs = {key: value.to(self.model.device) for key, value in inputs.items()}

        outputs = self.model.generate(
            **inputs,
            max_length=self.args.max_output_length,
            num_beams=4,
            early_stopping=True
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


def main():
    nltk.download("punkt", quiet=True)
    dataset = load_dataset("../scraper/preprocessed_files", "multi")
    model = T5ChessTrainer(args=T5ChessTrainerArgs())
    model.train(dataset)


if __name__ == "__main__":
    main()
