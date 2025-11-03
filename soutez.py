import json

import requests
from bs4 import BeautifulSoup
# import pandas as pd
import re
from geopy.distance import geodesic
from datetime import datetime
from dateutil.parser import parse
from dotenv import load_dotenv
import os
from ftp_upload import ftp_upload

load_dotenv()

# Params
#cps_year = "2023"
cps_year = str(datetime.today().year)
LKCM_coordinates = (49.2369444, 16.5552778)
start_buffer_km = 20



def is_within_distance(coord1, coord2):
    distance = geodesic(coord1, coord2).km
    return distance <= start_buffer_km

def is_date_in_year(date_str):
    try:
        date = parse(date_str)
        return date.year == int(cps_year)
    except ValueError:
        return False

def find_flights_table(tables):
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) > 1 and rows[0].find_all(['th', 'td']):
            headers = [col.text.strip().lower() for col in rows[0].find_all(['th', 'td'])]
            if 'datum' in headers and 'body' in headers:
                return table
    return None


def get_start_coordinates(url):
    response = requests.get(url + "&rezim=varianty")
    soup = BeautifulSoup(response.content, 'html.parser')
    tratbods = soup.find_all('div', class_='tratbod')
    if len(tratbods) > 0:
        text = tratbods[0].text

        pattern = re.compile(r"(\d+)'(\d+)'(\d+)([NS]),(\d+)'(\d+)'(\d+)([EW])")
        match = pattern.search(text)
        if match:
            lat_deg, lat_min, lat_mmm, lat_dir, lon_deg, lon_min, lon_mmm, lon_dir = match.groups()

            lat_minutes = float(f"{lat_min}.{lat_mmm}")
            lon_minutes = float(f"{lon_min}.{lon_mmm}")

            lat = int(lat_deg) + lat_minutes / 60
            lon = int(lon_deg) + lon_minutes / 60

            if lat_dir == "S":
                lat = -lat
            if lon_dir == "W":
                lon = -lon

            return lat, lon

    return None


