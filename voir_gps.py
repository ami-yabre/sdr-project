import serial
import time

# Port USB3 comme testé précédemment
port = '/dev/ttyUSB3'
ser = serial.Serial(port, 115200, timeout=1)

print(f"--- AFFICHAGE GPS EN DIRECT ---")
print("Appuyez sur Ctrl+C pour arrêter\n")

try:
    while True:
        ser.reset_input_buffer()
        ser.write(b'AT+CGPSINFO\r\n')
        
        # On lit la réponse du module
        data = ser.read(150).decode('utf-8', errors='ignore')
        
        if "+CGPSINFO:" in data:
            # On nettoie la réponse pour ne garder que la ligne utile
            ligne = [l for l in data.split('\n') if '+CGPSINFO:' in l]
            if ligne:
                contenu = ligne[0].replace("+CGPSINFO: ", "").strip()
                if contenu == ",,,,,,,,":
                    print("Signal perdu... (recherche en cours)", end="\r")
                else:
                    print(f"📍 Position : {contenu}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nArrêt de l'affichage.")
finally:
    ser.close()
