import os
import logging
from tqdm import tqdm
from download_videos import download_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def manage_downloads(video_urls_file, base_download_path):
    """Organize the download of videos listed in the video URLs file."""
    if not os.path.exists(base_download_path):
        os.makedirs(base_download_path)

    with open(video_urls_file, 'r') as file:
        video_urls = [line.strip() for line in file.readlines()]

    folder_counter = 1
    file_counter = 1

    with tqdm(total=len(video_urls)) as pbar:
        for url in video_urls:
            # Create a new folder for every 10 videos
            download_path = os.path.join(base_download_path, f"StDig_L{folder_counter}")
            if not os.path.exists(download_path):
                os.makedirs(download_path)

            result = download_video(url, download_path, file_counter)
            logging.info(result)
            pbar.update(1)

            file_counter += 1
            if file_counter > 10:
                file_counter = 1
                folder_counter += 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        logging.error("Usage: python manage_downloads.py <video_urls_file> <base_download_path>")
        sys.exit(1)

    video_urls_file = sys.argv[1]
    base_download_path = sys.argv[2]

    manage_downloads(video_urls_file, base_download_path)
