## Úvod

Repozitář obsahuje pomocné skripty pro klubovou soutěž AK Medlánky a související webové výstupy.

Součástí projektu je:
- generování výsledků klubové, typové a věkové soutěže z CPS,
- generování seznamu fotek z WeGlide pro slideshow,
- upload vygenerovaných JSON souborů na server přes FTP/FTPS,
- `web_scaler` pro zobrazení webového obsahu v automaticky škálovaném okně.

## PRAVIDLA
- zapocitava vsechny lety z CPS - modre i sede body
- zapocitava pouze lety, ktere maji startovni pasku maximalne ve vzdalenosti 20km od vztazneho bodu LKCM
- v celkové soutěži se každému pilotovi započítávají 4 nejlepší lety v daném roce 
- v typové a věkové soutěži se každému pilotovi započítává 1 nejlepší let v každé kategorii v daném roce

### Typová soutěž (orientační výčet)
  - Club - Std. Cirrus; ASW-15,19,24; Atlas; LS1; Astir; Cobra; Phoebus; PIK-20; Discus
  - Classic - Orlík; M-28,35; Foka; Ka 6
  - Základní - Blaník; Bergfalke; Šohaj; Luňák
  - Volná - Ventus; LAK-17; ASW-20; Nimbus; ASG-29,32, JS3

### Věková soutěž
  - mladší junior - věk do 25 let 
  - starší junior - věk 26 - 40 let
  - mladší senior - věk 41 - 55 let
  - starší senior - věk 56 - 70 let
  - super senior - věk 70 a více let

## .env

Nastavit promenne v ```~/.config/LKCM-klubova-soutez/.env``` podle ```.env_default```

### Proměnné prostředí

Konfigurace se načítá ze souboru `~/.config/LKCM-klubova-soutez/.env`.

FTP/FTPS:
- `FTP_SERVER` - adresa FTP serveru,
- `FTP_USERNAME` - uživatelské jméno,
- `FTP_PASSWORD` - heslo,
- `FTP_DIRECTORY_PATH_SOUTEZ` - cílová složka pro výsledky soutěže,
- `FTP_DIRECTORY_PATH_WEGLIDE_SLIDESHOW` - cílová složka pro slideshow fotek z WeGlide.

Kategorie kluzáků:
- `CATEGORY_CLUB` - seznam typů pro kategorii Club,
- `CATEGORY_CLASSIC` - seznam typů pro kategorii Classic,
- `CATEGORY_ZAKLADNI` - seznam typů pro kategorii Základní,
- `CATEGORY_OPEN` - seznam typů pro kategorii Volná/Open.

WeGlide:
- `WEGLIDE_FLIGHTS_URL` - URL endpointu WeGlide API pro výběr letů, ze kterých se načítají fotky.

Hodnoty kategorií jsou JSON seznamy, např.:
```
CATEGORY_CLUB=["Std. Cirrus","ASW-15","ASW-19"]
```

## Skripty

### `soutez.py`

Generuje výsledky klubové soutěže z CPS.

Skript:
- načte piloty AK Medlánky z CPS,
- dohledá lety pilotů za zvolený rok,
- započítá pouze lety se startovní páskou do 20 km od vztažného bodu LKCM,
- spočítá celkovou, typovou a věkovou soutěž,
- uloží výsledky do JSON,
- nahraje výsledky přes FTPS na server.

### `get_weglide_photos.py`

Generuje seznam fotek pro WeGlide slideshow.

Skript:
- načte poslední lety podle `WEGLIDE_FLIGHTS_URL`,
- pro každý let zavolá `/v1/story/{flight_id}`,
- z příběhu letu vybere obrázky,
- uloží seznam URL fotek do JSON,
- nahraje JSON přes FTPS na server.

### `web_scaler/web_scaler.html`

Jednoduchá HTML stránka pro zobrazení jiné webové stránky v iframe se zadaným měřítkem.

Použití:
```
web_scaler/?url=https://example.com&zoom=1.5
```

Parametry:
- `url` - adresa stránky, která se má zobrazit,
- `zoom` - měřítko zobrazení, výchozí hodnota je `1`.

## Výstupy

Lokálně se generují tyto soubory:
- `soutez_vysledky/soutez_vysledky.json` - výsledky soutěže pro zvolený rok,
- `soutez_vysledky/year_map.json` - mapa roků na dostupné soubory výsledků na serveru,
- `weglide_photos/image_urls.json` - seznam fotek pro WeGlide slideshow.

Na server se uploadují:
- `${FTP_DIRECTORY_PATH_SOUTEZ}/soutez_vysledky/soutez_vysledky_<rok>.json`,
- `${FTP_DIRECTORY_PATH_SOUTEZ}/year_map.json`,
- `${FTP_DIRECTORY_PATH_WEGLIDE_SLIDESHOW}/image_urls.json`.

