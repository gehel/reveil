# Réveil pour sourd

> **Statut : en cours de développement**

Réveil électronique custom conçu pour les personnes sourdes ou malentendantes. Au lieu d'une alarme sonore, le réveil utilise une LED clignotante et un moteur vibrant pour réveiller l'utilisateur.

## Matériel

### Microcontrôleur
- **Raspberry Pi Pico** (RP2040) — firmware CircuitPython

### Affichages
- **2× MAX7219** pilotant 4 affichages 7-segments de 4 chiffres chacun :
  - Affichage de la date (jour/mois)
  - Affichage de l'année
  - Affichage de l'heure courante
  - Affichage de l'heure d'alarme

### Contrôles

| Composant | Rôle |
|-----------|------|
| 3× encodeurs rotatifs | Réglage de la date/année, de l'heure, et de l'alarme |
| Bouton poussoir | Arrêt de l'alarme |
| Interrupteur SPDT | Activation / désactivation de l'alarme |
| Bouton poussoir | Allumage des affichages et LED (extinction automatique après 30 s d'inactivité) |
| Potentiomètre | Réglage de la luminosité des affichages 7-segments |

### Alarme
- **LED** blanche (D1) clignotante, pilotée via un transistor Q1 (2N3904)
- **Moteur DC** piloté via un MOSFET **IRF540N** (Q2) pour faire vibrer le lit

### Alimentation
- Port **USB** du Raspberry Pi Pico
- **Barrel jack** 5 V (alternatif)

## Fichiers KiCad

Les fichiers source KiCad sont à la racine du projet :

| Fichier | Contenu |
|---------|---------|
| `reveil.kicad_sch` | Schématique racine |
| `heure_alarme.kicad_sch` | Feuille *Heure et Alarme* |
| `date.kicad_sch` | Feuille *Date* |
| `reveil.kicad_pcb` | Layout PCB |
| `fp-lib-table` | Table de librairies de footprints du projet (référence `reveil.pretty/`) |
| `reveil.pretty/` | Librairie locale de footprints corrigés (overrides de footprints système erronés — voir TODO) |

### Générer les fichiers Gerber avec KiBot

Les fichiers de fabrication (Gerber, BOM, positions) sont générés via [KiBot](https://github.com/INTI-CMNB/KiBot) à partir de `config.kibot.yaml`. `kibot` nécessite `wxPython` (pas de wheel précompilé sur toutes les plateformes) — utiliser le conteneur Docker de la CI plutôt qu'un `pip install` local :

```bash
docker run --rm -v "$PWD":/mnt -w /mnt ghcr.io/inti-cmnb/kicad9_auto_full:latest kibot -c config.kibot.yaml
```

`kicad-cli` (ERC/DRC en ligne de commande) est fourni par l'installation KiCad elle-même — via le snap, il est accessible en `/snap/bin/kicad.kicad-cli` (pas `kicad-cli` directement sur le PATH).

Les fichiers générés se trouvent dans le dossier `Generated/`. Les fichiers prêts pour JLCPCB sont dans `jlcpcb/`.

## Connexions (RP2040)

| GPIO | Composant | Signal |
|------|-----------|--------|
| GP0  | Encodeur *Heure* | A |
| GP1  | Encodeur *Heure* | B |
| GP2  | Encodeur *Heure* | SW (bouton) |
| GP3  | Encodeur *Date/Année* | A |
| GP4  | Encodeur *Date/Année* | B |
| GP5  | MAX7219 *Heure/Alarme* | CS (LOAD) |
| GP6  | MAX7219 *Heure/Alarme* | CLK |
| GP7  | MAX7219 *Heure/Alarme* | DIN |
| GP8  | Encodeur *Date/Année* | SW (bouton) |
| GP9  | MAX7219 *Date/Année* | CS (LOAD) |
| GP10 | MAX7219 *Date/Année* | CLK |
| GP11 | MAX7219 *Date/Année* | DIN |
| GP12 | Encodeur *Alarme* | A |
| GP13 | Encodeur *Alarme* | B |
| GP14 | Encodeur *Alarme* | SW (bouton) |
| GP15 | Bouton allumage affichages | Signal |
| GP16 | Bouton arrêt alarme | Signal |
| GP17 | LED alarme | Signal |
| GP18 | MOSFET IRF540N (moteur DC) | Gate |
| GP19 | Interrupteur SPDT alarme | Signal |
| GP26 | Potentiomètre luminosité | ADC |

## Logiciel

Firmware écrit en **CircuitPython**. Source : `firmware/code.py`.

### Dépendances

Les bibliothèques CircuitPython nécessaires sont listées dans `firmware/requirements.txt` :

```
adafruit_max7219
```

Copier les bibliothèques dans le dossier `lib/` du Pico (accessible en mode stockage USB).

## TODO

### Problèmes matériels connus
- [x] Court-circuit GND/+3V3 via l'interrupteur `ALARME_ON_OFF1` : le footprint système (`Button_Switch_THT:SW_Slide-03_Wuerth-WS-SLTV...`) avait les pads 1 et 2 physiquement inversés par rapport au composant monté. Corrigé via une librairie locale `reveil.pretty/` (pads 1/2 échangés) + `fp-lib-table`. Vérifié par mesure au multimètre, ERC et DRC (voir historique git).
- [x] LED D1 toujours allumée faiblement au lieu de clignoter : la base de Q1 (2N3904, driver de D1) était câblée directement sur GP17 sans résistance série, empêchant GP17 d'atteindre un état haut propre (chargé par la jonction base-émetteur). Corrigé dans KiCad : ajout de **R4 = 1.5 kΩ** en série sur la base, et **R3 = 100 Ω** (au lieu de 47 kΩ, qui aurait quasi éteint la LED) pour ~16 mA dans D1 (LED blanche, Vf≈3.2V supposé — pas de référence/datasheet exacte pour D1, à vérifier si besoin de précision). Vérifié par ERC/DRC.
  - [ ] **Bloquant pour tester la LED** : le PCB physique existant n'a pas ces corrections (footprint switch + R3/R4) — il faut ressouder à la main (bodge) ou fabriquer un nouveau PCB avant de pouvoir tester `code.py` avec `board.LED` remplacé par `board.GP17`. `firmware/code.py` a été remis à `board.LED` (LED embarquée du Pico) en attendant.
- [ ] **À vérifier — pilotage de grille de Q2 (IRF540N, moteur DC)** : topologie de câblage correcte (Gate←GP18, Drain→moteur(-), Source→GND, moteur(+)→VBUS ; vérifié via l'analyse du netlist), mais **pas corrigé, à confirmer avant de faire tourner le moteur** :
  - GP18 pilote la grille de Q2 directement en 3.3V, sans résistance de grille ni driver dédié.
  - L'IRF540N n'est **pas un MOSFET "logic-level"** : son Rds(on) nominal (~44-77 mΩ) est spécifié à Vgs=10V. À 3.3V (Vgs proche du seuil typique 2-4V du composant), le MOSFET risque de ne pas être pleinement enhancé → Rds(on) effectif bien plus élevé que la valeur datasheet → échauffement de Q2 et/ou sous-alimentation du moteur.
  - Pas de résistance de grille série non plus (moins critique électriquement pour un MOSFET qu'un BJT, mais bonne pratique pour limiter les transitoires de commutation).
  - Pistes de correction possibles (non appliquées) : remplacer Q2 par un MOSFET logic-level (ex. IRLZ44N, AO3400), ou ajouter un étage driver de grille.

### Structure du firmware
- [ ] Séparer `code.py` en modules : `display.py`, `encoder.py`, `alarm.py`, `backlight.py`
- [ ] Isoler la logique métier des appels hardware pour permettre les tests sans matériel

### Déploiement (Makefile)
- [x] Créer un `Makefile` (`firmware/Makefile`) avec les cibles :
  - `make install-circuitpython` — flashe CircuitPython sur le Pico
  - `make deploy` — copie `code.py` (et `lib/` si présent) sur le volume `CIRCUITPY` monté par l'hôte (pas `mpremote fs cp`, qui échoue en lecture seule sur CircuitPython)
  - `make deps` — installe les dépendances CircuitPython via `circup`
  - [ ] `make test-unit` — lance les tests unitaires sur l'hôte (cible stub, pas encore exécutable)
  - [ ] `make test-integration` — lance les tests d'intégration sur le Pico via `mpremote run` (cible stub, pas encore exécutable)
- [x] Séparer les dépendances : `firmware/requirements.txt` (librairies CircuitPython installées sur le Pico via `circup`, ce n'est pas un fichier pip) vs `requirements-dev.txt` à la racine (outillage hôte : `circup`, stubs d'autocomplete ; `kibot` nécessite Docker, voir commentaire dans le fichier)
- [ ] Envisager une migration vers Poetry (ou un outil équivalent) pour `requirements-dev.txt` si le besoin de lockfile reproductible ou de gestion d'environnement plus poussée se fait sentir — pas nécessaire pour l'instant (projet hobby solo, peu de dépendances)

### Tests unitaires (sur hôte)
- [ ] Mettre en place `pytest`
- [ ] Écrire des stubs pour les modules CircuitPython (`board`, `busio`, `digitalio`, `adafruit_max7219`)
- [ ] Écrire les tests unitaires pour la logique métier (alarme, encodeurs, extinction automatique)

### Tests d'intégration (sur Pico)
- [ ] Ajouter `adafruit_unittest` aux dépendances
- [ ] Écrire les tests d'intégration pour chaque composant hardware
- [ ] Intégrer l'exécution via `mpremote run` dans le `Makefile`

## Licence

Matériel : [CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S)](https://ohwr.org/cern_ohl_s_v2.txt)
