# Réveil pour sourd

> **Statut : en cours de développement**

Réveil électronique custom conçu pour les personnes sourdes ou malentendantes. Au lieu d'une alarme sonore, le réveil utilise une LED clignotante et un moteur vibrant pour réveiller l'utilisateur.

## Matériel

### Microcontrôleur
- **Raspberry Pi Pico W** (RP2040) — firmware CircuitPython

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
- **Moteur DC** piloté via un MOSFET (Q2) pour faire vibrer le lit — **IRLB8721PbF** (logic-level) dans le schéma/PCB, avec une résistance de grille R5 (100 Ω) ; la carte physique a encore l'ancien **IRF510** sans résistance de grille, rework pas encore fait (voir TODO)

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
| GP18 | MOSFET moteur DC (Q2) | Gate |
| GP19 | Interrupteur SPDT alarme | Signal |
| GP26 | Potentiomètre luminosité | ADC |

## Logiciel

Firmware écrit en **CircuitPython**. Point d'entrée : `firmware/code.py`. La logique est dans `firmware/reveil/` :
- `firmware/reveil/display.py` — pilotage des 2 puces MAX7219 (classe `Afficheurs`)
- `firmware/reveil/encoder.py` — encodeur rotatif + bouton associé (classe `Encodeur`)
- `firmware/reveil/reglage_date.py` — logique pure du réglage date/année (cycle de modes, calcul des jours par mois, application d'une rotation) : aucune dépendance matérielle, testable directement sur l'hôte

`display.py` et `encoder.py` séparent la construction matérielle (`depuis_broches()`, qui importe `board`/`busio`/`digitalio`/`rotaryio`) du reste de la classe, qui reçoit ses dépendances déjà construites — ça permet de tester leur logique (calcul de delta, détection de clic, écriture des digits) avec de faux objets, sans Pico ni stubs CircuitPython. `code.py` déploie via `depuis_broches()` ; les tests injectent de faux capteurs/chips (voir `firmware/tests/`).

`make deploy` copie `firmware/code.py` et aplatit `firmware/reveil/*.py` à la racine de `CIRCUITPY` (CircuitPython ne cherche les modules qu'à la racine et dans `lib/`, pas dans un sous-dossier arbitraire du dépôt).

### Mode de fonctionnement

**Affichages DATE et ANNEE.** En fonctionnement normal, l'affichage DATE montre le jour et le mois courants au format `JJ.MM` (point décimal séparateur entre les deux), et l'affichage ANNEE montre l'année sur 4 chiffres. Les valeurs viennent de l'horloge interne du RP2040 (module CircuitPython `rtc`) : celle-ci n'a **pas de pile de sauvegarde** sur cette carte, donc elle repart d'une date par défaut (1er janvier de l'année courante de développement) à chaque reset ou coupure d'alimentation — elle doit être réglée à nouveau à chaque démarrage.

**Réglage via l'encodeur REGLAGE_DATE.** Un clic sur le bouton de l'encodeur fait entrer/avancer dans le cycle de réglage :

1. Appui 1 → mode **réglage du jour** : le champ jour clignote (~1,25 Hz), tourner l'encodeur l'incrémente/décrémente (boucle 1 → dernier jour du mois → 1, en tenant compte des mois à 30/31 jours et des années bissextiles).
2. Appui 2 → mode **réglage du mois** : le champ mois clignote, rotation = incrément/décrément (boucle 1-12). Si le jour courant n'existe pas dans le nouveau mois (ex. 31 → février), il est ramené au dernier jour valide.
3. Appui 3 → mode **réglage de l'année** : l'affichage ANNEE clignote en entier, rotation = incrément/décrément (boucle 2000-2099). Même ajustement du jour si nécessaire (29 février d'une année non bissextile).
4. Appui 4 → retour au mode **normal** (plus aucun champ ne clignote), le cycle recommence au prochain clic.

Chaque changement de valeur est appliqué immédiatement à l'horloge RTC (pas de bouton "valider" séparé).

**Pas encore géré par ce firmware** : affichages HEURE et ALARME, encodeurs REGLAGE_HEURE et REGLAGE_ALARME, luminosité (potentiomètre), bouton d'allumage des affichages, bouton d'arrêt alarme, interrupteur SPDT, LED et moteur — voir TODO.

### Dépendances

Les bibliothèques CircuitPython nécessaires sont listées dans `firmware/requirements.txt` :

```
adafruit_max7219
```

Copier les bibliothèques dans le dossier `lib/` du Pico (accessible en mode stockage USB), ou via `make deps` (voir `firmware/Makefile`).

## TODO

### Problèmes matériels connus
- [x] Court-circuit GND/+3V3 via l'interrupteur `ALARME_ON_OFF1` : le footprint système (`Button_Switch_THT:SW_Slide-03_Wuerth-WS-SLTV...`) avait les pads 1 et 2 physiquement inversés par rapport au composant monté. Corrigé via une librairie locale `reveil.pretty/` (pads 1/2 échangés) + `fp-lib-table`. Vérifié par mesure au multimètre, ERC et DRC (voir historique git).
- [x] LED D1 toujours allumée faiblement au lieu de clignoter : la base de Q1 (2N3904, driver de D1) était câblée directement sur GP17 sans résistance série, empêchant GP17 d'atteindre un état haut propre (chargé par la jonction base-émetteur). Corrigé dans KiCad : ajout de **R4 = 1.5 kΩ** en série sur la base, et **R3 = 100 Ω** (au lieu de 47 kΩ, qui aurait quasi éteint la LED) pour ~16 mA dans D1 (LED blanche, Vf≈3.2V supposé — pas de référence/datasheet exacte pour D1, à vérifier si besoin de précision). Vérifié par ERC/DRC.
  - [ ] **Bloquant pour tester la LED** : le PCB physique existant n'a pas ces corrections (footprint switch + R3/R4) — il faut ressouder à la main (bodge) ou fabriquer un nouveau PCB avant de pouvoir tester `code.py` avec `board.LED` remplacé par `board.GP17`. `firmware/code.py` a été remis à `board.LED` (LED embarquée du Pico) en attendant.
- [x] **Décalage schéma/carte physique — Q2 (moteur DC)** : le schéma KiCad indiquait un IRF540N, mais le MOSFET réellement monté sur le PCB physique était un IRF510. Résolu en remplaçant Q2 par un **IRLB8721PbF** (logic-level) dans le schéma et le PCB — voir point suivant, qui couvre aussi la raison de ce changement. Footprint `TO-220-3_Horizontal_TabDown` (corrigé après repérage d'une variante `TO-220F` erronée), pinout G/D/S broches 1/2/3 vérifié contre la convention IR/Infineon. Vérifié par ERC/DRC.
- [x] **Pilotage de grille de Q2 (moteur DC)** : topologie de câblage correcte (Gate←GP18, Drain→moteur(-), Source→GND, moteur(+)→VBUS ; vérifié via l'analyse du netlist). Le problème identifié :
  - GP18 pilote la grille de Q2 directement en 3.3V, sans résistance de grille ni driver dédié.
  - Ni l'IRF540N (ancien schéma) ni l'IRF510 (carte physique) ne sont des MOSFET **"logic-level"** : leur Rds(on) nominal est spécifié à Vgs=10V (IRF510 : ~0.54Ω max ; IRF540N : ~44-77 mΩ). À 3.3V (Vgs proche du seuil typique 2-4V de ces composants), le MOSFET risque de ne pas être pleinement enhancé → Rds(on) effectif bien plus élevé que la valeur datasheet → échauffement de Q2 et/ou sous-alimentation du moteur.
  - Corrigé dans KiCad : Q2 remplacé par un **IRLB8721PbF** (Vgs(th) ≈ 1-2V, pleinement enhancé dès Vgs≈2.5V, Rds(on) ≈ 8.7 mΩ typique à Vgs=4.5V — largement suffisant en pilotage direct 3.3V), plus ajout de **R5 = 100 Ω** en série sur la grille (limite le pic de courant transitoire vu par GP18 et amortit le ringing). Vérifié par ERC/DRC.
  - [ ] **Bloquant pour tester le moteur** : le PCB physique existant a encore l'ancien IRF510 sans R5 — il faut ressouder à la main (bodge) ou fabriquer un nouveau PCB avant de pouvoir tester le moteur avec ce circuit. Un moteur de test n'est de toute façon pas encore disponible.

### Structure du firmware
- [x] `reveil/display.py`, `reveil/encoder.py` — modules matériels (MAX7219, encodeurs rotatifs), construction hardware isolée dans `depuis_broches()` pour rester testables par injection de dépendances
- [x] `reveil/reglage_date.py` — logique métier du réglage date/année, isolée (module pur, sans import CircuitPython)
- [ ] `alarm.py`, `backlight.py` — pas encore nécessaires (alarme, luminosité/extinction auto pas encore implémentées)
- [ ] Isoler la logique métier restante (alarme, extinction auto) au fur et à mesure qu'elle est écrite, sur le même modèle que `reglage_date.py`

### Déploiement (Makefile)
- [x] Créer un `Makefile` (`firmware/Makefile`) avec les cibles :
  - `make install-circuitpython` — flashe CircuitPython sur le Pico
  - `make deploy` — copie `code.py` et aplatit `reveil/*.py` à la racine du volume `CIRCUITPY` monté par l'hôte (pas `mpremote fs cp`, qui échoue en lecture seule sur CircuitPython)
  - `make deps` — installe les dépendances CircuitPython via `circup`
  - [x] `make test-unit` — lance les tests unitaires sur l'hôte (`pytest tests/`)
  - [ ] `make test-integration` — lance les tests d'intégration sur le Pico via `mpremote run` (cible stub, pas encore exécutable)
- [x] Séparer les dépendances : `firmware/requirements.txt` (librairies CircuitPython installées sur le Pico via `circup`, ce n'est pas un fichier pip) vs `requirements-dev.txt` à la racine (outillage hôte : `circup`, `pytest`, stubs d'autocomplete ; `kibot` nécessite Docker, voir commentaire dans le fichier)
- [ ] Envisager une migration vers Poetry (ou un outil équivalent) pour `requirements-dev.txt` si le besoin de lockfile reproductible ou de gestion d'environnement plus poussée se fait sentir — pas nécessaire pour l'instant (projet hobby solo, peu de dépendances)

### Tests unitaires (sur hôte)
- [x] Mettre en place `pytest` (`firmware/pytest.ini`, `firmware/tests/`, lancés via `make test-unit`)
- [x] ~~Écrire des stubs pour les modules CircuitPython~~ — évité par un autre moyen : `display.py`/`encoder.py` séparent la construction matérielle (`depuis_broches()`) du reste de la classe, qui reçoit ses dépendances déjà construites (`board`/`busio`/`digitalio`/`rotaryio` ne sont importés que dans `depuis_broches()`) ; les tests injectent de faux objets (voir `firmware/tests/test_display.py`, `test_encoder.py`) sans avoir besoin de stubber les modules CircuitPython eux-mêmes
  - **Piège rencontré** : `firmware/code.py` (imposé par CircuitPython comme nom de point d'entrée) entre en collision avec le module standard `code` — si `firmware/` se retrouve dans `sys.path` (ex. `python -m pytest`, qui ajoute le répertoire courant), l'import de `code` par `pdb` récupère `firmware/code.py` à la place et plante. D'où `firmware/reveil/` comme dossier séparé pour la logique importable, et `pytest` invoqué directement (jamais `python -m pytest`) dans le Makefile.
- [x] Écrire les tests unitaires pour la logique métier du réglage date/année (`firmware/tests/test_reglage_date.py`) ; reste à faire au fur et à mesure pour l'alarme, les encodeurs restants, l'extinction automatique

### Tests d'intégration (sur Pico)
- [ ] Ajouter `adafruit_unittest` aux dépendances
- [ ] Écrire les tests d'intégration pour chaque composant hardware
- [ ] Intégrer l'exécution via `mpremote run` dans le `Makefile`

## Licence

Matériel : [CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S)](https://ohwr.org/cern_ohl_s_v2.txt)
