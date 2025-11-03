import requests
import json
from dotenv import load_dotenv
import os
from ftp_upload import ftp_upload

load_dotenv()


def scrape_images():
    try:
        # poslednich 100 letu v CR
        # url = 'https://api.weglide.org/v1/flight?country_id_in=CZ&contest=free&order_by=-scoring_date&not_scored=false&story=false&valid=false&skip=0&limit=100&include_story=true&include_stats=false&format=json'

        # poslednich 100 letu clenu AK Medlanky
        url = 'https://api.weglide.org/v1/flight?club_id_in=1152&contest=free&order_by=-scoring_date&not_scored=false&story=false&valid=false&skip=0&limit=100&include_story=true&include_stats=false&format=json'

        # Lety Michal Cupak
        # url = 'https://api.weglide.org/v1/flight?user_id_in=11692&contest=free&order_by=-scoring_date&not_scored=false&story=false&valid=false&skip=0&limit=100&include_story=true&include_stats=false&format=json'

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        images = []
        for flight in data:
            if 'story' in flight:
                for image_url in flight['story']:
                    if image_url.endswith(('.jpg', '.png')):
                        large_image_url = image_url.replace('_small', '')
                        images.append({
                            "url": f'https://weglidefiles.b-cdn.net/{large_image_url}',
                            "pilot": flight['user']['name'],
                            "datum": flight['scoring_date'],
                        })
        return images
    except Exception as e:
        print(f"An error occurred: {e}")
        return []




if __name__ == '__main__':
    image_urls = scrape_images()
    print(image_urls)
    print()

    with open('/home/lkcm/LKCM-klubova-soutez/weglide_photos/image_urls.json', 'w', encoding="utf-8") as f:
        json.dump(image_urls, f, ensure_ascii=False, indent=2)

    ftp = ftp_upload.connect_to_ftp(os.getenv('FTP_SERVER'), os.getenv('FTP_USERNAME'), os.getenv('FTP_PASSWORD'))
    if ftp:
        ftp_upload.upload_file_to_ftp(ftp, "/home/lkcm/LKCM-klubova-soutez/weglide_photos/image_urls.json", "/www/subdom/lkcm/weglide_slideshow/image_urls.json")
        ftp.quit()

