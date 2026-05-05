import serial
import time
import threading
import os

class GPSReader:
    def __init__(self, port='/dev/ttyUSB3', baudrate=115200):
        self.port     = port
        self.baudrate = baudrate
        self.lat      = 47.5072
        self.lon      = 6.7961
        self.fix      = False
        self.running  = True
        threading.Thread(target=self._lire, daemon=True).start()
        print("GPS Reader démarré...")

    def _convertir(self, val, direction):
        try:
            val = float(val)
            deg = int(val / 100)
            minutes = val - deg * 100
            result = deg + minutes / 60
            if direction in ['S', 'W']:
                result = -result
            return round(result, 6)
        except:
            return None

    def _lire(self):
        while self.running:
            try:
                # ✅ Si le module GPS n'est pas branché, attend sans erreur
                if not os.path.exists(self.port):
                    time.sleep(5)
                    continue

                s = serial.Serial(self.port, self.baudrate, timeout=3)
                while self.running:
                    s.write(b'AT+CGPSINFO\r\n')
                    time.sleep(3)
                    data = s.read(300).decode('utf-8', errors='ignore')

                    if '+CGPSINFO:' in data:
                        ligne = [l for l in data.split('\n') if '+CGPSINFO:' in l]
                        if ligne:
                            parts = ligne[0].replace('+CGPSINFO:', '').strip().split(',')
                            if len(parts) >= 4 and parts[0] and parts[2]:
                                lat = self._convertir(parts[0], parts[1])
                                lon = self._convertir(parts[2], parts[3])
                                if lat and lon:
                                    self.lat  = lat
                                    self.lon  = lon
                                    self.fix  = True
                                    print(f"GPS OK: {lat:.6f}, {lon:.6f}")
            except Exception as e:
                time.sleep(5)

    def get_position(self):
        return self.lat, self.lon, self.fix

    def stop(self):
        self.running = False
