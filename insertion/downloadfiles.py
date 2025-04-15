import re
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from googlesearch import search
import yt_dlp
import time



max_size = 18 * 1024 # 18gb
current_size = 0

def sanitize_filename(name):
    sanitized = re.sub(r'[^a-zA-Z0-9 ._-]', '_', name)
    sanitized = sanitized.strip()
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized

def download_documents(driver, query, amount=5):
    final = []
    documents = [
        "filetype:txt OR filetype:pdf",
        "filetype:doc OR filetype:docx",
        "filetype:xls OR filetype:xlsx",
        "filetype:ppt OR filetype:pptx",
    ]
    for extension in documents:
        dork_query = f'{extension} {query}'
        try:
            driver.get("https://duckduckgo.com/?q=" + dork_query.replace(" ", "+"))
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
            )

            links = driver.find_elements(By.CSS_SELECTOR, "[data-testid='result-title-a']")
            for link in links[:amount*2]:
                href = link.get_attribute("href")
                if href and not href.startswith("https://duckduckgo.com"):
                    final.append(href)
        except Exception:
            return final
    return final

def download_images(driver, query, amount=5):
    driver.get(f"https://www.pexels.com/search/{query}/")

    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    images = []
    for img in soup.select('img[src*="pexels.com/photos"]'):
        images.append(img['src'].split('?')[0])

    return images[:amount]

def download_audio(query, amount=2):
    downloaded_sizes = []
    url = []

    def progress_hook(d):
        if d['status'] == 'finished':
            # Size is in bytes, convert to MB
            file_size_mb = d.get('total_bytes', d.get('total_bytes_estimate', 0)) / (1024 * 1024)
            downloaded_sizes.append(file_size_mb)
            url.append(d['info_dict']['webpage_url'])

    ydl_opts = {
        'format': 'bestaudio/best',
        'progress_hooks': [progress_hook],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }

    os.makedirs("downloads", exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{amount}:{query} sound effect"])

    return url, sum(downloaded_sizes)

def download_videos(driver, query, amount=2):
    downloaded_sizes = []
    urls = []
    def download_helper(url):
        def progress_hook(d):
            if d['status'] == 'finished':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                size_mb = total_bytes / (1024 * 1024)
                downloaded_sizes.append(size_mb)

        ydl_opts = {
            # FORCE MP4 OUTPUT
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': 'downloads/%(title)s.%(ext)s',

            'cookies_from_browser': ('chrome',),
            'extractor_args': {'youtube': {'player_client': ['android']}},

            # POST-PROCESSING
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Double conversion ensures MP4
            }],
            'progress_hooks': [progress_hook],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_file = ydl.prepare_filename(info).replace('.webm', '.mp4')
                print(f"✅ Downloaded: {os.path.basename(final_file)}")
                return final_file
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    driver.get("https://www.youtube.com")
    time.sleep(random.uniform(1, 3))

    # Human-like typing
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "search_query"))
    )
    for char in query:
        search_box.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))  # Human typing speed

    # Press enter (more natural than clicking search button)
    search_box.submit()
    time.sleep(random.uniform(2, 4))

    # Scroll to load more results
    driver.execute_script("window.scrollTo(0, 500)")
    time.sleep(random.uniform(1, 2))

    # Extract video links
    video_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-video-renderer #video-title"))
    )

    for video in video_elements[:amount*2]:
        url = video.get_attribute("href")
        if url and "youtube.com/watch" in url:
            urls.append(url)  # Clean URL parameters

    return urls, sum(downloaded_sizes)

def download_file(driver, query, amount):

    # documents = download_documents(driver, query)
    # images = download_images(driver, query)
    audio = download_audio(query)[0]
    videos = download_videos(driver, query)[0]

    final = videos + audio
    for i, link in enumerate(videos):
        print(i, link)

    for i, link in enumerate(audio):
        print(i, link)


def initialize_browser():
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(options=options)
    return driver

if __name__ == "__main__":
    browser = initialize_browser()

    # search_terms = " ".join(sys.argv[1:-1])


    search_terms = "pets"
    download_file(browser, search_terms, 5)


    browser.quit()
