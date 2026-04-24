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
        pass  # Silence les logs HTTP

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
        .signal { background: #0f3460; margin: 8px 0; padding: 10px; border-radius: 8px; border-left: 4px solid #e94560; font-size: 13px; }
        .signal .freq { font-size: 16px; font-weight: bold; color: #e94560; }
        .TRES_PROCHE { border-left-color: #ff0000; }
        .PROCHE      { border-left-color: #ff8800; }
        .MOYEN       { border-left-color: #ffff00; }
        .LOIN        { border-left-color: #00ff00; }
        h3 { color: #e94560; }
    </style>
</head>
<body>
    <div id="titre">🛰️ SDR - Système de Détection Radio - IUT Montbéliard</div>
    <div id="container">
        <div id="carte"></div>
        <div id="panneau">
            <h3>📡 Signaux détectés</h3>
            <div id="liste"></div>
        </div>
    </div>

<script>
    // Initialise la carte sur IUT Montbéliard
    var carte = L.map('carte').setView([47.5072, 6.7961], 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(carte);

    // Marqueur position récepteur
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

    function actualiser() {
        fetch('/signaux')
        .then(r => r.json())
        .then(signaux => {
            var liste = document.getElementById('liste');
            liste.innerHTML = '';

            signaux.slice().reverse().forEach(function(s) {
                // Carte — cercle autour du récepteur
                var id = s.freq.toFixed(3);
                if (!marqueurs[id]) {
                    var rayon = s.distance === 'TRES_PROCHE' ? 20 :
                                s.distance === 'PROCHE'      ? 80 :
                                s.distance === 'MOYEN'       ? 200 : 500;
                    marqueurs[id] = L.circle([47.5072, 6.7961], {
                        color: couleurDistance(s.distance),
                        fillOpacity: 0.3,
                        radius: rayon
                    }).addTo(carte)
                    .bindPopup('<b>' + s.freq.toFixed(3) + ' MHz</b><br>RSSI: ' + s.rssi + ' dB<br>BW: ' + s.bw + ' kHz<br>Distance: ' + s.distance);
                }

                // Panneau latéral
                var div = document.createElement('div');
                div.className = 'signal ' + s.distance;
                div.innerHTML =
                    '<div class="freq">' + s.freq.toFixed(3) + ' MHz</div>' +
                    'RSSI: ' + s.rssi + ' dB<br>' +
                    'BW: ' + s.bw + ' kHz<br>' +
                    'Distance: <b>' + s.distance + '</b><br>' +
                    '<small>' + s.heure + '</small>';
                liste.appendChild(div);
            });
        });
    }

    // Actualise toutes les 2 secondes
    setInterval(actualiser, 2000);
    actualiser();
</script>
</body>
</html>
"""

def ecouter_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5006))
    print("Ecoute UDP sur port 5005...")

    while True:
        data, _ = sock.recvfrom(1024)
        message = data.decode()
        print(f"Reçu : {message}")

        try:
            # Parse le message
            # Format: SIGNAL_DETECTE | FREQ:868.018MHz | RSSI:-45.2dB | BW:39kHz | DISTANCE:TRES_PROCHE
            parts = message.split("|")
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

            # Garde seulement les 100 derniers
            if len(signaux) > 100:
                signaux.pop(0)

        except Exception as e:
            print(f"Erreur parsing: {e}")

if __name__ == "__main__":
    # Lance l'écoute UDP dans un thread
    t = threading.Thread(target=ecouter_udp)
    t.daemon = True
    t.start()

    # Lance le serveur web
    print("Serveur web sur http://localhost:8080")
    print("Ouvre ton navigateur sur http://localhost:8080")
    HTTPServer(("0.0.0.0", 8080), WebHandler).serve_forever()
