"""
Zweck des Skripts:
Dieses Skript durchsucht rekursiv eine gegebene Verzeichnisstruktur, extrahiert Video-URLs aus HTML-Dateien und speichert diese in gut organisierten Ausgabeverzeichnissen.
Jede HTML-Datei wird parallel verarbeitet, um die Effizienz zu maximieren. Die Video-URLs werden in Textdateien gespeichert, die nach den Namen der HTML-Dateien benannt sind.

Hauptfunktionen und -methoden:
- extract_video_urls_from_file: Extrahiert Video-URLs aus einer gegebenen HTML-Datei.
- process_html_files: Durchsucht rekursiv die Verzeichnisstruktur, extrahiert Video-URLs und speichert sie in entsprechenden Verzeichnissen.
- main: Einstiegspunkt des Skripts, definiert Quell- und Zielverzeichnisse und startet die Verarbeitung.

Übersicht über den Ablauf des Skripts:
1. Das Skript durchsucht rekursiv das Quellverzeichnis nach HTML-Dateien.
2. Jede gefundene HTML-Datei wird parallel verarbeitet, um Video-URLs zu extrahieren.
3. Die extrahierten URLs werden in Textdateien im Zielverzeichnis gespeichert, wobei die Verzeichnisstruktur beibehalten wird.

Hinweise auf spezielle Implementierungsentscheidungen oder Sicherheitsaspekte:
- Es wird sichergestellt, dass die Ausgabeverzeichnisse erstellt werden, falls sie noch nicht existieren.
- Es wird Typannotationen verwendet, um die Lesbarkeit und Fehlersicherheit zu erhöhen.
- Die parallele Verarbeitung erfolgt mit dask und concurrent.futures, um die Effizienz zu maximieren.
"""

import os
import re
import json
import logging
from typing import List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import dask
from dask import delayed, compute
from tqdm import tqdm

# Konfiguration des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_video_urls_from_file(html_file: str) -> List[str]:
    """
    Extrahiert Video-URLs aus einer gegebenen HTML-Datei.

    :param html_file: Pfad zur HTML-Datei
    :return: Liste der extrahierten Video-URLs
    """
    logging.info(f"Extrahiere Video-URLs aus {html_file}")
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    video_urls = [
        tag.get('src') or tag.get('data-src')
        for tag in soup.find_all(['iframe', 'video', 'source'])
        if (src := tag.get('src') or tag.get('data-src')) and 'http' in src
    ]

    # Extrahiere URLs aus JSON-Teilen in Script-Tags
    for script in soup.find_all('script', type='text/javascript'):
        if script.string and 'kalturaIframePackageData' in script.string:
            json_text = re.search(r'window\.kalturaIframePackageData\s*=\s*(\{.*?\});', script.string, re.DOTALL)
            if json_text:
                data = json.loads(json_text.group(1))
                entry_result = data.get('entryResult', {})
                playlist_result = data.get('playlistResult', {})

                # Verarbeite entryResult für Video-URLs
                video_urls.extend(
                    entry.get('downloadUrl')
                    for entry in entry_result.get('meta', {}).get('flavorAssets', [])
                    if isinstance(entry, dict) and (download_url := entry.get('downloadUrl'))
                )

                # Verarbeite playlistResult für Video-URLs
                for key, value in playlist_result.items():
                    if isinstance(value, dict):
                        video_urls.extend(
                            item.get('dataUrl')
                            for item in value.get('items', [])
                            if (download_url := item.get('dataUrl'))
                        )

    logging.info(f"Gefundene Video-URLs in {html_file}: {len(video_urls)}")
    return video_urls

def process_file(html_file: str, source_directory: str, output_directory: str) -> None:
    """
    Verarbeitet eine einzelne HTML-Datei, extrahiert Video-URLs und speichert sie in einem entsprechenden Verzeichnis.

    :param html_file: Pfad zur HTML-Datei
    :param source_directory: Quellverzeichnis mit HTML-Dateien
    :param output_directory: Zielverzeichnis für die extrahierten Video-URLs
    """
    relative_path = os.path.relpath(html_file, source_directory)
    lesson_directory = os.path.join(output_directory, os.path.dirname(relative_path))
    os.makedirs(lesson_directory, exist_ok=True)
    video_urls = extract_video_urls_from_file(html_file)
    for i, url in enumerate(video_urls):
        output_file = os.path.join(lesson_directory, f"video_{i + 1}.txt")
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(url + '\n')
        logging.info(f"Video-URL gespeichert in {output_file}.")

def process_html_files(source_directory: str, output_directory: str) -> None:
    """
    Durchsucht rekursiv die Verzeichnisstruktur, extrahiert Video-URLs aus HTML-Dateien und speichert diese in entsprechenden Verzeichnissen.

    :param source_directory: Quellverzeichnis mit HTML-Dateien
    :param output_directory: Zielverzeichnis für die extrahierten Video-URLs
    """
    html_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(source_directory)
        for file in files if file.endswith('.html')
    ]

    if not html_files:
        logging.info("Keine HTML-Dateien im Quellverzeichnis gefunden.")
        return

    os.makedirs(output_directory, exist_ok=True)

    tasks = [
        delayed(process_file)(html_file, source_directory, output_directory)
        for html_file in html_files
    ]

    with tqdm(total=len(tasks), desc="Verarbeitung der HTML-Dateien") as pbar:
        for _ in compute(*tasks, scheduler='threads'):
            pbar.update(1)

def main() -> None:
    """
    Hauptfunktion des Skripts. Definiert Quell- und Zielverzeichnisse und startet die Verarbeitung.
    """
    source_directory = "/Users/python/Python Projekte/Studium Digitale/source"
    output_directory = "/Users/python/Python Projekte/Studium Digitale/links"

    process_html_files(source_directory, output_directory)

if __name__ == "__main__":
    main()
