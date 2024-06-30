import os
import requests
import logging
from tqdm import tqdm

import extract_videos

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def download_video(url, download_path, counter):
    """Download a video from the given URL."""
    try:
        if 'api.cast.switch.ch' in url:
            response = requests.get(url, stream=True)
            filename = os.path.basename(url)
            if not filename.endswith('.mp4'):
                filename += '.mp4'
            filename = f"{counter}_{filename}"  # Make filename unique by adding a counter
            filepath = os.path.join(download_path, filename)

            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            return f"Downloaded: {filepath}"
        else:
            return f"Skipped: {url} (not matching the required pattern)"
    except Exception as e:
        return f"Failed to download {url}: {e}"


def download_videos(video_urls_file, download_path):
    """Download videos listed in the video URLs file."""
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    with open(video_urls_file, 'r') as file:
        video_urls = [line.strip() for line in file.readlines()]

    with tqdm(total=len(video_urls)) as pbar:
        for counter, url in enumerate(video_urls, 1):
            result = download_video(url, download_path, counter)
            logging.info(result)
            pbar.update(1)


if __name__ == "__main__":

    # Define the path to the video URLs file and the download directory
    video_urls_file = "/Users/python/Python Projekte/Studium Digitale/txt/23448423_video_urls.txt"
    download_path = "/Users/python/Python Projekte/Studium Digitale/Downloads"

    # Download the videos
    download_videos(video_urls_file, download_path)
