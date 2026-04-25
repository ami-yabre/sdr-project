import socket
import threading
import json
import time
import math
from http.server import HTTPServer, BaseHTTPRequestHandler

LATITUDE  = 47.5105
LONGITUDE = 6.7978

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
    <title>SDR - Système de Sauvetage</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; font-family: Arial; background: #1a1a2e; color: white; }
        #titre { padding: 12px; text-align: center; background: #c0392b; font-size: 18px; font-weight: bold; }
        #container { display: flex; height: calc(100vh - 50px); }
        #carte { flex: 2; }
        #panneau { flex: 1; padding: 15px; overflow-y: auto; background: #16213e; max-width: 380px; }
        h3 { color: #e94560; margin-top: 0; }
        .signal { background: #0f3460; margin: 8px 0; padding: 12px; border-radius: 8px; font-size: 13px; }
        .signal .type  { font-size: 11px; color: #aaa; }
        .signal .freq  { font-size: 15px; font-weight: bold; color: #e94560; }
        .signal .dist  { font-size: 14px; font-weight: bold; margin: 5px 0; }
        .signal .instruction { margin-top: 8px; padding: 8px; border-radius: 6px; font-size: 13px; font-weight: bold; }
        .TRES_PROCHE { border-left: 5px solid #ff0000; }
        .PROCHE      { border-left: 5px solid #ff8800; }
        .MOYEN       { border-left: 5px solid #ffff00; }
        .LOIN        { border-left: 5px solid #00ff00; }
        .instr_urgence { background: #c0392b; color: white; }
        .instr_proche  { background: #e67e22; color: white; }
        .instr_moyen   { background: #f39c12; color: #1a1a2e; }
        .instr_loin    { background: #27ae60; color: white; }
        #alerte_urgente {
            display: none;
            background: #c0392b;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            animation: clignoter 1s infinite;
        }
        @keyframes clignoter {
            0%   { opacity: 1; }
            50%  { opacity: 0.3; }
            100% { opacity: 1; }
        }
        #resume { background: #0f3460; padding: 10px; border-radius: 8px; margin-bottom: 10px; font-size: 13px; }
        #aucun_signal { background: #0f3460; padding: 15px; border-radius: 8px; text-align: center; color: #aaa; display: none; }
        #legende { margin-top: 15px; padding: 10px; background: #0f3460; border-radius: 8px; font-size: 12px; }
        .leg-item { display: flex; align-items: center; margin: 4px 0; }
        .leg-c { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
    </style>
</head>
<body>
    <div id="titre">🆘 SDR - Système de Localisation et Sauvetage — IUT Montbéliard</div>
    <div id="container">
        <div id="carte"></div>
        <div id="panneau">
            <div id="alerte_urgente">🚨 URGENCE — PERSONNE DÉTECTÉE À MOINS DE 25m !</div>
            <h3>📡 Signaux détectés</h3>
            <div id="resume">En attente de signaux...</div>
            <div id="aucun_signal">
                ✅ Aucun signal proche détecté<br>
                <small>Les antennes opérateurs sont filtrées</small>
            </div>
            <div id="liste"></div>
            <div id="legende">
                <b>Légende :</b>
                <div class="leg-item"><div class="leg-c" style="background:red"></div> &lt; 25m — Fouiller immédiatement</div>
                <div class="leg-item"><div class="leg-c" style="background:orange"></div> 25-100m — Se rapprocher</div>
                <div class="leg-item"><div class="leg-c" style="background:yellow"></div> 100-350m — Zone de recherche</div>
                <div class="leg-item"><div class="leg-c" style="background:green"></div> &gt; 350m — Zone élargie</div>
                <br>
                <small>⚠️ Signaux &gt; 600m filtrés (antennes opérateurs)</small>
            </div>
        </div>
    </div>

<script>
    var carte = L.map('carte').setView([47.5105, 6.7978], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(carte);

    var iconRecepteur = L.divIcon({ html: '📡', iconSize: [30,30], className: '' });
    L.marker([47.5105, 6.7978], {icon: iconRecepteur})
        .addTo(carte)
        .bindPopup('<b>📡 Récepteur SDR</b><br>23 Rue Maurice Ravel, Montbéliard')
        .openPopup();

    var marqueurs = {};
    var cercles   = {};

    function distanceMetres(rssi) {
        if (rssi > -40) return 5;
        if (rssi > -50) return 10;
        if (rssi > -60) return 25;
        if (rssi > -70) return 50;
        if (rssi > -75) return 100;
        if (rssi > -80) return 200;
        if (rssi > -85) return 350;
        if (rssi > -90) return 500;
        return 800;
    }

    function couleur(rssi) {
        if (rssi > -60) return 'red';
        if (rssi > -75) return 'orange';
        if (rssi > -85) return 'yellow';
        return 'green';
    }

    function instruction(rssi, dist) {
        if (rssi > -60) return {
            classe: 'instr_urgence',
            texte:  '🚨 FOUILLER IMMÉDIATEMENT dans un rayon de ' + dist + 'm !'
        };
        if (rssi > -75) return {
            classe: 'instr_proche',
            texte:  '⚠️ Personne à ~' + dist + 'm. Avancez et scannez la zone.'
        };
        if (rssi > -85) return {
            classe: 'instr_moyen',
            texte:  '🔍 Zone de recherche ~' + dist + 'm. Déployez les équipes en cercle.'
        };
        return {
            classe: 'instr_loin',
            texte:  '📡 Signal à ~' + dist + 'm. Rapprochez le récepteur.'
        };
    }

    function iconeType(type) {
        if (type.includes('5G'))        return '5️⃣';
        if (type.includes('4G'))        return '4️⃣';
        if (type.includes('3G'))        return '3️⃣';
        if (type.includes('LoRa'))      return '📻';
        if (type.includes('WiFi'))      return '📶';
        if (type.includes('Bluetooth')) return '🔵';
        return '📡';
    }

    function actualiser() {
        fetch('/signaux')
        .then(r => r.json())
        .then(signaux => {
            var liste      = document.getElementById('liste');
            var resume     = document.getElementById('resume');
            var alerte     = document.getElementById('alerte_urgente');
            var aucun      = document.getElementById('aucun_signal');
            liste.innerHTML = '';
            var urgence    = false;
            var nbAffiche  = 0;
            var typesVus   = {};

            // Nettoie les anciens marqueurs
            Object.keys(cercles).forEach(function(id) {
                carte.removeLayer(cercles[id]);
                if (marqueurs[id]) carte.removeLayer(marqueurs[id]);
            });
            cercles   = {};
            marqueurs = {};

            signaux.slice().reverse().forEach(function(s) {
                var dist = distanceMetres(s.rssi);

                // ✅ Filtre — ignore les signaux trop lointains (antennes opérateurs)
                if (dist > 600) return;

                nbAffiche++;
                var col   = couleur(s.rssi);
                var instr = instruction(s.rssi, dist);
                var id    = s.type + '_' + s.freq.toFixed(0);

                typesVus[s.type] = (typesVus[s.type] || 0) + 1;
                if (s.rssi > -60) urgence = true;

                // Cercle zone de recherche
                cercles[id] = L.circle([47.5105, 6.7978], {
                    color:       col,
                    fillColor:   col,
                    fillOpacity: 0.2,
                    radius:      dist,
                    weight:      3,
                    dashArray:   dist > 200 ? '8,5' : null
                }).addTo(carte)
                .bindPopup(
                    '<b>🆘 ZONE DE RECHERCHE</b><br>' +
                    iconeType(s.type) + ' ' + s.type + '<br>' +
                    '📡 ' + s.freq.toFixed(3) + ' MHz<br>' +
                    '🔋 RSSI: ' + s.rssi + ' dB<br>' +
                    '📍 Distance: ~' + dist + 'm<br>' +
                    '🕐 ' + s.heure + '<br><br>' +
                    '<b style="color:orange">' + instr.texte + '</b>'
                );

                // Icône personne au bord du cercle
                var latP  = 47.5105 + (dist / 111320);
                var iconP = L.divIcon({
                    html: dist <= 25 ? '🆘' : (dist <= 100 ? '⚠️' : '👤'),
                    iconSize: [25,25],
                    className: ''
                });
                marqueurs[id] = L.marker([latP, 6.7978], {icon: iconP})
                    .addTo(carte)
                    .bindPopup(
                        '<b>Zone probable</b><br>' +
                        '~' + dist + 'm du récepteur<br>' +
                        s.freq.toFixed(3) + ' MHz'
                    );

                // Panneau latéral
                var div = document.createElement('div');
                div.className = 'signal ' + s.distance;
                div.innerHTML =
                    '<div class="type">' + iconeType(s.type) + ' ' + s.type + '</div>' +
                    '<div class="freq">' + s.freq.toFixed(3) + ' MHz</div>' +
                    '<div class="dist" style="color:' + col + '">📍 ~' + dist + ' mètres</div>' +
                    '🔋 RSSI: ' + s.rssi + ' dB | 📶 BW: ' + s.bw + ' kHz<br>' +
                    '🕐 ' + s.heure +
                    '<div class="instruction ' + instr.classe + '">' + instr.texte + '</div>';
                liste.appendChild(div);
            });

            // Résumé
            var resumeHtml = '<b>📊 ' + nbAffiche + ' signal(s) affiché(s)</b><br>';
            Object.keys(typesVus).forEach(function(t) {
                resumeHtml += iconeType(t) + ' ' + t + ' : ' + typesVus[t] + '<br>';
            });
            resume.innerHTML = resumeHtml;

            // Aucun signal proche
            aucun.style.display = nbAffiche === 0 ? 'block' : 'none';

            // Alerte urgente
            alerte.style.display = urgence ? 'block' : 'none';
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
            type_sig = parts[1].split(":")[1].strip()
            freq     = float(parts[2].split(":")[1].replace("MHz","").strip())
            rssi     = float(parts[3].split(":")[1].replace("dB","").strip())
            bw       = float(parts[4].split(":")[1].replace("kHz","").strip())
            distance = parts[5].split(":")[1].strip()
            signal = {
                "type":     type_sig,
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
    HTTPServer(("0.0.0.0", 8080), WebHandler).serve_forever()
