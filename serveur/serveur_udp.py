import socket
import time

# Ce serveur reçoit de GNU Radio (port 5005)
# et relaie vers tous les clients (port 6000)

clients = []

def demarrer_serveur():
    # Socket qui reçoit de GNU Radio
    udp_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_in.bind(("127.0.0.1", 5005))

    # Socket qui envoie aux clients
    udp_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("Serveur UDP démarré")
    print("Reçoit GNU Radio sur port 5005")
    print("Envoie aux clients sur port 6000")
    print("-" * 50)

    while True:
        data, _ = udp_in.recvfrom(1024)
        message = data.decode()
        horodatage = time.strftime('%H:%M:%S')
        message_complet = f"[{horodatage}] {message}"

        print(f"REÇU  : {message_complet}")

        # Relaie vers le client
        udp_out.sendto(message_complet.encode(), ("127.0.0.1", 6000))
        print(f"RELAYÉ → port 6000")

if __name__ == "__main__":
    demarrer_serveur()
