#!/bin/bash
echo "Préparation du système SDR..."

# Active le USRP
sudo bash -c 'echo -1 > /sys/module/usbcore/parameters/autosuspend'

# Ajoute usrp_source si pas déjà présent
if ! grep -q "usrp_source=self.uhd_usrp_source_0" ~/sdr-project/test_gnu.py; then
    sed -i 's/self.epy_block_0 = epy_block_0.blk(samp_rate=samp_rate, center_freq=868000000.0)/self.epy_block_0 = epy_block_0.blk(samp_rate=samp_rate, center_freq=868000000.0, usrp_source=self.uhd_usrp_source_0)/' ~/sdr-project/test_gnu.py
    echo "usrp_source ajouté ✅"
fi

# Efface le cache
rm -rf ~/sdr-project/__pycache__

# Lance GNU Radio
echo "Lancement GNU Radio..."
python3 ~/sdr-project/test_gnu.py
