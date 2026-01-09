import json
from collections import defaultdict

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
#cps_year = "2025"
#cps_year = str(datetime.today().year)
cps_year = str(datetime.today().year - (1 if datetime.today().month <= 3 else 0))
LKCM_coordinates = (49.2369444, 16.5552778)
start_buffer_km = 20

category_club = ["std. cirrus", "asw-15", "asw-19", "asw-24", "atlas", "ls-1", "astir", "cobra", "phoebus", "pik-20", "dg-300", "discus cs"]
category_classic = ["orlik", "m-28", "m-35", "foka", "ka 6"]
category_zakladni = ["blaník", "bergfalke", "šohaj", "luňák", "spatz"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(BASE_DIR, 'soutez_vysledky.json')

# global variables
types_per_category = defaultdict(set)

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


def get_more_flight_info(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # -------------------------------------------------
    # 1) Název kluzáku
    # -------------------------------------------------
    glider_name = None
    for div in soup.find_all("div", class_="panel_lt"):
        icon = div.find("img", class_="panel_icon")
        src = (icon.get("src") or "") if icon else ""
        if "lt32_glider.gif" in src:
            h3 = div.find("h3")
            if h3:
                glider_name = h3.get_text(strip=True)
            break

    # -------------------------------------------------
    # 2) Výkony letu (perf-tbl)
    # -------------------------------------------------
    task_distance_km = None
    task_speed_kmh = None
    task_shape = None
    task_type = None

    perf_tbl = soup.find("table", class_="perf-tbl")
    if perf_tbl:
        rows = perf_tbl.find_all("tr", recursive=False)

        # --- vzdálenost + rychlost (2. řádek)
        if len(rows) >= 2:
            tds = rows[1].find_all("td", recursive=False)
            if len(tds) >= 2:

                def parse_big_num(td):
                    int_span = td.find("span", class_="int")
                    frac_span = td.find("span", class_="frac")
                    if int_span:
                        num = int_span.get_text(strip=True)
                        if frac_span:
                            num += frac_span.get_text(strip=True)
                        try:
                            return float(num)
                        except ValueError:
                            pass

                    txt = td.get_text(" ", strip=True)
                    m = re.search(r"(\d+(?:[.,]\d+)?)", txt)
                    return float(m.group(1).replace(",", ".")) if m else None

                task_distance_km = parse_big_num(tds[0])
                task_speed_kmh = parse_big_num(tds[1])

        # --- tvar + typ letu (3. řádek)
        if len(rows) >= 3:
            p_tags = rows[2].find_all("p")

            def clean_text(txt: str) -> str:
                # odstraní úvodní piktogramy / symboly
                return re.sub(
                    r"^[^\wÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž]+",
                    "",
                    txt,
                ).strip()

            if len(p_tags) >= 1:
                task_shape = clean_text(p_tags[0].get_text(" ", strip=True))

            if len(p_tags) >= 2:
                task_type = clean_text(p_tags[1].get_text(" ", strip=True))

    if not any([glider_name, task_distance_km, task_speed_kmh]):
        return None

    return {
        "glider_name": glider_name,
        "task_distance_km": task_distance_km,
        "task_speed_kmh": task_speed_kmh,
        "task_shape": task_shape,
        "task_type": task_type,
    }


def get_category(glider_name: str) -> str:
    """Určí kategorii kluzáku podle typu (string z 'type')."""
    glider_name_norm = glider_name.lower()

    # kontrola přes "substring" – aby to fungovalo i kdyby tam bylo např. "Std. Cirrus B"
    for name in category_club:
        if name in glider_name_norm:
            return "club"

    for name in category_classic:
        if name in glider_name_norm:
            return "classic"

    for name in category_zakladni:
        if name in glider_name_norm:
            return "zakladni"

    return "open"


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
                        more_flight_info = get_more_flight_info(let_url) or {}
                        try:
                            flight_data = (
                                {
                                    'date': cols[0].text.strip(),
                                    'points': int(cols[2].text.strip().replace('\u202f', '').replace('b', '')),
                                    'url': let_url,
                                    'start_coordinates': start_coordinates,
                                    'lkcm_start': is_within_distance(LKCM_coordinates, start_coordinates),
                                    'category': get_category(more_flight_info["glider_name"])
                                }
                                |
                                more_flight_info
                            )
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
        #print(filtered_flights)

        # Top 4 flights
        top_4_flights = filtered_flights[:4]
        sum_points = sum([flight['points'] for flight in top_4_flights])
        pilot['top_4_lkcm_flights'] = top_4_flights
        pilot['sum_of_points'] = sum_points
        print(pilot['name'] + ' ... ' + str(pilot['sum_of_points']))


        # Typova soutez
        best_for_category = {}
        for flight in filtered_flights:
            category = flight["category"]

            # přidáme typ do množiny typů v kategorii (globálně)
            types_per_category[category].add(flight["glider_name"])

            # aktualizace nejlepšího letu pro danou kategorii a pilota
            if category not in best_for_category:
                best_for_category[category] = flight
            else:
                if flight["points"] > best_for_category[category]["points"]:
                    best_for_category[category] = flight

        pilot['best_lkcm_flights_by_category'] = best_for_category



        if pilot['sum_of_points'] > 0:
            pilots.append(pilot)

    return pilots


def hodnoceni_typove_souteze(pilots_info):
    typova_soutez_vysledky = {}
    for pilot in pilots_info:
        for category, flight in pilot['best_lkcm_flights_by_category'].items():
            flight["pilot"] = pilot['name']
            flight["pilot_year_of_birth"] = pilot['year_of_birth']
            flight["pilot_url"] = pilot['url']
            if category not in typova_soutez_vysledky:
                typova_soutez_vysledky[category] = [flight]
            else:
                typova_soutez_vysledky[category].append(flight)

    for category, flights in typova_soutez_vysledky.items():
        typova_soutez_vysledky[category] = sorted(flights, key=lambda x: x['points'], reverse=True)#[:3]

    return typova_soutez_vysledky


def main():
    print("AK Medlánky - Klubová soutěž " + cps_year)
    print("spuštěno: " + datetime.now().strftime('%d. %m. %Y %H:%M:%S') + "\n")

    url = 'https://www.cpska.cz/public/index3.php?lpg=piloti&klub=4'
    pilots_info = get_pilots_info(url)
    pilots_info.sort(key=lambda x: x['sum_of_points'], reverse=True)
    # print("pilots_info")
    # print(pilots_info)



    # Typova soutez
    print()
    typova_soutez_vysledky = hodnoceni_typove_souteze(pilots_info)
    print("typova_soutez_vysledky:")
    for category, flights in typova_soutez_vysledky.items():
        print(f"{category}:")
        for flight in flights[:3]:
            print(flight)
    print()
    print("types_per_category:")
    for category, types in types_per_category.items():
        print(f"{category}: {', '.join(sorted(types))}")



    soutez_vysledky = {
        "cps_year": cps_year,
        "updated_at": datetime.now().strftime('%d. %m. %Y %H:%M:%S'),
        "pilots_info": pilots_info,
        "typova_soutez_vysledky": typova_soutez_vysledky,
        "types_per_category": {k: list(v) for k, v in types_per_category.items()},
    }

    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(soutez_vysledky, f, ensure_ascii=False, indent=2)

    print()

    ftp = ftp_upload.connect_to_ftp(os.getenv('FTP_SERVER'), os.getenv('FTP_USERNAME'), os.getenv('FTP_PASSWORD'))
    if ftp:
        ftp_upload.upload_file_to_ftp(ftp, output_path, "/www/subdom/lkcm/soutez/soutez_vysledky.json")

        ftp.quit()

if __name__ == '__main__':
    main()
