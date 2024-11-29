import asyncio
import json
import logging
from pathlib import Path

import yaml
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkUpdater:
    def __init__(self, config_path):
        self.config = yaml.safe_load(Path(config_path).read_text())
        self.links = self._load_previous_links()

    async def __aenter__(self):
        self.session = ClientSession(timeout=ClientTimeout(total=self.config['page_timeout']))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def _save_links(self):
        path = Path(self.config['saved_links_path'])
        Path(path).write_text(json.dumps(self.links, indent=2))

    def _load_previous_links(self) -> dict[str, int]:
        try:
            with open(self.config['saved_links_path'], 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def _parse_page(self, url: str) -> BeautifulSoup:
        async with self.session.get(url, headers=self.headers) as response:
            page = await response.read()
            return BeautifulSoup(page, 'html.parser', from_encoding='utf-8')

    async def get_page_count(self, url: str) -> int:
        soup = await self._parse_page(url)
        paginator = soup.find_all('table', class_="paginator")
        return int(paginator[0].find_all('a')[-2].text) if paginator else 1

    async def _fetch_page_links(self, url: str) -> int:
        root_url = self.config['root_url']
        soup = await self._parse_page(url)
        count = 0
        for elem in soup.find_all('tr', ["evn_list", "odd_list"]):
            link = elem.find_all('a')[1].get('href')
            cleaned_link = link.split('/')[-1]
            if cleaned_link in self.links:
                logger.info(f"{cleaned_link} already exists, skipping")
                continue

            page_count = await self.get_page_count(f"{root_url}{link}")
            logger.info(f"Found new link: {cleaned_link} with {page_count} pages")

            self.links[cleaned_link] = page_count
            await asyncio.sleep(self.config['request_delay'])
            count += 1
        return count

    def get_game_links(self):
        return self.links

    async def update_game_links(self):
        annotations_url = self.config['annotations_url']
        nav_page_count = await self.get_page_count(annotations_url)
        await asyncio.sleep(self.config['request_delay'])

        for i in range(nav_page_count):
            page_url = f"{annotations_url}&p={i}"
            try:
                count = await self._fetch_page_links(page_url)
                self._save_links()
                logger.info(f"Fetched {count} links from page {i}")
                await asyncio.sleep(self.config['request_delay'])
            except Exception as e:
                logger.error(f"Failed to fetch {page_url}: {e}")


async def main():
    async with LinkUpdater("./config.yaml") as updater:
        # await updater.update_game_links()
        links = updater.get_game_links()
        print(f"Found {len(links)} links with {sum(links.values())} total pages")


if __name__ == "__main__":
    asyncio.run(main())
