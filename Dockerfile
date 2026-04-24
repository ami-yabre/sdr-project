FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances
RUN apt update && apt install -y \
    tzdata \
    gnuradio \
    uhd-host \
    python3 \
    python3-pip \
    python3-numpy \
    && apt clean

# Timezone
RUN ln -fs /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Téléchargement des images UHD pour USRP
RUN uhd_images_downloader

# Copie du code dans le conteneur
WORKDIR /app
COPY gnuradio/ ./gnuradio/
COPY serveur/ ./serveur/
COPY client/ ./client/

# Port UDP exposé
EXPOSE 5005/udp
EXPOSE 6000/udp

# Lancement du serveur par défaut
CMD ["python3", "serveur/serveur_udp.py"]
