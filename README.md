# MAGNUS: AI-Powered Chess Assistant

An AI-powered chess assistant that combines Stockfish, NLP, and LangChain to provide interactive gameplay, game
analysis, and insightful commentary.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Example Commands](#example-commands)
- [Scraping and Data Preparation](#scraping-and-data-preparation)
- [Training](#training)
- [Demo](#demo)

---

## Introduction

MAGNUS is a cutting-edge Chess Analysis Assistant designed for players of all skill levels. Leveraging **Stockfish** for
accurate game evaluations, **Natural Language Processing (NLP)** for human-like commentary, and **LangChain** for smooth
integration, MAGNUS elevates your chess experience.

Whether you are a beginner or an expert, MAGNUS helps you understand your games better, refine your strategies, and
improve your skills.

---

## Features

- **Move-by-Move Analysis**: Get detailed, strategy-focused explanations for each move.
- **Question Answering**: Ask questions like, "Why is this move good?" or "What’s the best next move?" and receive
  clear, insightful answers.
- **Interactive Gameplay**: Play against Stockfish while receiving real-time suggestions and tips.
- **Custom Puzzles**: Practice with puzzles tailored to your skill level, with hints and solutions.
- **User-Friendly Interface**: Includes a chessboard and chatbox for seamless interaction.

---

## Getting Started

### Prerequisites

Ensure you have the following:

- Python 3.8+
- **GPU** with at least 8GB VRAM for optimal performance
- OpenAI API key

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/CS6320Team/nlp-project.git
    cd nlp-project
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv env
    source env/bin/activate # or `env\Scripts\activate` on Windows
    ```

3. Install PyTorch ([instructions](https://pytorch.org/get-started/locally/)).

4. Install other required dependencies:
    ```bash
    pip install pandas PyQt6 python-dotenv stockfish chess langchain transformers zstandard
    ```

5. Install additional tools for scraping and fine-tuning:
    ```bash
    pip install beautifulsoup4 playwright nltk lxml evaluate datasets sentencepiece rouge-score absl-py protobuf tensorboard
    playwright install chromium
    ```

6. Set up **Stockfish**:
    - Download it from [Stockfish's official website](https://stockfishchess.org/download/).
    - Ensure it’s in your system path or specify its path in your `.env` file.

7. Configure the `.env` file using the provided `example.env`:
    ```plaintext
    OPENAI_API_KEY=<your-api-key>
    LICHESS_PUZZLE_DATASET_PATH=<path-to-puzzle-dataset>
    STOCKFISH_PATH=<path-to-stockfish-executable>
    OPENAI_MODEL=<model-name>
    ```

8. Launch the application:
    ```bash
    python ./chess_ui/main.py
    ```

---

### Usage

- Launch the application and start a new game against Stockfish.
- Interact with the assistant by asking questions or requesting analysis during the game.

---

### Example Commands

- "Move my pawn to e4."
- "Why is this move strong?"
- "What should I play next?"

---

## Scraping and Data Preparation

Follow these steps to prepare data for fine-tuning the model:

1. Navigate to the `scraper` directory.
2. Run `link_updater.py` to generate links (`./init_data/links.json`).
3. Run `scraper.py` to scrape pages (`./saved_files`).
4. Parse the pages using `parser.py` (`./parsed_files`).
5. Split the data with `splitter.py` (`./init_data/split_data.json`).
6. Preprocess the data using `preprocess.py` (`./preprocessed_file`).

---

## Training

Fine-tune the model for game commentary generation:

1. Navigate to the `trainer` directory.
2. Run `trainer.py` to start training. Monitor progress with **TensorBoard**.
3. Replace the model in the `chess_model` directory with the new trained model.

Update `chess_ui/main.py` to point to the updated model.

---

## Demo

Watch a [demo video](https://www.youtube.com/watch?v=BqDGz8EystM) showcasing MAGNUS in action!

![MAGNUS Demo](https://img.youtube.com/vi/BqDGz8EystM/0.jpg)

---

Inspired by [Chess Commentary Generation](https://github.com/harsh19/ChessCommentaryGeneration). Enjoy improving your
chess skills with MAGNUS!
