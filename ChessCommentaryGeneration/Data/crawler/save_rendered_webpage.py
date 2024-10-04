import argparse
import pickle
import time

from selenium import webdriver


def fetch_html(url):
    """Fetch the rendered HTML content of the given URL using Selenium."""
    options = webdriver.FirefoxOptions()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    time.sleep(5)  # Wait for the page to fully render
    html = driver.page_source
    driver.quit()
    return html


def save_all(i, num):
    all_links = pickle.load(open('./saved_files/saved_links.p', 'rb'))
    url = all_links[i]
    if num != 0:
        url += '&pg=' + str(num)
    print(f"i, url = {i}, {url}")

    try:
        html_doc = fetch_html(url)
        file_name = f'./saved_files/saved{i}.html' if num == 0 else f'./saved_files/saved{i}_{num}.html'
        with open(file_name, 'w', encoding='utf-8') as fw:
            fw.write(html_doc)
        print("---- SLEEPING ----")
        time.sleep(10)
    except Exception as e:
        print("ERROR!!")
        print(f"Exception: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=int, dest="i", help="Index of the link")
    parser.add_argument("-num", type=int, dest="num", help="Page number")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    save_all(args.i, args.num)


if __name__ == "__main__":
    main()
