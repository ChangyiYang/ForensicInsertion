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


def split_list(elements):
    # Calculate the split point (2/3 of the list)
    split_point = int(len(elements) * 2 / 3)

    # Split the list
    videos = elements[:split_point]  # First 2/3
    audio = elements[split_point:]  # Remaining 1/3

    return videos, audio

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


def download_youtube(url, type='video'):
    try:
        if type == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',  # Best audio quality available
                'outtmpl': os.path.join(BASE_UPLOAD_DIR, '%(title)s.mp3'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'extract_audio': True,  # Only keep the audio
            }
        else:  # video
            ydl_opts = {
                'format': 'worst[ext=mp4]',  # Worst quality that's already in mp4 format
                'outtmpl': os.path.join(BASE_UPLOAD_DIR, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == 'audio':
                filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            print(f"Downloaded: {os.path.basename(filename)}")
            return filename

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

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

def get_videos_and_audio(driver, query, amount=3):

    filenames = []

    driver.get("https://duckduckgo.com/?q=site%3Ayoutube.com+" + query.replace(" ", "+") + "&iax=videos&ia=videos")
    time.sleep(random.uniform(2, 4))

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3)")
    time.sleep(random.uniform(1, 2))

    pool = []
    elements = driver.find_elements(By.TAG_NAME, "a")
    for element in elements:
        url = element.get_attribute("href")
        if url and "youtube.com/watch" in url:
            pool.append(url)

    video_urls, audio_urls = split_list(pool[:3])

    for url in audio_urls:
        download_youtube(url, "audio")
        time.sleep(random.uniform(1, 3))  # Be polite with delays


    for url in video_urls:
        download_youtube(url)
        time.sleep(random.uniform(1, 3))  # Be polite with delays

    return video_urls, audio_urls, filenames


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


            elif category == "videos/audio":
                for query in queries:
                    get_videos_and_audio(driver, query)

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
    
    # Reset the upload folders
    reset_uploads(filetypes)

    # Example search queries
    example_queries = {
        "documents": ["climate change effects", "global warming report"],
        "images": ["polar bear on melting ice", "glacier retreat photos"],
        "audios": ["climate speech recording"],
        "videos": ["arctic wildlife documentary"]
    }

    # Download files based on example queries
    downloaded_files = download_file(example_queries)

    print("\nDownloaded Files:")
    for f in downloaded_files:
        print(f" - {f}")



