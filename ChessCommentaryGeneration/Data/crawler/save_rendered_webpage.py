import argparse
import pickle
import sys
import time

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=int, dest="i", help="Index of the link")
    parser.add_argument("-num", type=int, dest="num", help="Page number")
    args = parser.parse_args()
    return args


class Render(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        super().__init__(self.app)
        self.html = ""
        self.loadFinished.connect(self._load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _load_finished(self):
        self.toHtml(self._callable)

    def _callable(self, data):
        self.html = data
        self.app.quit()


def save_all():
    args = parse_arguments()
    all_links = pickle.load(open("./saved_files/saved_links.p", "rb"))
    i = args.i
    num = args.num
    url = all_links[i]
    if num != 0:
        url += "&pg=" + str(num)
    print(f"i, url = {i}, {url}")

    try:
        r = Render(url)
        html_doc = r.html
        file_name = f"./saved_files/saved{i}.html" if num == 0 else f"./saved_files/saved{i}_{num}.html"
        with open(file_name, "w", encoding="utf-8") as fw:
            fw.write(html_doc)
        print("---- SLEEPING ----")
        time.sleep(10)
    except Exception as e:
        print("ERROR!!")
        print(f"Exception: {e}")


if __name__ == "__main__":
    save_all()
