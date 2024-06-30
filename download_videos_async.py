import os
import aiohttp
import asyncio
import logging
from tqdm.asyncio import tqdm
from aiofiles import open as aio_open
import ssl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_WORKERS = 10  # Maximale Anzahl der parallelen Downloads

# SSL-Kontext für unsichere Verbindungen (Deaktiviert die SSL-Zertifikatsüberprüfung)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

semaphore = asyncio.Semaphore(MAX_WORKERS)


async def download_video(session: aiohttp.ClientSession, url: str, download_path: str, file_name: str) -> str:
    """Lädt ein Video von der gegebenen URL herunter und speichert es unter dem angegebenen Pfad und Dateinamen."""
    async with semaphore:
        try:
            async with session.get(url, ssl=ssl_context) as response:
                if response.status != 200:
                    logging.error(f"Failed to download {url}: Status code {response.status}")
                    return None

                filepath = os.path.join(download_path, file_name)

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


async def process_video_urls_file(session: aiohttp.ClientSession, video_urls_file: str, download_path: str):
    """Verarbeitet eine einzelne .txt-Datei mit Video-URLs und startet den Download."""
    async with aio_open(video_urls_file, 'r') as file:
        video_urls = [line.strip() for line in await file.readlines()]

    logging.info(f"Found {len(video_urls)} URLs in {video_urls_file}")

    base_name = os.path.splitext(os.path.basename(video_urls_file))[0]
    tasks = [
        download_video(session, url, download_path, f"{base_name}.mp4")
        for index, url in enumerate(video_urls)
    ]

    results = []
    async for task in tqdm.as_completed(tasks, total=len(tasks), desc="Downloading videos"):
        result = await task
        results.append(result)

    for result in results:
        if result:
            logging.info(f"Successfully downloaded: {result}")
        else:
            logging.error(f"Failed to download some videos.")


async def process_directory(source_directory: str, download_directory: str):
    """Durchsucht das Quellverzeichnis rekursiv nach .txt-Dateien und startet den Download der Videos."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for root, _, files in os.walk(source_directory):
            logging.info(f"Visiting directory: {root}")
            for file in files:
                logging.info(f"Found file: {file}")
                if file.endswith('.txt'):
                    video_urls_file = os.path.join(root, file)
                    relative_path = os.path.relpath(root, source_directory)
                    download_path = os.path.join(download_directory, relative_path)

                    if not os.path.exists(download_path):
                        os.makedirs(download_path)

                    logging.info(f"Processing file: {video_urls_file}")
                    tasks.append(process_video_urls_file(session, video_urls_file, download_path))

        if not tasks:
            logging.warning("No tasks found. Please check the source directory and file extensions.")

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Define source and download directories
    source_directory = "/Users/python/Python Projekte/Studium Digitale/links"
    download_directory = "/Users/python/Python Projekte/Studium Digitale/Downloads"

    # Process directories and download videos
    asyncio.run(process_directory(source_directory, download_directory))
