from urllib.parse import urlparse, unquote
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import yt_dlp
import time


def extract_filename(url):
    path = urlparse(url).path
    filename = os.path.basename(path)
    return unquote(filename)

def download_from_url(url, filename):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True

    except Exception:
        return False

def get_documents(driver, query, amount=5):
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
        name = extract_filename(url)
        filenames.append(name)
        path = f"../to_upload/documents/{name}"
        if download_from_url(url, path):
            count += 1
        if count >= amount:
            break

    return documents, filenames

def get_images(driver, query, amount=5):
    driver.get(f"https://www.pexels.com/search/{query}/")

    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    images = []
    filenames = []
    for img in soup.select('img[src*="pexels.com/photos"]'):
        images.append(img['src'].split('?')[0])

    random.shuffle(images)
    images = images[:amount]

    count = 0
    for url in images:
        name = extract_filename(url)
        filenames.append(name)
        path = f"../to_upload/images/{name}"
        if download_from_url(url, path):
            count += 1
        if count >= amount:
            break

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
        'outtmpl': '../to_upload/audios/%(title)s.%(ext)s',
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
            # FORCE MP4 OUTPUT
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': '../to_upload/videos/%(title)s.%(ext)s',

            'cookies_from_browser': ('chrome',),
            'extractor_args': {'youtube': {'player_client': ['android']}},

            # POST-PROCESSING
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Double conversion ensures MP4
            }],
            'progress_hooks': [progress_hook],
            'quiet': True
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

def download_file(driver, query, filetypes):

    pool = [
        get_documents(driver, query),
        get_images(driver, query),
        get_audio(query),
        get_videos(driver, query)
    ]

    for i, values in enumerate(pool):
        print(i, filetypes[i])
        for [url, name] in values:
            print(name, url)

def initialize_browser():
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(options=options)
    return driver

def reset_uploads(filetypes):
    for type in filetypes:
        os.system(f"rm ../to_upload/{type}/*")

if __name__ == "__main__":

    # search_terms = " ".join(sys.argv[1:-1])
    browser = initialize_browser()

    filetypes = ["documents", "images", "audios", "videos"]




    search_terms = "changyi yang"
    download_file(browser, search_terms, filetypes)

    # reset_uploads(filetypes)



    # browser.quit()