## Zdroje dat

Soutěž:
- CPS stránka pilotů AK Medlánky: `https://www.cpska.cz/public/index3.php?lpg=piloti&klub=4`,
- detail letu v CPS pro zjištění typu kluzáku, bodů, tratě a startovní pásky.

WeGlide slideshow:
- `WEGLIDE_FLIGHTS_URL` z `.env`,
- detail příběhu letu přes endpoint `/v1/story/{flight_id}`,
- obrázky se skládají jako URL pod `https://weglidefiles.b-cdn.net/`.

## How to deploy
```
# create user and clone repo
sudo adduser worker
su worker
cd ~
git clone https://github.com/michalcupak/LKCM-klubova-soutez.git
chmod 700 LKCM-klubova-soutez
cd LKCM-klubova-soutez

# create venv and install requirements
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# create config dir and .env file
mkdir ~/.config/LKCM-klubova-soutez
cp .env_default ~/.config/LKCM-klubova-soutez/.env
chmod 600 ~/.config/LKCM-klubova-soutez/.env
# edit .env - set your credentials

# run scripts
.venv/bin/python soutez.py
.venv/bin/python get_weglide_photos.py
```


### Run scripts on cron
prepare logs folder
```
su worker
mkdir ~/logs
chmod 700 ~/logs
```
Edit crontab
```
su worker
crontab -e
```
add lines:
```
# get weglide photos
10 03 * * * ~/LKCM-klubova-soutez/.venv/bin/python ~/LKCM-klubova-soutez/get_weglide_photos.py > ~/logs/get_weglide_photos.log 2>&1

# v lednu, unoru kazdy den ve 3:30 spousti vypocet pro lonsky rocnik
30 03 * 1,2 * ~/LKCM-klubova-soutez/.venv/bin/python ~/LKCM-klubova-soutez/soutez.py --year previous_year > ~/logs/soutez_previous_year.log 2>&1

# kazdy den ve 4:30 spousti vypocet pro aktualni rocnik
30 04 * * * ~/LKCM-klubova-soutez/.venv/bin/python ~/LKCM-klubova-soutez/soutez.py > ~/logs/soutez.log 2>&1
```  


## How to execute
```% python soutez.py```  
Výstupem je soubor ```soutez_vysledky.json```, ktery je ve skriptu zaroven uploadovan na FTP

### Parametry - příklady spuštění
```
# Výchozí chování – aktuální rok
python soutez.py

# Konkrétní rok
python soutez.py --year 2024

# Loňský rok (dopočítá se automaticky)
python soutez.py --year previous_year
```

## Lokální vývoj

Základní spuštění v lokálním prostředí:
```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p ~/.config/LKCM-klubova-soutez
cp .env_default ~/.config/LKCM-klubova-soutez/.env
.venv/bin/python soutez.py
.venv/bin/python get_weglide_photos.py
```

Pozor: oba hlavní skripty se po doběhnutí pokusí připojit na FTPS a uploadovat výstupy. Pro čistě lokální test je potřeba mít v `.env` platné FTP údaje, nebo dočasně upravit/spustit jen část skriptu, která generuje data.

## How to deploy new version on Raspberry
 - prejit do adresare s repozitarem (~/LKCM-klubova-soutez)
 - git status
 - git fetch
 - git pull

## Kontrola po nasazení

Po aktualizaci na Raspberry je vhodné zkontrolovat:
- `git status` - pracovní adresář by neměl obsahovat nechtěné lokální změny,
- výstup ručního spuštění `.venv/bin/python soutez.py`,
- výstup ručního spuštění `.venv/bin/python get_weglide_photos.py`,
- logy v `~/logs`,
- zda na serveru vznikly/aktualizovaly se cílové JSON soubory,
- zda web správně načítá aktuální `soutez_vysledky_<rok>.json`, `year_map.json` a `image_urls.json`.

## Troubleshooting

Časté problémy:
- prázdné výsledky soutěže - zkontrolovat dostupnost CPS, zvolený rok a zda lety splňují podmínku startu do 20 km od LKCM,
- chybějící typová kategorie - doplnit typ kluzáku do příslušné `CATEGORY_*` proměnné v `.env`,
- chyba WeGlide fotek - zkontrolovat `WEGLIDE_FLIGHTS_URL` a dostupnost WeGlide API,
- chyba uploadu - zkontrolovat `FTP_SERVER`, přihlašovací údaje a cílové cesty,
- chybějící `year_map.json` - ověřit, že na FTP existuje složka `soutez_vysledky` a že obsahuje soubory ve tvaru `soutez_vysledky_<rok>.json`,
- cron nic negeneruje - zkontrolovat absolutní cesty v crontabu, existenci `.venv`, práva k `.env` a logy v `~/logs`.

## Todo
- doplnit **"Body CPS"** ke kazdemu pilotovi
