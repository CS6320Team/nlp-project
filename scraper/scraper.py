import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import yaml
from playwright.async_api import async_playwright

# Configure logging
os.mkdir("./logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.output_dir = Path(self.config['scrape_output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Status tracking
        self.progress_file = self.output_dir / 'progress.json'
        self.status = {
            'successful_urls': set(),
            'failed_urls': set(),
            'last_index': self.config['start_index']
        }
        self.load_progress()

    @staticmethod
    def load_config(path: str) -> dict:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def load_progress(self):
        """Load progress from previous run if it exists."""
        if self.progress_file.exists() and self.config['resume_enabled']:
            try:
                with open(self.progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    self.status['successful_urls'] = set(saved_progress['successful_urls'])
                    self.status['failed_urls'] = set(saved_progress['failed_urls'])
                    self.status['last_index'] = saved_progress['last_index']
                    logger.info(f"Resumed from index {self.status['last_index']}")
            except Exception as e:
                logger.error(f"Error loading progress: {e}")

    def save_progress(self):
        """Save current progress."""
        try:
            progress = {
                'successful_urls': list(self.status['successful_urls']),
                'failed_urls': list(self.status['failed_urls']),
                'last_index': self.status['last_index'],
                'timestamp': datetime.utcnow().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    async def scrape_page(self, browser, url: str, name: str) -> bool:
        """Scrape and save the content of a single page."""
        if url in self.status['successful_urls']:
            return True

        page = None
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=self.config["page_timeout"] * 1000, wait_until='domcontentloaded')
            await asyncio.sleep(self.config["render_wait"])

            content = await page.content()

            filepath = self.output_dir / f"{name}.html"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Successfully scraped {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return False
        finally:
            if page:
                await page.close()
                await asyncio.sleep(self.config['request_delay'])

    def load_urls(self) -> dict[str, int]:
        """Load URLs from saved files."""
        try:
            with open(self.config['saved_links_path'], 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def run(self):
        try:
            logger.info("Starting scraper...")

            # Load URLs
            links = list(self.load_urls().items())
            logger.info(f"Loaded {len(links)} URLs")

            # Get URL slice based on index range
            start_idx = max(self.status['last_index'], self.config['start_index'])
            end_idx = min(self.config['end_index'], len(links)) if self.config['end_index'] else len(links)
            logger.info(f"Processing URLs from index {start_idx} to {end_idx}")
            game_url = self.config['game_url']

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )

                semaphore = asyncio.Semaphore(self.config['max_concurrent'])

                async def bounded_scrape(url, index, name):
                    async with semaphore:
                        success = await self.scrape_page(browser, url, name)
                        if success:
                            self.status['successful_urls'].add(url)
                        else:
                            self.status['failed_urls'].add(url)
                        self.status['last_index'] = index
                        if index % self.config['save_frequency'] == 0:
                            self.save_progress()

                tasks = []
                for i in range(start_idx, end_idx):
                    url, page_count = links[i]
                    for page_num in range(page_count):
                        page_url = f"{game_url}/{url}&pg={page_num}"
                        saved_name = f"saved{i}_{page_num}"
                        tasks.append(bounded_scrape(page_url, i, saved_name))

                await asyncio.gather(*tasks)
                await browser.close()

            self.save_progress()

            logger.info(f"Scraping completed. "
                        f"Successful: {len(self.status['successful_urls'])}, "
                        f"Failed: {len(self.status['failed_urls'])}")

        except Exception as e:
            logger.error(f"Scraping process failed: {e}")
            self.save_progress()
            raise


async def main():
    scraper = Scraper('./config.yaml')
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
