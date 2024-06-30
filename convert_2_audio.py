import os
import logging
import asyncio
import psutil
from typing import List

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_CPU_PERCENT = 90
MAX_MEMORY_PERCENT = 90
MAX_CONCURRENT_TASKS = 8


def find_mp4_files(directory: str) -> List[str]:
    """
    Find all MP4 files in the specified directory and its subdirectories.

    :param directory: The directory to search for MP4 files.
    :return: A list of paths to MP4 files.
    """
    mp4_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp4'):
                mp4_files.append(os.path.join(root, file))
    logging.info(f"Found {len(mp4_files)} MP4 files.")
    return mp4_files


async def extract_audio_from_video(file_path: str, output_dir: str, semaphore: asyncio.Semaphore) -> str:
    """
    Asynchronously extract audio from the given MP4 file and save it in the specified output directory.
    Maintain the directory structure of the original file.

    :param file_path: Path to the MP4 file.
    :param output_dir: Root directory to save the extracted audio files.
    :param semaphore: Asyncio semaphore to limit concurrent tasks.
    :return: Path to the extracted audio WAV file.
    """
    async with semaphore:
        relative_path = os.path.relpath(file_path, 'videos')
        audio_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + '.wav')

        # Create the necessary directories
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        if os.path.exists(audio_path):
            logging.info(f"Audio file already exists for {file_path}. Skipping extraction.")
            return audio_path

        command = ['ffmpeg', '-i', file_path, '-vn', '-acodec', 'copy', audio_path]
        proc = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            logging.info(f"Extracted audio from {file_path} to {audio_path}.")
            return audio_path
        else:
            logging.error(f"Error extracting audio from {file_path}: {stderr.decode()}")
            return None


async def monitor_resources():
    """
    Monitor the system's CPU and memory usage and ensure it stays within limits.
    """
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > MAX_CPU_PERCENT or memory_percent > MAX_MEMORY_PERCENT:
            logging.warning(f"System resources high: CPU {cpu_percent}%, Memory {memory_percent}%")
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(0.1)


async def convert_mp4_to_wav(directory: str, output_dir: str) -> List[str]:
    """
    Asynchronously extract audio from all MP4 files in the given directory and save them in the specified output directory.

    :param directory: The directory containing MP4 files.
    :param output_dir: The root directory to save the extracted audio files.
    :return: A list of paths to the extracted audio WAV files.
    """
    mp4_files = find_mp4_files(directory)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    tasks = []

    for file_path in mp4_files:
        tasks.append(extract_audio_from_video(file_path, output_dir, semaphore))

    resource_monitor = asyncio.create_task(monitor_resources())
    wav_files = await asyncio.gather(*tasks)
    resource_monitor.cancel()

    return [wav_file for wav_file in wav_files if wav_file]


if __name__ == "__main__":
    download_directory = 'videos'
    audio_directory = 'audio'
    asyncio.run(convert_mp4_to_wav(download_directory, audio_directory))
