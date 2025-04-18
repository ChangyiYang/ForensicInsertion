from urllib.parse import urlparse, unquote, quote, parse_qs
import random
import os
import time
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import yt_dlp
import tempfile

# Base upload directory
BASE_UPLOAD_DIR = "./to_upload"

download_records = []


def extract_filename(url, file_type, base_filename = None):
    # Valid image extensions
    image_exts = {
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif", "svg", "ico", "heic", "psd", "raw"
    }

    # Initialize counter for fallback filenames
    if not hasattr(extract_filename, "counter"):
        extract_filename.counter = {}

    path = urlparse(url).path
    filename = unquote(os.path.basename(path))

    # Extract file extension if present
    ext = filename.split('.')[-1].lower() if '.' in filename else None

    # If extension is valid, return the filename
    if ext in image_exts:
        return filename

    # Otherwise, generate fallback
    if file_type not in extract_filename.counter:
        extract_filename.counter[file_type] = 1

    fallback = f"{base_filename}_{extract_filename.counter[file_type]}"
    if file_type == "image":
        fallback+= ".jpg"
    extract_filename.counter[file_type] += 1
    return fallback


def download_from_url(url, filename):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        # print(f"Downloaded successfully: {filename} ← {url}")
        download_records.append(filename)
        return True

    except Exception as e:
        # print(f"Failed to download: {url}, Error: {e}")
        return False

def get_documents(driver, query, amount=3):
    documents = []
    filenames = []
    documents_query = [
        "filetype:txt OR filetype:pdf",
        "filetype:doc OR filetype:docx",
        "filetype:xls OR filetype:xlsx",
        "filetype:ppt OR filetype:pptx",
    ]
    for extension in documents_query:
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
                    documents.append(href)
        except Exception:
            return documents

    random.shuffle(documents)

    count = 0
    for url in documents:
        name = extract_filename(url, "document", query)
        filenames.append(name)
        path = os.path.join(BASE_UPLOAD_DIR, "documents", name)
        if download_from_url(url, path):
            count += 1
        if count >= amount:
            break

    return documents, filenames

def get_images(driver, query, amount=3):
    origin_query = query
    query = f"https://duckduckgo.com/?q={quote(query)}&t=h_&iax=images&ia=images"
    print("Searching for images with query:", query)
    driver.get(query)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    images = []
    filenames = []
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src') or img_tag.get('data-src')
        if src and "external-content.duckduckgo.com/iu/?" in src:
            if src.startswith("//"):
                src = "https:" + src

            # Optional: extract original image URL
            parsed = urlparse(src)
            qs = parse_qs(parsed.query)
            original_url = qs.get("u", [None])[0]
            if original_url:
                images.append(unquote(original_url))
            else:
                images.append(src)  # fallback

    # print("Got image urls:", images)

    random.shuffle(images)
    images = images[:amount]

    count = 0
    for url in images:
        name = extract_filename(url, "image", origin_query)
        filenames.append(name)
        path = os.path.join(BASE_UPLOAD_DIR, "images", name)
        if download_from_url(url, path):
            count += 1
        if count >= amount:
            break
    print(f"Downloaded {count} images.")
    return images, filenames

def get_audio(query, amount=2):
    url = []
    filenames = []

    def progress_hook(d):
        if d['status'] == 'finished':
            filenames.append(d.get('filename'))
            url.append(d['info_dict']['webpage_url'])

    ydl_opts = {
        'format': 'bestaudio/best',
        'progress_hooks': [progress_hook],
        'outtmpl': os.path.join(BASE_UPLOAD_DIR, "audios", "%(title)s.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    os.makedirs("downloads", exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{amount}:{query} sound effect"])

    return url, filenames

def get_videos(driver, query, amount=2):
    urls = []
    filenames = []

    def download_helper(url):
        def progress_hook(d):
            if d['status'] == 'finished':
                filenames.append(d.get('filename'))

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(BASE_UPLOAD_DIR, "videos", "%(title)s.%(ext)s"),
            'cookies_from_browser': ('chrome',),
            'extractor_args': {'youtube': {'player_client': ['android']}},
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [progress_hook],
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_file = ydl.prepare_filename(info).replace('.webm', '.mp4')
                print(f"Downloaded: {os.path.basename(final_file)}")
                return final_file
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    driver.get("https://www.youtube.com")
    time.sleep(random.uniform(1, 3))

    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "search_query"))
    )
    for char in query:
        search_box.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

    search_box.submit()
    time.sleep(random.uniform(2, 4))

    driver.execute_script("window.scrollTo(0, 500)")
    time.sleep(random.uniform(1, 2))

    video_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-video-renderer #video-title"))
    )

    for video in video_elements[:amount*2]:
        url = video.get_attribute("href")
        if url and "youtube.com/watch" in url:
            urls.append(url)

    random.shuffle(urls)
    urls = urls[:amount]

    for url in urls:
        download_helper(url)

    return urls, filenames

def download_file(query_dict):
    driver = initialize_browser()
    download_records.clear()

    try:
        for category, queries in query_dict.items():
            if not queries:
                continue  # skip empty list

            if category == "documents":
                for query in queries:
                    get_documents(driver, query)

            elif category == "images":
                for query in queries:
                    get_images(driver, query)

            elif category == "audios":
                for query in queries:
                    get_audio(query)

            elif category == "videos":
                for query in queries:
                    get_videos(driver, query)

            else:
                print(f"Unknown category: {category}")

    finally:
        driver.quit()
        print("All downloads completed.")

    return download_records


def initialize_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    driver = webdriver.Chrome(options=options)
    return driver

def reset_uploads(filetypes):
    for filetype in filetypes:
        folder = os.path.join(BASE_UPLOAD_DIR, filetype)
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)

if __name__ == "__main__":
    filetypes = ["documents", "images", "audios", "videos"]
    search_terms = "changyi yang Berkeley California"
    download_file(search_terms)