def get_pilot_flights(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table', class_='list-tbl')
    if len(tables) > 0:
        flights_table = find_flights_table(tables)
        flights_rows = []
        if flights_table:
            flights_rows = flights_table.find_all('tr')[1:]
        flights_data = []
        for row in flights_rows:
            cols = row.find_all('td')
            if len(cols) > 0:
                for col in cols:
                    if col.find('a') and col.find('a')['href'].startswith('index3.php?lpg=zobraz_let'):
                        let_url = 'https://www.cpska.cz/public/' + col.find('a')['href']
                        start_coordinates = get_start_coordinates(let_url)
                        try:
                            flight_data = {
                                'date': cols[0].text.strip(),
                                'points': int(cols[2].text.strip().replace('\u202f', '').replace('b', '')),
                                'url': let_url,
                                'start_coordinates': start_coordinates,
                                'lkcm_start': is_within_distance(LKCM_coordinates, start_coordinates),
                            }
                            if is_date_in_year(flight_data['date']):
                                flights_data.append(flight_data)
                        except ValueError:
                            continue
        return flights_data

    return []


def get_pilots_info(url):
    pilots = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    panels = soup.find_all('div', class_='panel_pilot')

    for panel in panels:
        pilot = {}

        jmeno_div = panel.find('div', class_='jmeno')
        rok_div = panel.find('div', class_='rok')

        if jmeno_div:
            pilot['name'] = jmeno_div.find('a').text.strip()
            pilot['url'] = 'https://www.cpska.cz/public/' + jmeno_div.find('a')['href'] + "&sez_rok=" + cps_year

        if rok_div:
            pilot['year_of_birth'] = rok_div.text.strip()

        flights = get_pilot_flights(pilot['url'])

        filtered_flights = [flight for flight in flights if flight.get('lkcm_start', False)]
        filtered_flights.sort(key=lambda x: x['points'], reverse=True)
        top_4_flights = filtered_flights[:4]

        sum_points = sum([flight['points'] for flight in top_4_flights])
        pilot['top_4_lkcm_flights'] = top_4_flights
        pilot['sum_of_points'] = sum_points
        print(pilot['name'] + ' ... ' + str(pilot['sum_of_points']))

        if pilot['sum_of_points'] > 0:
            pilots.append(pilot)

    return pilots


def main():
    print("AK Medlánky - Klubová soutěž " + cps_year + "\n")

    url = 'https://www.cpska.cz/public/index3.php?lpg=piloti&klub=4'
    pilots_info = get_pilots_info(url)
    pilots_info.sort(key=lambda x: x['sum_of_points'], reverse=True)

    soutez_vysledky = {
        "cps_year": cps_year,
        "updated_at": datetime.now().strftime('%d. %m. %Y %H:%M:%S'),
        "pilots_info": pilots_info,
    }

    with open('/home/lkcm/LKCM-klubova-soutez/soutez_vysledky.json', 'w', encoding="utf-8") as f:
        json.dump(soutez_vysledky, f, ensure_ascii=False, indent=2)

    print()

    html_content = '<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8">'
    html_content += '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">'
    html_content += '</head><body>'

    html_content += "<div class='container-fluid ml-2 mr-2'>"
    html_content += f"<h1>AK Medlánky - Klubová soutěž {cps_year}</h1>"
    html_content += f"<p>Aktualizováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html_content += "<div class='row'>"

    # Table
    html_content += "<div class='col-xl-6 col-lg-8 col-md-10'>"
    html_content += "<table class='table table-striped'>"
    html_content += "<tr><th>#</th><th>Jméno</th><th>Rok</th><th colspan='4'>4 nejlepší lety</th><!--th>Let 2</th><th>Let 3</th><th>Let 4</th--><th>Celkem</th></tr>"
    for i, pilot in enumerate(pilots_info, start=1):
        flights = pilot['top_4_lkcm_flights']
        lety = []
        for flight in flights:
            lety.append(
                f'<a href="{flight["url"]}" title="{flight["date"]}"><b>{flight["points"]}</b><span style="font-size: 0.6rem">&nbsp;b</span></a>')
        nejlepsi_lety = lety + [''] * (4 - len(lety))
        html_content += f"<tr><td>{i}</td><td><a href='{pilot['url']}'>{pilot['name']}</a></td><td>{pilot['year_of_birth']}</td><td>{nejlepsi_lety[0]}</td><td>{nejlepsi_lety[1]}</td><td>{nejlepsi_lety[2]}</td><td>{nejlepsi_lety[3]}</td><td><b>{pilot['sum_of_points']}</b><span style='font-size: 0.6rem'>&nbsp;b</span></td></tr>"
    html_content += "</table>"
    html_content += "</div>"

    html_content += "</div>"  # Close row
    html_content += "<hr/><h3>Pravidla</h3><ul><li>započítává lety z CPS - modré i šedé body</li><li>započítává pouze lety, které mají startovní pásku maximálně ve vzdálenosti 20km od vztažného bodu LKCM</li><li>každému pilotovi se započítávají 4 nejlepší lety v daném roce</li></ul>"
    html_content += "</div>"  # Close container
    html_content += '</body></html>'

    with open('/home/lkcm/LKCM-klubova-soutez/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    ftp = ftp_upload.connect_to_ftp(os.getenv('FTP_SERVER'), os.getenv('FTP_USERNAME'), os.getenv('FTP_PASSWORD'))
    if ftp:
        ftp_upload.upload_file_to_ftp(ftp, "/home/lkcm/LKCM-klubova-soutez/soutez_vysledky.json", "/www/subdom/lkcm/soutez_v2/soutez_vysledky.json")
        ftp_upload.upload_file_to_ftp(ftp, "/home/lkcm/LKCM-klubova-soutez/index.html", "/www/subdom/lkcm/soutez/index.html")
        ftp.quit()

if __name__ == '__main__':
    main()