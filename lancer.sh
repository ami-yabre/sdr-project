#!/bin/bash
echo "Préparation du système SDR..."

# Active le USRP
sudo bash -c 'echo -1 > /sys/module/usbcore/parameters/autosuspend'

# Recopie le bon bloc Python
cp ~/sdr-project/gnuradio/detecteur.py ~/sdr-project/test_gnu_epy_block_0.py
echo "Bloc Python restauré ✅"

# Corrige test_gnu.py - remplace usrp_source=None par le vrai USRP
sed -i 's/usrp_source=None/usrp_source=self.uhd_usrp_source_0/' ~/sdr-project/test_gnu.py
echo "USRP connecté dans test_gnu.py ✅"

# Efface le cache
rm -rf ~/sdr-project/__pycache__

# Lance GNU Radio
echo "Lancement GNU Radio..."
python3 ~/sdr-project/test_gnu.py
