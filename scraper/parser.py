import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import unicodedata
import yaml

from ChessCommentaryGeneration.Data.crawler.utilities import Utilities


def _board_cell_to_info(list_of_board_cells):
    ret = []
    column_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    row_names = ['1', '2', '3', '4', '5', '6', '7', '8']

    def get_piece_type(cell):
        color = "white" if int(cell['left_img']) == 0 else "black"
        piece_mapping = {
            '0': "king",
            '-30': "queen",
            '-60': "rook",
            '-90': "knight",
            '-120': "bishop",
            '-150': "pawn"
        }
        piece_type = piece_mapping.get(cell.get('top_img'), "unknown")
        return f"{color}_{piece_type}"

    for index, cur_cell in enumerate(list_of_board_cells):
        column = column_names[index // len(row_names)]
        row = row_names[index % len(row_names)]
        cell_info = {'location': f"{column}{row}"}

        if 'left_img' in cur_cell and 'top_img' in cur_cell:
            cell_info['piece'] = get_piece_type(cur_cell)

        ret.append(cell_info)

    return ret


# TODO: combine multi-page games into single json
class DataCollector:
    def __init__(self, config):
        self._utils = Utilities()
        self.input_dir = Path(config['scrape_output_dir'])
        self.output_dir = Path(config['parse_output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parse_error_file = Path(config['parse_error_path'])

    def _get_input_files(self) -> list:
        return [f for f in os.listdir(self.input_dir) if f.endswith(".html")]

    def _get_board_values(self, soup) -> list:
        divs = self._utils.getDivOfClass(soup, "cdiag_frame")
        if not divs:
            return []

        board = self._utils.getDivOfID(divs[0], "board")
        board_elements = self._utils.getDivAll(board[0], recursive=False)
        board_element_vals = []

        def parse_style(style):
            return {
                part.split(": ")[0].strip(): part.split(": ")[1].strip().replace("px", "")
                for part in style.split(";") if ": " in part
            }

        for ele in board_elements:
            ele_style_vals = parse_style(ele.get('style', ''))
            left, top = ele_style_vals.get('left'), ele_style_vals.get('top')
            if left and top:
                tmp = {'left': left, 'top': top}

                ele_img = self._utils.getImgAll(ele)
                if ele_img:
                    ele_img_style_vals = parse_style(ele_img[0].get('style', ''))
                    tmp['left_img'] = ele_img_style_vals.get('left')
                    tmp['top_img'] = ele_img_style_vals.get('top')

                board_element_vals.append(tmp)

        return board_element_vals

    def process_file(self, file):
        try:
            print(f"Processing file {file}")
            file_path = os.path.join(self.input_dir, file)

            output_file_path = os.path.join(self.output_dir, file.replace(".html", ".json"))
            if os.path.exists(output_file_path):
                return file, None

            with open(file_path, "r", encoding="utf-8") as html_file:
                html_doc = html_file.read()

            soup = self._utils.getSoupFromHTML(html_doc)
            results = soup.findAll("table", {"class": "dialog"})
            tmp = results[0]  # Expecting only 1 table of this type
            results2 = [result for result in tmp.findAll("tr")
                        if len(result.findAll("td", recursive=False)) == 2
                        and self._utils.getDivOfClass(result, "cdiag_frame")]

            all_steps_info = []
            for index, result in enumerate(results2):
                if index % 2 == 1:
                    continue  # Skip every other row to avoid repetitions

                # Extract move information
                td_res = result.findAll("td", recursive=False)
                move_text = td_res[0].get_text()
                moves = (unicodedata.normalize('NFKD', move_text)
                         .encode('ascii', 'ignore')
                         .decode('utf-8'))
                moves = moves.split('<!--', 1)[0].strip()

                # Extract board information
                board_element_vals = self._get_board_values(result)
                board_element_info = _board_cell_to_info(board_element_vals)

                # Extract comment
                comment = self._utils.soupToText(td_res[1])

                # Compile step info
                current_step_info = {
                    "moves": moves,
                    "board": board_element_info,
                    "comment": comment
                }
                all_steps_info.append(current_step_info)

            with open(output_file_path, "w") as output_file:
                json.dump(all_steps_info, output_file)
        except Exception as e:
            return file, str(e)
        return file, None  # Success

    def parse_data(self):
        all_files = self._get_input_files()
        with ThreadPoolExecutor() as executor, open(self.parse_error_file, "w") as fw:
            futures = {executor.submit(self.process_file, file): file for file in all_files}
            for future in as_completed(futures):
                file, error = future.result()
                if error:
                    fw.write(f"{file}: {error}\n")
                    print(f"Error processing file {file}: {error}")


def main():
    config_path = "./config.yaml"
    config = yaml.safe_load(open(config_path))
    collector = DataCollector(config)
    collector.parse_data()


if __name__ == "__main__":
    main()
