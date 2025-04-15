import re
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from googlesearch import search
from yt_dlp import YoutubeDL
import time



max_size = 18 * 1024 # 18gb

def sanitize_filename(name):
    sanitized = re.sub(r'[^a-zA-Z0-9 ._-]', '_', name)
    sanitized = sanitized.strip()
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized

def download_documents(query, amount=5):
    final = []
    documents = [
        "filetype:txt OR filetype:pdf",
        "filetype:doc OR filetype:docx",
        "filetype:xls OR filetype:xlsx",
        "filetype:ppt OR filetype:pptx",
    ]
    for extension in documents:
        dork_query = f'{extension} {query}'

        print(f"🔎 Top {amount} results for '{query}':\n")

        for i, url in enumerate(search(dork_query, num_results=amount), 1):
            print(f"{i}. {url}")
            final.append(url)
    return final

def download_images(query, amount=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.pexels.com/search/{query}/")

    # Wait for JavaScript to load
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    images = []
    for img in soup.select('img[src*="pexels.com/photos"]'):
        images.append(img['src'].split('?')[0])

    return images[:amount]

def download_audio(query, amount=5):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }], 'quiet': False
    }

    os.makedirs("downloads", exist_ok=True)

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{amount}:{query} sound effect"])

def download_videos(query, amount=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.pexels.com/search/videos/{query}/")

    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    images = []
    for img in soup.select('img[src*="pexels.com/photos"]'):
        images.append(img['src'].split('?')[0])

    return images[:amount]


def download_file(query):
    download_documents(query)
    download_images(query)
    download_audio(query)
    download_videos(query)


def main():
    # search_terms = " ".join(sys.argv[1:-1])
    search_terms = "pets"
    download_images(search_terms, 5)



if __name__ == "__main__":
    main()
