import serial
import time

# On teste USB2 ou USB3 (change si besoin)
port = '/dev/ttyUSB3'
ser = serial.Serial(port, 115200, timeout=1)

def send_at(command):
    ser.write((command + '\r\n').encode())
    time.sleep(1)
    return ser.read_all().decode('utf-8', errors='ignore')

print(f"--- DIAGNOSTIC MATÉRIEL GPS (Port: {port}) ---")

# 1. On réinitialise proprement le module
print("1. Réinitialisation du module (Cold Start)...")
send_at('AT+CGPS=0')
time.sleep(1)
send_at('AT+CGPSCOLD')
time.sleep(1)
send_at('AT+CGPS=1')
print("✅ Module redémarré.")

try:
    while True:
        # 2. On demande les infos détaillées (GNSS)
        # Cette commande montre les satellites même SANS position fixée
        print("\n--- Analyse du ciel ---")
        response = send_at('AT+CGNSSINFO')
        
        if "+CGNSSINFO:" in response:
            print(response.strip())
            # On vérifie si on voit des satellites (chiffres après les premières virgules)
            if ",,,," in response:
                print("❌ AUCUN SATELLITE EN VUE. Vérifiez le branchement de l'antenne sur le port GNSS.")
            else:
                print("📡 SATELLITES DÉTECTÉS ! Attente du calcul de précision...")
        
        # 3. On vérifie quand même la position finale
        pos = send_at('AT+CGPSINFO')
        if ",,,,,,,," not in pos:
            print("🎯 POSITION FIXÉE !")
            print(pos.strip())
            break
        
        time.sleep(3)

except KeyboardInterrupt:
    print("\nArrêt du diagnostic.")
finally:
    ser.close()
