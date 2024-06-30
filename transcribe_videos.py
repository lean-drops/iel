import os
import asyncio
import logging
import time
import warnings

from tqdm.asyncio import tqdm
import whisper
from docx import Document
import re
import aiofiles
from concurrent.futures import ProcessPoolExecutor
from typing import List
from convert_2_audio import convert_mp4_to_wav

# Suppress specific warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_WORKERS = 6  # Adjusted number of workers to balance performance and system load
BATCH_SIZE = 10  # Process files in smaller batches
CPU_THRESHOLD = 80  # CPU usage percentage threshold
MEMORY_THRESHOLD = 80  # Memory usage percentage threshold


def monitor_system_resources() -> bool:
    """
    Monitor the system's CPU and memory usage.

    :return: True if the system is under the threshold, False otherwise.
    """
    import psutil
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    logging.info(f"CPU usage: {cpu_usage}%, Memory usage: {memory_usage}%")
    return cpu_usage < CPU_THRESHOLD and memory_usage < MEMORY_THRESHOLD


def clean_transcription(text: str) -> str:
    """
    Clean the transcription text by handling common issues and formatting.

    :param text: The transcription text to clean.
    :return: The cleaned transcription text.
    """
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'([.,!?])', r' \1 ', text)  # Add spaces around punctuation
    text = text.strip()
    logging.info("Cleaned transcription text.")
    return text


def transcribe_wav_sync(file_path: str) -> str:
    """
    Transcribe the given WAV file using Whisper API synchronously.

    :param file_path: Path to the WAV file.
    :return: The transcription result as a string.
    """
    try:
        model = whisper.load_model("small", device="cpu", fp16=False)  # Use a smaller model for faster transcription
        result = model.transcribe(file_path)
        transcription = result['text']
        transcription = clean_transcription(transcription)
        logging.info(f"Transcription completed for {file_path}.")
        return transcription
    except Exception as e:
        logging.error(f"Error transcribing {file_path}: {e}")
        return ""


async def transcribe_wav(file_path: str, executor: ProcessPoolExecutor) -> str:
    """
    Asynchronously transcribe the given WAV file using Whisper API.

    :param file_path: Path to the WAV file.
    :param executor: Process pool executor for parallel processing.
    :return: The transcription result as a string.
    """
    loop = asyncio.get_event_loop()
    transcription = await loop.run_in_executor(executor, transcribe_wav_sync, file_path)
    return transcription


async def save_transcription(file_path: str, transcription: str, base_directory: str,
                             original_base_directory: str) -> None:
    """
    Save the transcription to a .txt and .docx file in a structured directory.

    :param file_path: Path to the original WAV file.
    :param transcription: The transcription text.
    :param base_directory: The base directory to save the transcriptions.
    :param original_base_directory: The original base directory of the MP4 files.
    """
    relative_path = os.path.relpath(file_path, original_base_directory)
    transcription_path = os.path.join(base_directory, os.path.splitext(relative_path)[0])

    os.makedirs(transcription_path, exist_ok=True)

    txt_file = os.path.join(transcription_path, 'transcription.txt')
    docx_file = os.path.join(transcription_path, 'transcription.docx')

    async with aiofiles.open(txt_file, 'w', encoding='utf-8') as f:
        await f.write(transcription)

    doc = Document()
    doc.add_heading('Transcription', 0)
    doc.add_paragraph(transcription)
    doc.save(docx_file)

    logging.info(f"Transcription saved to {txt_file} and {docx_file}.")


async def transcribe_audio_files(wav_files: List[str], base_directory: str, original_base_directory: str,
                                 max_workers: int) -> None:
    """
    Transcribe audio files in parallel and save the transcriptions.

    :param wav_files: List of paths to WAV files.
    :param base_directory: The base directory to save the transcriptions.
    :param original_base_directory: The original base directory of the MP4 files.
    :param max_workers: Maximum number of parallel workers.
    """
    executor = ProcessPoolExecutor(max_workers=max_workers)
    tasks = []

    for i in range(0, len(wav_files), BATCH_SIZE):
        batch = wav_files[i:i + BATCH_SIZE]

        for file_path in batch:
            # Monitor system resources before starting each task
            while not monitor_system_resources():
                logging.warning("High system usage detected. Waiting to continue...")
                await asyncio.sleep(5)  # Wait before rechecking the system resources

            tasks.append(transcribe_wav(file_path, executor))

        results = await tqdm.gather(*tasks, desc="Transcribing audio", total=len(tasks))

        for file_path, transcription in zip(batch, results):
            if transcription:
                await save_transcription(file_path, transcription, base_directory, original_base_directory)

        tasks.clear()  # Clear tasks after each batch to free up resources
        await asyncio.sleep(1)  # Shorter delay between batches to keep the system responsive


async def main():
    """
    Main function to find and process MP4 files in parallel.
    """
    directory = "videos"
    base_transcription_directory = "transcriptions"
    audio_directory = "audios"

    # Step 1: Convert MP4 files to WAV
    wav_files = await convert_mp4_to_wav(directory, audio_directory)

    # Step 2: Transcribe the extracted audio files
    await transcribe_audio_files(wav_files, base_transcription_directory, audio_directory, MAX_WORKERS)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    logging.info(f"Total time taken: {end_time - start_time:.2f} seconds")
