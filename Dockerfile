FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    tzdata \
    gnuradio \
    uhd-host \
    python3 \
    python3-pip \
    && apt clean

RUN ln -fs /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

RUN uhd_images_downloader
