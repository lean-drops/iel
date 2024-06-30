import os
import re
import requests
from bs4 import BeautifulSoup
from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, END
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor


def extract_video_urls(url):
    """Extract video URLs from the given webpage."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    video_urls = []

    for tag in soup.find_all(['iframe', 'video', 'source']):
        src = tag.get('src') or tag.get('data-src')
        if src and 'http' in src:
            video_urls.append(src)
        if 'kaltura' in src:
            data_url = re.search(r'dataUrl":"(https.*?)"', response.text)
            if data_url:
                video_urls.append(data_url.group(1))

    return video_urls


def download_video(url, download_path):
    """Download a video from the given URL."""
    try:
        response = requests.get(url, stream=True)
        filename = os.path.join(download_path, url.split('/')[-1])

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        return f"Downloaded: {filename}"
    except Exception as e:
        return f"Failed to download {url}: {e}"


def download_videos_concurrently(video_urls, download_path, text_widget):
    """Download videos concurrently."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_video, url, download_path): url for url in video_urls}
        for future in futures:
            result = future.result()
            text_widget.insert(END, result + "\n")
            text_widget.see(END)


def start_download():
    website_url = url_entry.get()
    download_path = filedialog.askdirectory()

    if not download_path:
        return

    text_widget.delete(1.0, END)
    video_urls = extract_video_urls(website_url)

    if not video_urls:
        text_widget.insert(END, "No videos found.\n")
        return

    text_widget.insert(END, f"Found {len(video_urls)} videos.\n")
    download_videos_concurrently(video_urls, download_path, text_widget)


# Tkinter GUI
root = Tk()
root.title("Video Downloader")

Label(root, text="Website URL:").grid(row=0, column=0, padx=10, pady=10)

url_entry = Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10)

download_button = Button(root, text="Download Videos", command=start_download)
download_button.grid(row=0, column=2, padx=10, pady=10)

text_widget = Text(root, wrap='word', height=15, width=70)
text_widget.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

scrollbar = Scrollbar(root, command=text_widget.yview)
scrollbar.grid(row=1, column=3, sticky='nsew')
text_widget['yscrollcommand'] = scrollbar.set

root.mainloop()
