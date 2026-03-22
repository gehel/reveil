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
- **LED** clignotante
- **Moteur DC** piloté via un MOSFET **IRF510** pour faire vibrer le lit

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

### Générer les fichiers Gerber avec KiBot

Les fichiers de fabrication (Gerber, BOM, positions) sont générés via [KiBot](https://github.com/INTI-CMNB/KiBot) à partir de `config.kibot.yaml`.

```bash
kibot -c config.kibot.yaml
```

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
| GP18 | MOSFET IRF510 (moteur DC) | Gate |
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
- [ ] Créer un script de déploiement pour automatiser la copie du firmware et des bibliothèques sur le Pico.

## Licence

Matériel : [CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S)](https://ohwr.org/cern_ohl_s_v2.txt)
