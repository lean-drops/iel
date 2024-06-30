import os
import re
import json
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_video_urls(html_file):
    """Extract video URLs from the given HTML file."""
    logging.info(f"Extracting video URLs from {html_file}")
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    video_urls = []

    # Extract URLs from iframe, video, and source tags
    for tag in soup.find_all(['iframe', 'video', 'source']):
        src = tag.get('src') or tag.get('data-src')
        if src and 'http' in src:
            video_urls.append(src)

    # Extract URLs from JSON part in script tags
    for script in soup.find_all('script', type='text/javascript'):
        if script.string and 'kalturaIframePackageData' in script.string:
            json_text = re.search(r'window\.kalturaIframePackageData\s*=\s*(\{.*?\});', script.string, re.DOTALL)
            if json_text:
                data = json.loads(json_text.group(1))
                entry_result = data.get('entryResult', {})
                playlist_result = data.get('playlistResult', {})

                # Process entryResult for video URLs
                meta_entries = entry_result.get('meta', {}).get('flavorAssets', [])
                for entry in meta_entries:
                    if isinstance(entry, dict):
                        download_url = entry.get('downloadUrl')
                        if download_url:
                            video_urls.append(download_url)

                # Process playlistResult for video URLs
                for key, value in playlist_result.items():
                    if isinstance(value, dict):
                        items = value.get('items', [])
                        for item in items:
                            download_url = item.get('dataUrl')
                            if download_url:
                                video_urls.append(download_url)

    logging.info(f"Found {len(video_urls)} video URLs.")
    return video_urls


def main():
    # Definieren der HTML-Datei
    html_file = "/Users/python/Python Projekte/Studium Digitale/htmls/23448423.html"

    # Extrahieren der Video-URLs
    video_urls = extract_video_urls(html_file)

    # Definieren der Ausgabedatei
    output_file = os.path.splitext(html_file)[0] + '_video_urls.txt'

    # Schreiben der URLs in die Ausgabedatei
    with open(output_file, 'w') as file:
        for url in video_urls:
            file.write(url + '\n')

    logging.info(f"Video URLs saved to {output_file}")


if __name__ == "__main__":
   main()