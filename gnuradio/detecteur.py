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
        self.center_freq = center_freq + 4.5e6
        self.last_time = 0
        self.detected_freqs = deque(maxlen=100)
        self.last_reset = time.time()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5005
        print(f"INIT OK | center_freq reel={self.center_freq/1e6}MHz")

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
        if time.time() - self.last_reset > 30:
            self.detected_freqs.clear()
            self.last_reset = time.time()
        for f in self.detected_freqs:
            if abs(freq - f) < 50e3:
                return False
        self.detected_freqs.append(freq)
        return True

    def work(self, input_items, output_items):
        for vec in input_items[0]:
            vec_smooth = np.convolve(vec, np.ones(5)/5, mode='same')

            vec_center = vec_smooth.copy()
            vec_center[:50] = -999
            vec_center[-50:] = -999

            rssi = np.max(vec_center)
            idx  = np.argmax(vec_center)

            # ✅ Filtre bruit de fond
            if rssi < -87:
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

            # ✅ Filtre BW — rejette signaux trop larges
            if bw > 2000e3:
                continue

            if not self.is_new_signal(freq):
                continue

            now = time.time()
            if now - self.last_time < 0.1:
                continue
            self.last_time = now

            distance = self.estimer_distance(rssi)

            message = (
                f"SIGNAL_DETECTE | "
                f"FREQ:{freq/1e6:.3f}MHz | "
                f"RSSI:{rssi:.1f}dB | "
                f"BW:{bw/1e3:.0f}kHz | "
                f"DISTANCE:{distance}"
            )
            print(message)
            self.sock.sendto(message.encode(), (self.udp_ip, self.udp_port))

        return len(input_items[0])
