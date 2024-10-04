import concurrent.futures
import pickle
import sys

import save_rendered_webpage

# Constants
COMMAND = 'python classify.py'
MAX_PROCESSES = int(sys.argv[3])
START = int(sys.argv[1])
END = int(sys.argv[2])

# Load links
with open("./saved_files/saved_links.p", "rb") as f:
    all_links = pickle.load(f)

with open("./extra_pages.p", "rb") as f:
    extra_links = pickle.load(f)


def main():
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor:
        futures = []
        for i, link in enumerate(all_links):
            if i < START:
                continue
            if i > END:
                break
            num = extra_links[i]
            print(f"i, num: {i}, {num}")
            for j in range(num):
                print(j)
                futures.append(executor.submit(save_rendered_webpage.save_all, i, j))

        # Wait for all futures to complete (blocks until done)
        concurrent.futures.wait(futures)


if __name__ == "__main__":
    main()
