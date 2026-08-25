import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from ftp_upload import ftp_upload
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

env_path = Path.home() / ".config" / "LKCM-klubova-soutez" / ".env"
load_dotenv(env_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'weglide_photos',), exist_ok=True)
output_path = os.path.join(BASE_DIR, 'weglide_photos', 'image_urls.json')

def convert_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y")

def get_story_url(flights_url, flight_id):
    parts = urlsplit(flights_url)
    return urlunsplit((parts.scheme, parts.netloc, f"/v1/story/{flight_id}", "", ""))

def get_pilot(flight):
    pilot = flight['user']['name']
    if "co_user" in flight and flight['co_user']['name'] != pilot:
        pilot += ' & ' + flight['co_user']['name']
    return pilot

def add_image(images, image_path, flight):
    if not image_path.lower().endswith(('.jpg', '.png')):
        return

    large_image_path = image_path.replace('_small', '')
    images.append({
        "url": f'https://weglidefiles.b-cdn.net/{large_image_path}',
        "pilot": get_pilot(flight),
        "datum": convert_date(flight['scoring_date']),
    })

def scrape_images():
    try:
        url = os.getenv('WEGLIDE_FLIGHTS_URL')
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        images = []
        for flight in data:
            if 'id' not in flight:
                continue

            story_response = requests.get(get_story_url(url, flight['id']), headers=headers, timeout=30)
            story_response.raise_for_status()
            story = story_response.json()

            for item in story:
                image_path = item.get('image')
                if image_path:
                    add_image(images, image_path, flight)
        return images
    except Exception as e:
        print(f"An error occurred: {e}")
        return []




if __name__ == '__main__':
    print("AK Medlánky - Get Weglide photos")
    print("spuštěno: " + datetime.now().strftime('%d. %m. %Y %H:%M:%S') + "\n")

    image_urls = scrape_images()
    print(image_urls)
    print()

    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(image_urls, f, ensure_ascii=False, indent=2)

    ftp = ftp_upload.connect_to_ftps(os.getenv('FTP_SERVER'), os.getenv('FTP_USERNAME'), os.getenv('FTP_PASSWORD'))
    if ftp:
        ftp_upload.upload_file_to_ftp(ftp, output_path, os.path.join(os.getenv('FTP_DIRECTORY_PATH_WEGLIDE_SLIDESHOW'), "image_urls.json"))
        ftp.quit()
