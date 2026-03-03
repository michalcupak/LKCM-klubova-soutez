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

## Requirments
pip install requests beautifulsoup4 geopy python-dotenv

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

### Priklady CRON jobu
```
# v lednu a unoru kazdy den ve 3:30 spousti vypocet pro lonsky rocnik
30 03 * 1,2 * ~/LKCM-klubova-soutez/venv/bin/python3 ~/LKCM-klubova-soutez/soutez.py --year previous_year > ~/LKCM-klubova-soutez/logfile.log 2>&1

# kazdy den ve 4:30 spousti vypocet pro aktualni rocnik
30 04 * * * ~/LKCM-klubova-soutez/venv/bin/python3 ~/LKCM-klubova-soutez/soutez.py > ~/LKCM-klubova-soutez/logfile.log 2>&1

```

## How to deploy on Raspberry
 - prejit do adresare s repozitarem (~/LKCM-klubova-soutez)
 - smazat soubor ```soutez_vysledky.json```
 - git status
 - git fetch
 - git pull

## Věková soutěž
  - mladší junior - věk do 25 let 
  - starší junior - věk 26 - 40 let
  - mladší senior - věk 41 - 55 let
  - starší senior - věk 56 - 70 let
  - super senior - věk 70 a více let

## Todo
- doplnit **"Body CPS"** ke kazdemu pilotovi
- human-readable seznam kluzáků v typových kategoriích
