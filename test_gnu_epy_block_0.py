import numpy as np
from gnuradio import gr
import time
import socket
from collections import deque

class blk(gr.sync_block):
    def __init__(self, samp_rate=10e6, center_freq=868e6):
        gr.sync_block.__init__(
            self,
            name='Systeme Secours Montagne',
            in_sig=[(np.float32, 1024)],
            out_sig=None
        )
        self.samp_rate = samp_rate
        self.last_time = 0
        self.detected_freqs = deque(maxlen=100)
        self.last_reset = time.time()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_ip = "127.0.0.1"
        self.udp_ports = [5005, 5006]

        # ✅ Scan automatique de toutes les bandes
        self.bandes = [
            {"nom": "LoRa_868MHz",  "freq": 868e6 + 4.5e6},
            {"nom": "WiFi_BT",      "freq": 2400e6},
            {"nom": "3G_900MHz",    "freq": 900e6},
            {"nom": "4G_800MHz",    "freq": 800e6},
            {"nom": "3G_2100MHz",   "freq": 2100e6},
            {"nom": "4G_1800MHz",   "freq": 1800e6},
            {"nom": "5G_3500MHz",   "freq": 3500e6},
        ]
        self.bande_idx  = 0
        self.center_freq = self.bandes[0]["freq"]
        self.last_scan  = time.time()
        self.scan_duree = 10  # 10 secondes par bande
        print(f"INIT OK — Scan universel de {len(self.bandes)} bandes")
        print(f"Bande actuelle : {self.bandes[0]['nom']}")

    def identifier_signal(self, freq_hz, bw_hz, rssi):
        freq_mhz = freq_hz / 1e6

        # LoRa 868 MHz
        if 860 < freq_mhz < 872:
            if bw_hz < 150e3:
                return "LoRa_BW125kHz"
            elif bw_hz < 350e3:
                return "LoRa_BW250kHz"
            else:
                return "LoRa_BW500kHz"

        # WiFi et Bluetooth 2.4 GHz
        elif 2395 < freq_mhz < 2490:
            if rssi > -55:
                return "WiFi_2.4GHz"
            else:
                return "Bluetooth_2.4GHz"

        # 3G 900 MHz
        elif 876 < freq_mhz < 915:
            return "3G_900MHz"

        # 4G 800 MHz
        elif 790 < freq_mhz < 820:
            return "4G_800MHz"

        # 4G 1800 MHz
        elif 1805 < freq_mhz < 1880:
            return "4G_1800MHz"

        # 3G 2100 MHz
        elif 2090 < freq_mhz < 2180:
            return "3G_2100MHz"

        # 5G 3500 MHz
        elif 3400 < freq_mhz < 3600:
            return "5G_3500MHz"

        return "SIGNAL_INCONNU"

    def estimer_distance(self, rssi):
        if rssi > -60:
            return "TRES_PROCHE"
        elif rssi > -75:
            return "PROCHE"
        elif rssi > -90:
            return "MOYEN"
        else:
            return "LOIN"

    def is_new_signal(self, freq):
        if time.time() - self.last_reset > 60:
            self.detected_freqs.clear()
            self.last_reset = time.time()
        for f in self.detected_freqs:
            if abs(freq - f) < 50e3:
                return False
        self.detected_freqs.append(freq)
        return True

    def changer_bande(self):
        self.bande_idx = (self.bande_idx + 1) % len(self.bandes)
        self.center_freq = self.bandes[self.bande_idx]["freq"]
        print(f"--- Scan : {self.bandes[self.bande_idx]['nom']} ({self.center_freq/1e6:.0f} MHz) ---")

    def work(self, input_items, output_items):
        # ✅ Change de bande toutes les 10 secondes
        if time.time() - self.last_scan > self.scan_duree:
            self.changer_bande()
            self.last_scan = time.time()

        for vec in input_items[0]:
            vec_smooth = np.convolve(vec, np.ones(5)/5, mode='same')

            vec_center = vec_smooth.copy()
            vec_center[:50] = -999
            vec_center[-50:] = -999

            rssi = np.max(vec_center)
            idx  = np.argmax(vec_center)

            if rssi < -95:
                continue

            freq = self.center_freq + (idx - 512) * (self.samp_rate / 1024)

            threshold = rssi - 6.0
            left = idx
            right = idx
            while left > 0 and vec_smooth[left] > threshold:
                left -= 1
            while right < len(vec_smooth)-1 and vec_smooth[right] > threshold:
                right += 1
            bw = (right - left) * (self.samp_rate / 1024)

            if bw > 5000e3:
                continue

            if not self.is_new_signal(freq):
                continue

            now = time.time()
            if now - self.last_time < 0.3:
                continue
            self.last_time = now

            distance    = self.estimer_distance(rssi)
            signal_type = self.identifier_signal(freq, bw, rssi)

            message = (
                f"SIGNAL_DETECTE | "
                f"TYPE:{signal_type} | "
                f"FREQ:{freq/1e6:.3f}MHz | "
                f"RSSI:{rssi:.1f}dB | "
                f"BW:{bw/1e3:.0f}kHz | "
                f"DISTANCE:{distance}"
            )
            print(message)
            for port in self.udp_ports:
                self.sock.sendto(message.encode(), (self.udp_ip, port))

        return len(input_items[0])
