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

## How to deploy
```
# create user and clone repo
sudo adduser worker
su worker
cd ~
git clone https://github.com/michalcupak/LKCM-klubova-soutez.git
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


## How to deploy new version on Raspberry
 - prejit do adresare s repozitarem (~/LKCM-klubova-soutez)
 - git status
 - git fetch
 - git pull


## Todo
- doplnit **"Body CPS"** ke kazdemu pilotovi

