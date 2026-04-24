import socket
import time

def demarrer_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 6000))

    print("CLIENT UDP - Collecte des signaux")
    print("En attente de données du serveur...")
    print("=" * 60)

    compteur = 0
    while True:
        data, _ = sock.recvfrom(1024)
        message = data.decode()
        compteur += 1
        print(f"[Signal #{compteur}] {message}")

if __name__ == "__main__":
    demarrer_client()
