import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from ftp_upload import ftp_upload
from pathlib import Path

env_path = Path.home() / ".config" / "LKCM-klubova-soutez" / ".env"
load_dotenv(env_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, 'weglide_photos',), exist_ok=True)
output_path = os.path.join(BASE_DIR, 'weglide_photos', 'image_urls.json')

def convert_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y")

def scrape_images():
    try:
        url = os.getenv('WEGLIDE_FLIGHTS_URL')
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        images = []
        for flight in data:
            if 'story' in flight:
                for image_url in flight['story']:
                    if image_url.endswith(('.jpg', '.png')):
                        large_image_url = image_url.replace('_small', '')
                        pilot = flight['user']['name']
                        if "co_user" in flight and flight['co_user']['name'] != pilot:
                            pilot += ' & ' + flight['co_user']['name']
                        images.append({
                            "url": f'https://weglidefiles.b-cdn.net/{large_image_url}',
                            "pilot": pilot,
                            "datum": convert_date(flight['scoring_date']),
                        })
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

