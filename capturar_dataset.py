import numpy as np
from rtlsdr import RtlSdr
import time
import os

os.makedirs('dataset', exist_ok=True)

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
time.sleep(0.5)

MUESTRAS_POR_CAPTURA = 1024
CAPTURAS = 500  # subimos de 200 a 500

# Varias frecuencias FM y gains para más variedad
fm_configs = [
    (92.7e6, 40),
    (99.7e6, 40),
    (101.7e6, 40),
    (92.7e6, 20),  # mismo canal, gain bajo = señal más débil
    (99.7e6, 20),
]

print("=== Capturando FM ===")
all_fm = []
capturas_por_config = CAPTURAS // len(fm_configs)
for freq, gain in fm_configs:
    sdr.center_freq = freq
    sdr.gain = gain
    time.sleep(0.2)
    for i in range(capturas_por_config):
        s = sdr.read_samples(MUESTRAS_POR_CAPTURA)
        all_fm.append(s)
    print(f"  {freq/1e6:.1f} MHz gain={gain} — {capturas_por_config} muestras")

np.save('dataset/fm.npy', np.array(all_fm))
print(f"  Total FM: {len(all_fm)} muestras\n")

# ADS-B con más capturas
print("=== Capturando ADS-B ===")
sdr.center_freq = 1090e6
sdr.gain = 49
adsb_samples = []
for i in range(CAPTURAS):
    s = sdr.read_samples(MUESTRAS_POR_CAPTURA)
    adsb_samples.append(s)
    if (i+1) % 100 == 0:
        print(f"  {i+1}/{CAPTURAS}")
np.save('dataset/adsb.npy', np.array(adsb_samples))
print(f"  Total ADS-B: {len(adsb_samples)} muestras\n")

# Ruido en varias frecuencias vacías
print("=== Capturando ruido ===")
noise_configs = [
    (400e6, 0),
    (350e6, 0),
    (450e6, 0),
    (400e6, 10),  # gain más alto = más ruido del propio dongle
    (350e6, 10),
]
all_noise = []
capturas_por_config = CAPTURAS // len(noise_configs)
for freq, gain in noise_configs:
    sdr.center_freq = freq
    sdr.gain = gain
    time.sleep(0.2)
    for i in range(capturas_por_config):
        s = sdr.read_samples(MUESTRAS_POR_CAPTURA)
        all_noise.append(s)
    print(f"  {freq/1e6:.1f} MHz gain={gain} — {capturas_por_config} muestras")

np.save('dataset/noise.npy', np.array(all_noise))
print(f"  Total ruido: {len(all_noise)} muestras\n")

sdr.close()
print(f"Dataset completo: {len(all_fm)} FM + {len(adsb_samples)} ADS-B + {len(all_noise)} ruido")