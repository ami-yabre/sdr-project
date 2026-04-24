# Système de Localisation d'Émetteurs Radio SDR

## Description
Système de détection et localisation d'émetteurs radio à l'aide d'une radio logicielle (SDR) USRP B200 et GNU Radio.

## Signaux détectés
- LoRa 868 MHz
- WiFi 2.4 GHz
- Bluetooth 2.4 GHz
- 4G LTE 800 MHz

## Caractéristiques détectées par signal
- Fréquence (MHz)
- Puissance reçue (RSSI en dB)
- Largeur de canal (BW en kHz)
- Distance estimée (TRES_PROCHE / PROCHE / MOYEN / LOIN)

## Architecture
- GNU Radio + USRP B200 : capture et analyse du signal
- Serveur UDP : collecte les détections
- Client UDP : affiche les signaux en temps réel

## Structure du projet
sdr-project/
├── gnuradio/
│   ├── detecteur.py
│   └── flowgraph.grc
├── serveur/
│   └── serveur_udp.py
├── client/
│   └── client_udp.py
├── arduino/
│   ├── carte_a/carte_a.ino
│   └── carte_b/carte_b.ino
└── README.md

## Utilisation
1. Lancer GNU Radio avec flowgraph.grc
2. Lancer le serveur : python3 serveur/serveur_udp.py
3. Lancer le client : python3 client/client_udp.py
