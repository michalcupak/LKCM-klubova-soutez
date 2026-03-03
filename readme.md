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
