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

### Skills Claude Code (kicad-happy)

Les skills [kicad-happy](https://github.com/aklofas/kicad-happy) (analyse schéma/PCB, BOM, datasheets, EMC, SPICE, fournisseurs JLCPCB/LCSC/DigiKey/Mouser…) sont installés au niveau du projet via [`skills`](https://github.com/vercel-labs/skills) :

```bash
npx skills add aklofas/kicad-happy
```

Seul `skills-lock.json` (sources et hashes des skills) est versionné ; les fichiers installés (`.agents/skills/`, et les liens symboliques `.claude/skills/`) sont ignorés par git. Pour les restaurer après un clone, ou les mettre à jour :

```bash
npx skills experimental_install   # restaure les skills depuis skills-lock.json
npx skills update -p               # met à jour les skills du projet (et skills-lock.json)
```

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
- `firmware/reveil/reglage_heure.py` — logique pure du réglage heure (cycle de modes, application d'une rotation sur heures/minutes) : même principe que `reglage_date.py`, réutilisé tel quel pour l'heure d'alarme
- `firmware/reveil/luminosite.py` — lecture du potentiomètre LUMINOSITE (classe `Potentiometre`) + conversion pure ADC→niveau MAX7219 (`niveau_depuis_adc()`)

`display.py`, `encoder.py` et `luminosite.py` séparent la construction matérielle (`depuis_broches()`/`depuis_broche()`, qui importent `board`/`busio`/`digitalio`/`rotaryio`/`analogio`) du reste de la classe, qui reçoit ses dépendances déjà construites — ça permet de tester leur logique (calcul de delta, détection de clic, écriture des digits, conversion ADC) avec de faux objets, sans Pico ni stubs CircuitPython. `code.py` déploie via ces méthodes ; les tests injectent de faux capteurs/chips (voir `firmware/tests/`).

`make deploy` copie `firmware/code.py` et aplatit `firmware/reveil/*.py` à la racine de `CIRCUITPY` (CircuitPython ne cherche les modules qu'à la racine et dans `lib/`, pas dans un sous-dossier arbitraire du dépôt).

### Mode de fonctionnement

**Affichages DATE et ANNEE.** En fonctionnement normal, l'affichage DATE montre le jour et le mois courants au format `JJ.MM` (point décimal séparateur entre les deux), et l'affichage ANNEE montre l'année sur 4 chiffres. Les valeurs viennent de l'horloge interne du RP2040 (module CircuitPython `rtc`) : celle-ci n'a **pas de pile de sauvegarde** sur cette carte, donc elle repart d'une date par défaut (1er janvier de l'année courante de développement) à chaque reset ou coupure d'alimentation — elle doit être réglée à nouveau à chaque démarrage.

**Réglage via l'encodeur REGLAGE_DATE.** Un clic sur le bouton de l'encodeur fait entrer/avancer dans le cycle de réglage :

1. Appui 1 → mode **réglage du jour** : le champ jour clignote (~1,25 Hz), tourner l'encodeur l'incrémente/décrémente (boucle 1 → dernier jour du mois → 1, en tenant compte des mois à 30/31 jours et des années bissextiles).
2. Appui 2 → mode **réglage du mois** : le champ mois clignote, rotation = incrément/décrément (boucle 1-12). Si le jour courant n'existe pas dans le nouveau mois (ex. 31 → février), il est ramené au dernier jour valide.
3. Appui 3 → mode **réglage de l'année** : l'affichage ANNEE clignote en entier, rotation = incrément/décrément (boucle 2000-2099). Même ajustement du jour si nécessaire (29 février d'une année non bissextile).
4. Appui 4 → retour au mode **normal** (plus aucun champ ne clignote), le cycle recommence au prochain clic.

Chaque changement de valeur est appliqué immédiatement à l'horloge RTC (pas de bouton "valider" séparé).

**Affichage HEURE.** En fonctionnement normal, montre l'heure courante au format `HH.MM` (point décimal séparateur). Même horloge RTC que DATE/ANNEE (pas de pile de sauvegarde, à régler à chaque démarrage).

**Réglage via l'encodeur REGLAGE_HEURE.** Cycle à 3 états (un champ de moins que REGLAGE_DATE, pas d'équivalent de l'année) :

1. Appui 1 → mode **réglage des heures** : le champ heures clignote, rotation = incrément/décrément (boucle 0-23).
2. Appui 2 → mode **réglage des minutes** : le champ minutes clignote, rotation = incrément/décrément (boucle 0-59).
3. Appui 3 → retour au mode **normal**, le cycle recommence au prochain clic.

Même principe que REGLAGE_DATE : chaque changement est appliqué immédiatement à l'horloge RTC.

**Affichage ALARME.** Montre l'heure d'alarme réglée, au format `HH.MM`. Contrairement à DATE/ANNEE/HEURE, ce n'est **pas** une valeur RTC : juste une paire (heures, minutes) gardée en mémoire côté firmware, réinitialisée à une valeur par défaut (7h00) à chaque démarrage — comme pour l'heure courante, il n'y a pas de pile de sauvegarde.

**Réglage via l'encodeur REGLAGE_ALARME.** Même cycle à 3 états que REGLAGE_HEURE (réglage des heures puis des minutes de l'alarme, mêmes bornes 0-23/0-59), avec les mêmes fonctions de logique (`reglage_heure.py` est réutilisé tel quel : une paire heures/minutes avec un cycle de réglage à 2 champs, que ce soit l'heure courante ou l'heure d'alarme).

**L'alarme ne se déclenche pas encore** : pas de comparaison avec l'heure courante, pas de pilotage de la LED ni du moteur. Seule l'heure d'alarme peut être affichée et réglée pour l'instant.

**Luminosité via le potentiomètre LUMINOSITE.** Lu en continu (à chaque itération de la boucle principale) et appliqué aux deux puces MAX7219 (donc aux 4 affichages). La valeur ADC brute (0-65535) est convertie en niveau MAX7219 (0-15) par `luminosite.niveau_depuis_adc()`.

**Pas encore géré par ce firmware** : déclenchement de l'alarme (LED, moteur), bouton d'allumage des affichages, bouton d'arrêt alarme, interrupteur SPDT — voir TODO.

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

### Améliorations matérielles proposées (revue schéma/PCB du 2026-10-03)

État au moment de la revue : ERC 0 erreur / 0 avertissement ; DRC 0 piste non connectée, 0 écart schéma/PCB, seulement 6 avertissements de sérigraphie de J2 coupée par le bord (normal pour un jack en bordure). Limite de la revue : aucun composant n'a de MPN ni de datasheet dans le projet, les valeurs datasheet citées ci-dessous n'ont pas été relues dans les PDF.

**Prioritaire**
- [x] **Symbole des afficheurs incohérent avec le câblage** : le schéma utilisait `CA56-12EWA` (anode commune), mais les anodes communes CA1-CA4 sont reliées aux sorties `DIG_x` du MAX7219 (qui *absorbent* le courant) et les segments aux sorties `SEG_x` (qui *fournissent* le courant). Avec de vrais afficheurs à anode commune, rien ne s'allumerait ; comme les afficheurs fonctionnent, les composants montés sont très probablement à cathode commune (confirmé par le fonctionnement du circuit, référence imprimée non relue). → Symbole remplacé par `CC56-12EWA` (même brochage/footprint `Display_7Segment:CA56-12EWA`, seules la doc et la BOM changent) dans `date.kicad_sch`, `heure_alarme.kicad_sch` et la `Value` des empreintes dans `reveil.kicad_pcb`. BOM/CPL JLCPCB (`jlcpcb/production_files/`) encore à régénérer via `kibot -c config.kibot.yaml` (kibot non disponible dans cet environnement).
- [ ] **Pas de diode de roue libre sur le moteur** : rien entre le drain de Q2 et VBUS, en parallèle de M1. La surtension inductive à chaque coupure passe par l'avalanche de Q2 et parasite le 5 V du Pico. → Ajouter une Schottky (1N5819) ou une 1N4148 entre le drain de Q2 et VBUS (cathode côté VBUS), plus 100 nF aux bornes du moteur contre les parasites des balais.
- [ ] **Grille de Q2 flottante au démarrage** : GPIO18 est en haute impédance pendant le boot/reset → vibration intempestive possible, ou Q2 à moitié passant qui chauffe. → Ajouter 100 kΩ grille-source, près de Q2. Éventuellement 47 kΩ base-émetteur sur Q1.
- [ ] **R1 sans valeur** (valeur « R ») : c'est la résistance ISET de U2. → Mettre 47 kΩ comme R2 (≈ 14 mA par segment), sinon HEURE/ALARME n'auront pas la même luminosité que DATE/ANNEE.

**Alimentation**
- [ ] **Le barrel jack J1 alimente directement VBUS** : si l'USB est branché en même temps, les deux 5 V sont en parallèle et l'alimentation du jack renvoie du courant vers le PC. Pas de protection contre l'inversion de polarité. → Rail 5 V externe pour MAX7219 + moteur + LED, Schottky de ce rail vers VSYS (broche 39), VBUS laissé à l'USB ; ajouter 220-470 µF en entrée.
- [ ] **Logique 3,3 V vers un MAX7219 alimenté en 5 V** : le VIH minimal du MAX7219 est de 3,5 V, les signaux du Pico sont hors spécification (ça marche, mais sans marge). → 74AHCT125 ou 74HCT245 alimenté en 5 V sur DIN/CLK/LOAD (6 signaux).
- [ ] **Découplage des MAX7219 trop loin** (datasheet : 10 µF + 100 nF au plus près de V+/GND). Distances estimées depuis la broche V+ : U1 → C1 ≈ 21 mm, C2 ≈ 30 mm ; U2 → C3 ≈ 12 mm, C4 ≈ 15 mm. → Rapprocher à moins de 5 mm (le balayage du MAX7219 crée de forts pics de courant).

**PCB**
- [ ] Toutes les pistes font 0,2 mm, alimentations comprises. → Passer VBUS, GND et le chemin moteur (drain de Q2) à 0,5-1 mm.
- [ ] Plan de masse B.Cu très découpé par les pistes de signal. → Ajouter des vias de couture GND, router moins en B.Cu.
- [ ] VIBREUR fait ≈ 169 mm entre le Pico et Q2. → Garder R5 et la future résistance de rappel près de Q2 (déjà le cas pour R5).
- [ ] Cartouche vide (titre, révision, date) sur le schéma et le PCB. → Le remplir (les sorties KiBot en profitent).
- [ ] Ajouter des points de test (voir section suivante).

**Fonctionnel**
- [ ] **Aucune sauvegarde de l'heure** : une coupure de courant efface l'heure et l'alarme, ce qui est critique pour un réveil. → DS3231 + pile CR2032 sur I2C (GP20/GP21 sont libres), et/ou synchronisation NTP par le WiFi du Pico W (firmware seul).
- [ ] **Une LED 3 mm (~16 mA) réveille mal.** → LED de puissance ou ruban LED commandé par un MOSFET, comme le moteur.
- [ ] **Moteur sur un jack 3,5 mm avec le +5 V sur le manchon** (exposé). → Connecteur polarisé et verrouillable (JST-XH, bornier). Pour M1, cocher « Exclure du PCB » plutôt que de laisser l'empreinte vide.
- [ ] Petits plus : bouton reset (RUN vers GND) pour le développement ; 100 nF sur le curseur de LUMINOSITE, alimenté par ADC_VREF/AGND ; filtres RC recommandés pour les encodeurs EC11 (10 kΩ + 10 nF).

**Faux positifs écartés par la revue** : 3V3_EN « sans pull-up » (pull-up interne au Pico), J2 « sans masse » (moteur commuté côté bas, voulu), absence de MPN (sans importance pour un montage à la main), J2 qui dépasse du bord (montage en bordure).

### Points de test proposés

Pastilles traversantes (`TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm`) ou boucles (`TestPoint:TestPoint_Keystone_5000-5004_Miniature`) pour les masses, avec la référence `TPx` et le nom du net sur la sérigraphie. À placer en bord de carte ou dans les zones dégagées, accessibles avec les afficheurs et les encodeurs montés.

| Point | Net | Usage |
|-------|-----|-------|
| TP1, TP2, TP3 | GND | Masse pour la pince de l'oscilloscope / du multimètre : une près de J1, une près des MAX7219, une près de Q2 (boucles) |
| TP4 | VBUS (5 V) | Tension d'entrée, chute sous charge (moteur + afficheurs à fond) |
| TP5 | +3V3 | Sortie du régulateur du Pico |
| TP6 | VSYS | Utile surtout si l'alimentation passe par VSYS (voir ci-dessus) |
| TP7, TP8, TP9 | DATE_DIN, DATE_CLK, DATE_LOAD | Trame SPI vers U1 (niveaux logiques, décodage à l'analyseur logique) |
| TP10, TP11, TP12 | HEURE_ALARME_DIN, HEURE_ALARME_CLK, HEURE_ALARME_LOAD | Trame SPI vers U2 |
| TP13 | Grille de Q2 (après R5) | Commande du moteur, état au démarrage (vérifie la résistance de rappel) |
| TP14 | Drain de Q2 | Surtension de coupure du moteur (vérifie la diode de roue libre), Vds en conduction |
| TP15 | Collecteur de Q1 | Commande de la LED (saturation de Q1) |
| TP16 | LUMINOSITE | Tension du curseur du potentiomètre (bruit lu par l'ADC) |
| TP17 | ISET de U1 ou U2 | Optionnel : contrôle de la résistance ISET sans dessouder |

Les signaux des encodeurs, des boutons et de l'interrupteur restent accessibles directement sur les broches des composants, pas besoin de points de test dédiés.

### Structure du firmware
- [x] `reveil/display.py`, `reveil/encoder.py`, `reveil/luminosite.py` — modules matériels (MAX7219, encodeurs rotatifs, potentiomètre ADC), construction hardware isolée dans `depuis_broches()`/`depuis_broche()` pour rester testables par injection de dépendances
- [x] `reveil/reglage_date.py`, `reveil/reglage_heure.py` — logique métier des réglages date/année et heure, isolée (modules purs, sans import CircuitPython). `reglage_heure.py` est réutilisé tel quel pour l'heure d'alarme (même forme : une paire heures/minutes avec un cycle de réglage à 2 champs)
- [ ] `alarm.py` — déclenchement de l'alarme (comparaison heure courante / heure d'alarme réglée, pilotage LED + moteur) pas encore implémenté ; l'heure d'alarme peut déjà être affichée et réglée
- [ ] `backlight.py` — extinction automatique des affichages après 30 s d'inactivité pas encore implémentée (luminosité l'est déjà via `luminosite.py`, mais l'allumage/extinction sur bouton est distinct)
- [ ] Isoler la logique métier restante (déclenchement alarme, extinction auto) au fur et à mesure qu'elle est écrite, sur le même modèle que `reglage_date.py`

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
- [x] ~~Écrire des stubs pour les modules CircuitPython~~ — évité par un autre moyen : `display.py`/`encoder.py`/`luminosite.py` séparent la construction matérielle (`depuis_broches()`/`depuis_broche()`) du reste de la classe, qui reçoit ses dépendances déjà construites (`board`/`busio`/`digitalio`/`rotaryio`/`analogio` ne sont importés que dans ces méthodes) ; les tests injectent de faux objets (voir `firmware/tests/test_display.py`, `test_encoder.py`, `test_luminosite.py`) sans avoir besoin de stubber les modules CircuitPython eux-mêmes
  - **Piège rencontré** : `firmware/code.py` (imposé par CircuitPython comme nom de point d'entrée) entre en collision avec le module standard `code` — si `firmware/` se retrouve dans `sys.path` (ex. `python -m pytest`, qui ajoute le répertoire courant), l'import de `code` par `pdb` récupère `firmware/code.py` à la place et plante. D'où `firmware/reveil/` comme dossier séparé pour la logique importable, et `pytest` invoqué directement (jamais `python -m pytest`) dans le Makefile.
- [x] Écrire les tests unitaires pour la logique métier des réglages date/année et heure (`firmware/tests/test_reglage_date.py`, `test_reglage_heure.py`, réutilisés pour l'heure d'alarme) et pour la conversion ADC→luminosité (`test_luminosite.py`) ; reste à faire au fur et à mesure pour le déclenchement de l'alarme, l'extinction automatique
- [x] Test de régression sur la position physique 4-7 de la puce Heure/Alarme (`test_display.py::test_heure_et_alarme_ne_se_marchent_pas_dessus`) — même classe de bug que l'inversion des digits déjà rencontrée sur Date/Année, jamais testée explicitement sur cette puce avant l'ajout d'ALARME

### Tests d'intégration (sur Pico)
- [ ] Ajouter `adafruit_unittest` aux dépendances
- [ ] Écrire les tests d'intégration pour chaque composant hardware
- [ ] Intégrer l'exécution via `mpremote run` dans le `Makefile`

## Licence

Matériel : [CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S)](https://ohwr.org/cern_ohl_s_v2.txt)
