import json
import logging
import os
from pathlib import Path

import yaml
from nltk.tokenize import word_tokenize

os.mkdir("./logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/preprocess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def map_name(x: str) -> str:
    piece_map = {
        "K": "king",
        "Q": "queen",
        "R": "rook",
        "B": "bishop",
        "N": "knight"
    }
    return piece_map.get(x, f"pawn {x}")


def diff_string(previous_state, current_state):
    board_changes = []
    for prev, curr in zip(previous_state, current_state):
        if 'piece' not in prev and 'piece' not in curr:
            change = 'eps'
        elif 'piece' in prev and 'piece' not in curr:
            change = '-' + prev['piece']
        elif 'piece' not in prev and 'piece' in curr:
            change = '+' + curr['piece']
        else:
            change = 'eps' if prev['piece'] == curr['piece'] else '+' + curr['piece']
        board_changes.append(change)
    return " ".join(board_changes)


def parse_move(move: str) -> str:
    move = move.rstrip("+#")
    if "x" not in move:
        if len(move) == 2:
            return f"_pawn {move}"
        elif len(move) == 3:
            return f"_{map_name(move[0])} {move[1:]}"
    if "x" in move:
        return f"_{map_name(move[0])} X {move[2:]}"
    return "_<strangeMove>"


def parse_move_string(moves: str) -> list:
    moves = moves.split("\n")[0]  # remove layout from moves
    moves = moves.split()
    move_sequence = []

    if "..." in moves[0]:
        moves = moves[1:]
        start_index = 2
    else:
        start_index = 0

    for move in moves:
        if start_index % 3 != 0:
            color = "white" if start_index % 3 == 1 else "black"
            move_sequence.append(f"{color} {parse_move(move)} <EOM>")
        start_index += 1

    return move_sequence


class Preprocess:
    def __init__(self, config):
        self.input_dir = Path(config['parse_output_dir'])
        self.output_dir = Path(config['preprocess_output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._split_data_path = Path(config['split_data_path'])
        self._all_links_path = Path(config['saved_links_path'])
        self._start_state_path = Path(config['start_state_path'])
        self.split_data: dict[str, list[int]] = self.load_split_data()
        self.link_page_counts = self.load_link_page_counts()
        self.start_state = self.load_start_state()

    def load_start_state(self):
        if self._start_state_path.exists():
            with open(self._start_state_path, 'r') as f:
                return json.load(f)
        return {}

    def load_link_page_counts(self) -> list[int]:
        if self._all_links_path.exists():
            with open(self._all_links_path, 'r') as f:
                data = json.load(f)
                return list(data.values())
        return []

    def load_split_data(self):
        split_data = {}
        if self._split_data_path.exists():
            with open(self._split_data_path, 'r') as f:
                split_data = json.load(f)
        return split_data

    def process(self):
        for key, indices in self.split_data.items():
            logger.info(f"Processing {key}")

            out_file_multi_che = self.output_dir / f"{key}.che-eng.multi.che"
            out_file_multi_en = self.output_dir / f"{key}.che-eng.multi.en"
            out_file_single_che = self.output_dir / f"{key}.che-eng.single.che"
            out_file_single_en = self.output_dir / f"{key}.che-eng.single.en"

            multi_che, multi_en, single_che, single_en = [], [], [], []

            for index in indices:
                page_length = self.link_page_counts[index]
                for page_no in range(page_length):
                    logger.info(f"Processing [{key}] - {index}_{page_no}")

                    page_obj_name = self.input_dir / f"saved{index}_{page_no}.json"
                    try:
                        with open(page_obj_name, 'r') as f:
                            data = json.load(f)
                    except FileNotFoundError:
                        logger.error(f"File {page_obj_name} not found")
                        break

                    start_state = self.start_state
                    for elem in data:
                        moves = elem['moves']
                        board_state = elem['board']
                        comment = elem['comment'].encode('ascii', 'replace').strip().decode('ascii')
                        comment_words = " ".join(word_tokenize(comment))
                        current_state_str = " ".join([x['piece'] if 'piece' in x else 'eps' for x in board_state])
                        start_state_str = " ".join(
                            [x['piece'] if 'piece' in x else 'eps' for x in start_state['board']])
                        move_sequence = parse_move_string(moves)
                        src_str = f"{current_state_str} <EOC> {start_state_str} <EOP> {' '.join(move_sequence)} <EOMH>"
                        tgt_str = comment_words
                        if len(move_sequence) == 1:
                            single_che.append(src_str + '\n')
                            single_en.append(tgt_str + '\n')

                        multi_che.append(src_str + '\n')
                        multi_en.append(tgt_str + '\n')

                        start_state = elem

            with open(out_file_multi_che, 'w') as mc, open(out_file_multi_en, 'w') as me, \
                    open(out_file_single_che, 'w') as sc, open(out_file_single_en, 'w') as se:
                mc.writelines(multi_che)
                me.writelines(multi_en)
                sc.writelines(single_che)
                se.writelines(single_en)

            logger.info(f"Processed {key}")


def main():
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    preprocessor = Preprocess(config)
    preprocessor.process()


if __name__ == "__main__":
    main()
