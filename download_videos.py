import os
import requests
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import dask
from dask import delayed, compute
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_WORKERS = 100  # Maximale Anzahl der Threads für parallele Downloads


def download_video(url, audio_download_path, counter):
    """Download a video from the given URL."""
    try:
        response = requests.get(url, stream=True)
        filename = os.path.basename(url)
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        filename = f"{counter}_{filename}"  # Make filename unique by adding a counter
        video_filepath = os.path.join(audio_download_path, filename)

        with open(video_filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        return video_filepath
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None


def convert_to_mp3(video_filepath):
    """Convert a video file to MP3 using FFmpeg."""
    try:
        mp3_filepath = video_filepath.replace('.mp4', '.mp3')
        subprocess.run(
            ['ffmpeg', '-i', video_filepath, '-q:a', '0', '-map', 'a', mp3_filepath],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        os.remove(video_filepath)  # Remove the video file after conversion
        return mp3_filepath
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to convert {video_filepath} to MP3: {e}")
        return None


def download_and_convert(url, audio_download_path, counter):
    """Download a video and convert it to MP3."""
    video_filepath = download_video(url, audio_download_path, counter)
    if video_filepath:
        return convert_to_mp3(video_filepath)
    return None


def process_video_urls_file(video_urls_file, audio_download_path):
    """Process a single video URLs file."""
    with open(video_urls_file, 'r') as file:
        video_urls = [line.strip() for line in file.readlines()]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(download_and_convert, url, audio_download_path, counter)
            for counter, url in enumerate(video_urls, 1)
        ]

        results = []
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading and converting videos"):
            results.append(future.result())

    for result in results:
        if result:
            logging.info(f"Successfully processed: {result}")
        else:
            logging.error(f"Failed to process some videos.")


def process_directory(source_directory, download_directory):
    """Process each directory to download videos and convert them."""
    tasks = []
    for root, _, files in os.walk(source_directory):
        for file in files:
            if file.endswith('.txt'):
                video_urls_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, source_directory)
                audio_download_path = os.path.join(download_directory, relative_path)

                if not os.path.exists(audio_download_path):
                    os.makedirs(audio_download_path)

                tasks.append(delayed(process_video_urls_file)(video_urls_file, audio_download_path))

    with tqdm(total=len(tasks), desc="Processing directories") as pbar:
        results = compute(*tasks, scheduler='threads')
        for _ in results:
            pbar.update(1)


if __name__ == "__main__":
    # Define source and download directories
    source_directory = "/Users/python/Python Projekte/Studium Digitale/links"
    download_directory = "/Users/python/Python Projekte/Studium Digitale/Downloads"

    # Process directories and download videos
    process_directory(source_directory, download_directory)
