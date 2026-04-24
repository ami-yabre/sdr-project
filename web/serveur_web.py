import socket
import threading
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Position fixe du récepteur (IUT Montbéliard)
LATITUDE  = 47.5072
LONGITUDE = 6.7961

# Stockage des signaux reçus
signaux = []

class WebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.page_html().encode())

        elif self.path == "/signaux":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(signaux[-50:]).encode())

    def page_html(self):
        return """
<!DOCTYPE html>
<html>
<head>
    <title>SDR - Détection Signaux Radio</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; font-family: Arial; background: #1a1a2e; color: white; }
        #titre { padding: 15px; text-align: center; background: #16213e; font-size: 22px; }
        #container { display: flex; height: calc(100vh - 60px); }
        #carte { flex: 2; }
        #panneau { flex: 1; padding: 15px; overflow-y: auto; background: #16213e; max-width: 350px; }
        .signal { background: #0f3460; margin: 8px 0; padding: 10px; border-radius: 8px; font-size: 13px; }
        .signal .freq { font-size: 16px; font-weight: bold; color: #e94560; }
        .TRES_PROCHE { border-left: 4px solid #ff0000; }
        .PROCHE      { border-left: 4px solid #ff8800; }
        .MOYEN       { border-left: 4px solid #ffff00; }
        .LOIN        { border-left: 4px solid #00ff00; }
        h3 { color: #e94560; }
        #legende { margin-top: 20px; padding: 10px; background: #0f3460; border-radius: 8px; }
        .leg-item { display: flex; align-items: center; margin: 5px 0; font-size: 12px; }
        .leg-cercle { width: 15px; height: 15px; border-radius: 50%; margin-right: 8px; }
    </style>
</head>
<body>
    <div id="titre">🛰️ SDR - Système de Détection Radio - IUT Montbéliard</div>
    <div id="container">
        <div id="carte"></div>
        <div id="panneau">
            <h3>📡 Signaux détectés</h3>
            <div id="liste"></div>

            <div id="legende">
                <b>Légende distance :</b>
                <div class="leg-item"><div class="leg-cercle" style="background:red"></div> TRES_PROCHE (&lt; 10m)</div>
                <div class="leg-item"><div class="leg-cercle" style="background:orange"></div> PROCHE (10-50m)</div>
                <div class="leg-item"><div class="leg-cercle" style="background:yellow"></div> MOYEN (50-200m)</div>
                <div class="leg-item"><div class="leg-cercle" style="background:green"></div> LOIN (&gt; 200m)</div>
            </div>
        </div>
    </div>

<script>
    var carte = L.map('carte').setView([47.5072, 6.7961], 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(carte);

    // Marqueur récepteur
    L.marker([47.5072, 6.7961])
        .addTo(carte)
        .bindPopup('<b>📡 Récepteur SDR</b><br>IUT R&T Montbéliard')
        .openPopup();

    var marqueurs = {};

    function couleurDistance(distance) {
        if (distance === 'TRES_PROCHE') return 'red';
        if (distance === 'PROCHE')      return 'orange';
        if (distance === 'MOYEN')       return 'yellow';
        return 'green';
    }

    function rayonDistance(distance) {
        if (distance === 'TRES_PROCHE') return 15;
        if (distance === 'PROCHE')      return 50;
        if (distance === 'MOYEN')       return 150;
        return 400;
    }

    function actualiser() {
        fetch('/signaux')
        .then(r => r.json())
        .then(signaux => {
            var liste = document.getElementById('liste');
            liste.innerHTML = '';

            signaux.slice().reverse().forEach(function(s) {
                var id = s.freq.toFixed(3);

                // Supprime l'ancien cercle si distance a changé
                if (marqueurs[id]) {
                    carte.removeLayer(marqueurs[id]);
                }

                // Nouveau cercle avec bonne taille
                marqueurs[id] = L.circle([47.5072, 6.7961], {
                    color:       couleurDistance(s.distance),
                    fillColor:   couleurDistance(s.distance),
                    fillOpacity: 0.3,
                    radius:      rayonDistance(s.distance),
                    weight:      2
                }).addTo(carte)
                .bindPopup(
                    '<b>📡 ' + s.freq.toFixed(3) + ' MHz</b><br>' +
                    '🔋 RSSI: ' + s.rssi + ' dB<br>' +
                    '📶 BW: ' + s.bw + ' kHz<br>' +
                    '📍 Distance: <b>' + s.distance + '</b><br>' +
                    '🕐 ' + s.heure
                );

                // Panneau latéral
                var div = document.createElement('div');
                div.className = 'signal ' + s.distance;
                div.innerHTML =
                    '<div class="freq">📡 ' + s.freq.toFixed(3) + ' MHz</div>' +
                    '🔋 RSSI: ' + s.rssi + ' dB<br>' +
                    '📶 BW: ' + s.bw + ' kHz<br>' +
                    '📍 Distance: <b>' + s.distance + '</b><br>' +
                    '🕐 ' + s.heure;
                liste.appendChild(div);
            });
        });
    }

    setInterval(actualiser, 2000);
    actualiser();
</script>
</body>
</html>
"""

def ecouter_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5006))
    print("Ecoute UDP sur port 5006...")

    while True:
        data, _ = sock.recvfrom(1024)
        message = data.decode()
        print(f"Reçu : {message}")

        try:
            parts    = message.split("|")
            freq     = float(parts[1].split(":")[1].replace("MHz","").strip())
            rssi     = float(parts[2].split(":")[1].replace("dB","").strip())
            bw       = float(parts[3].split(":")[1].replace("kHz","").strip())
            distance = parts[4].split(":")[1].strip()

            signal = {
                "freq":     freq,
                "rssi":     rssi,
                "bw":       bw,
                "distance": distance,
                "lat":      LATITUDE,
                "lon":      LONGITUDE,
                "heure":    time.strftime("%H:%M:%S")
            }
            signaux.append(signal)

            if len(signaux) > 100:
                signaux.pop(0)

        except Exception as e:
            print(f"Erreur parsing: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=ecouter_udp)
    t.daemon = True
    t.start()

    print("Serveur web sur http://localhost:8080")
    print("Ouvre ton navigateur sur http://localhost:8080")
    HTTPServer(("0.0.0.0", 8080), WebHandler).serve_forever()
