import os
import re
import json
import time
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict
from azure.storage.blob import BlobServiceClient
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

BASE_URL = 'https://www.madewithnestle.ca'
STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
CONTAINER_NAME = 'nestle-scraped-content'
DATA_DIR = Path("./Scraped/")

# Ensure the data directory exists
DATA_DIR.mkdir(exist_ok=True)

class ScrapedPage:
    def __init__(self, url: str, title: str, content: str, links: List[str], images: List[str], metadata: Dict):
        self.url = url
        self.title = title
        self.content = content
        self.links = links
        self.images = images
        self.metadata = metadata

    def to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "links": self.links,
            "images": self.images,
            "metadata": self.metadata,
        }

async def scrape_website(limit_pages: int = 200) -> List[ScrapedPage]:
    pages: List[ScrapedPage] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()

        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_timeout(2000)

        links = await page.eval_on_selector_all("a[href]", "elements => elements.map(el => el.href)")
        filtered_links = list(set(
            l for l in links if BASE_URL in l and '#' not in l and '?' not in l
        ))[:limit_pages]

        for url in filtered_links:
            try:
                print(f"Scraping: {url}")
                await page.goto(url, timeout=45000, wait_until="networkidle")
                if page.url != url:
                    print(f"Redirected to {page.url}, skipping.")
                    continue
                await page.wait_for_timeout(2000)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                title = soup.title.string.strip() if soup.title else "Untitled"
                meta_desc = soup.find("meta", attrs={"name": "description"})
                meta_keywords = soup.find("meta", attrs={"name": "keywords"})

                description = meta_desc["content"] if meta_desc else ""
                keywords = meta_keywords["content"].split(',') if meta_keywords else []

                for s in soup(["script", "style"]):
                    s.decompose()

                texts = [el.get_text(strip=True) for el in soup.find_all(["p", "li", "h1", "h2", "h3", "h4"])]
                content = ' '.join(t for t in texts if len(t) > 5).strip()

                word_freq = {}
                for word in re.findall(r"\b\w{4,}\b", content.lower()):
                    word_freq[word] = word_freq.get(word, 0) + 1

                top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                all_keywords = list(set(keywords + [kw[0] for kw in top_keywords]))

                images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
                links = [l.get("href") for l in soup.find_all("a") if l.get("href")]

                pages.append(ScrapedPage(
                    url=url,
                    title=title,
                    content=content,
                    links=list(set(links)),
                    images=list(set(images)),
                    metadata={
                        "description": description,
                        "keywords": all_keywords,
                        "categories": []
                    }
                ))
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

        await browser.close()
    return pages

def save_locally(pages: List[ScrapedPage]):
    timestamp = int(time.time())
    file_path = DATA_DIR / f"scraped_content_{timestamp}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in pages], f, indent=2)
    print(f"✅ Saved to {file_path}")

    index_path = DATA_DIR / f"index_{timestamp}.json"
    index = {
        "scrapeTime": datetime.datetime.now().isoformat(),
        "pageCount": len(pages),
        "pages": [{"url": p.url, "title": p.title} for p in pages]
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"🗂️ Index saved to {index_path}")

def save_to_blob(pages: List[ScrapedPage]):
    if not STORAGE_CONNECTION_STRING:
        print("⚠️ No Azure Storage connection string found. Skipping blob upload.")
        return

    print("☁️ Uploading to Azure Blob Storage...")
    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    container = blob_service.get_container_client(CONTAINER_NAME)
    if not container.exists():
        container.create_container()

    timestamp = int(time.time())
    for i, page in enumerate(pages):
        blob_name = f"page_{i}_{timestamp}.json"
        blob = container.get_blob_client(blob_name)
        content = json.dumps(page.to_dict())
        blob.upload_blob(content, overwrite=True)

    index_blob = container.get_blob_client(f"index_{timestamp}.json")
    index = {
        "scrapeTime": datetime.datetime.now().isoformat(),
        "pageCount": len(pages),
        "pages": [{"url": p.url, "title": p.title} for p in pages]
    }
    index_blob.upload_blob(json.dumps(index), overwrite=True)
    print("✅ Content uploaded to Azure Blob Storage.")

def get_scraped_content() -> List[ScrapedPage]:
    """Retrieves the scraped content from Azure Blob Storage or local file"""
    try:
        # If we have Azure storage configured, retrieve from there
        if STORAGE_CONNECTION_STRING:
            print('Retrieving content from Azure Blob Storage...')
            blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            
            # Check if container exists
            if not container_client.exists():
                print('No scraped content found in blob storage')
                return []
            
            # Find the latest index file
            latest_index = None
            latest_time = 0
            
            for blob in container_client.list_blobs():
                if blob.name.startswith('index_'):
                    timestamp = int(blob.name.split('_')[1].split('.')[0])
                    if timestamp > latest_time:
                        latest_time = timestamp
                        latest_index = blob.name
            
            if not latest_index:
                print('No index file found in blob storage')
                return []
            
            # Download and parse the index file
            index_blob_client = container_client.get_blob_client(latest_index)
            index_content = index_blob_client.download_blob().readall().decode('utf-8')
            index = json.loads(index_content)
            
            # Download each page
            scraped_pages = []
            for page_info in index['pages']:
                # Find the corresponding page blob
                for blob in container_client.list_blobs():
                    if blob.name.startswith('page_') and str(latest_time) in blob.name:
                        page_blob_client = container_client.get_blob_client(blob.name)
                        page_content = page_blob_client.download_blob().readall().decode('utf-8')
                        page_data = json.loads(page_content)
                        scraped_pages.append(ScrapedPage(**page_data))
                        break
            
            return scraped_pages
        
        else:
            # If no Azure storage, check for local file
            print('Retrieving content from local file...')
            
            data_dir = Path(__file__).parent.parent / 'Scraped'
            if not data_dir.exists():
                print('Scraped directory does not exist')
                return []
            
            # Find the latest scraped content file
            scraped_files = [
                f for f in data_dir.glob('scraped_content_*.json')
                if f.is_file()
            ]
            
            if not scraped_files:
                print('No scraped content files found')
                return []
            
            # Sort by timestamp (descending)
            scraped_files.sort(key=lambda f: int(f.stem.split('_')[-1]), reverse=True)
            
            # Read the latest file
            latest_file = scraped_files[0]
            print(f'Reading content from {latest_file}')
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            print(f'Found {len(content)} pages in the file')
            return [ScrapedPage(**page) for page in content]
    
    except Exception as e:
        print(f'Error retrieving scraped content: {str(e)}')
        return []
    
