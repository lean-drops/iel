import os
import aiohttp
import asyncio
import logging
from tqdm import tqdm
from aiofiles import open as aio_open
import ssl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_WORKERS = 100  # Maximale Anzahl der parallelen Downloads

# SSL-Kontext für unsichere Verbindungen (Deaktiviert die SSL-Zertifikatsüberprüfung)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def download_video(session, url, download_path):
    """Download a video from the given URL."""
    try:
        async with session.get(url, ssl=ssl_context) as response:
            filename = os.path.basename(url)
            if not filename.endswith('.mp4'):
                filename += '.mp4'
            filepath = os.path.join(download_path, filename)

            async with aio_open(filepath, 'wb') as file:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk:
                        break
                    await file.write(chunk)

        return filepath
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None


async def process_video_urls_file(video_urls_file, download_path):
    """Process a single video URLs file."""
    async with aio_open(video_urls_file, 'r') as file:
        video_urls = [line.strip() for line in await file.readlines()]

    logging.info(f"Found {len(video_urls)} URLs in {video_urls_file}")

    async with aiohttp.ClientSession() as session:
        tasks = [
            download_video(session, url, download_path)
            for url in video_urls
        ]

        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading videos"):
            result = await task
            results.append(result)

    for result in results:
        if result:
            logging.info(f"Successfully downloaded: {result}")
        else:
            logging.error(f"Failed to download some videos.")


async def process_directory(source_directory, download_directory):
    """Process each directory to download videos."""
    tasks = []
    for root, _, files in os.walk(source_directory):
        logging.info(f"Visiting directory: {root}")
        for file in files:
            logging.info(f"Found file: {file}")
            if file.endswith('.txt'):  # Change to '.txt' to process text files
                video_urls_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, source_directory)
                download_path = os.path.join(download_directory, relative_path)

                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                logging.info(f"Processing file: {video_urls_file}")
                tasks.append(process_video_urls_file(video_urls_file, download_path))

    if not tasks:
        logging.warning("No tasks found. Please check the source directory and file extensions.")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Define source and download directories
    source_directory = "/Users/python/Python Projekte/Studium Digitale/links"
    download_directory = "/Users/python/Python Projekte/Studium Digitale/Downloads"

    # Process directories and download videos
    asyncio.run(process_directory(source_directory, download_directory))
