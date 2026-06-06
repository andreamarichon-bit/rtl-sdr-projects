import numpy as np
from rtlsdr import RtlSdr
import time
import os

os.makedirs('dataset', exist_ok=True)

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
time.sleep(0.5)

SAMPLES_PER_CAPTURE = 1024
CAPTURES = 500

# Multiple FM frequencies and gains for variety
fm_configs = [
    (92.7e6, 40),
    (99.7e6, 40),
    (101.7e6, 40),
    (92.7e6, 20),  # same channel, low gain = weaker signal
    (99.7e6, 20),
]

print("=== Capturing FM ===")
all_fm = []
captures_per_config = CAPTURES // len(fm_configs)
for freq, gain in fm_configs:
    sdr.center_freq = freq
    sdr.gain = gain
    time.sleep(0.2)
    for i in range(captures_per_config):
        s = sdr.read_samples(SAMPLES_PER_CAPTURE)
        all_fm.append(s)
    print(f"  {freq/1e6:.1f} MHz gain={gain} — {captures_per_config} samples")

np.save('dataset/fm.npy', np.array(all_fm))
print(f"  Total FM: {len(all_fm)} samples\n")

print("=== Capturing ADS-B ===")
sdr.center_freq = 1090e6
sdr.gain = 49
adsb_samples = []
for i in range(CAPTURES):
    s = sdr.read_samples(SAMPLES_PER_CAPTURE)
    adsb_samples.append(s)
    if (i+1) % 100 == 0:
        print(f"  {i+1}/{CAPTURES}")
np.save('dataset/adsb.npy', np.array(adsb_samples))
print(f"  Total ADS-B: {len(adsb_samples)} samples\n")

# Noise at several empty frequencies
print("=== Capturing noise ===")
noise_configs = [
    (400e6, 0),
    (350e6, 0),
    (450e6, 0),
    (400e6, 10),  # higher gain = more dongle thermal noise
    (350e6, 10),
]
all_noise = []
captures_per_config = CAPTURES // len(noise_configs)
for freq, gain in noise_configs:
    sdr.center_freq = freq
    sdr.gain = gain
    time.sleep(0.2)
    for i in range(captures_per_config):
        s = sdr.read_samples(SAMPLES_PER_CAPTURE)
        all_noise.append(s)
    print(f"  {freq/1e6:.1f} MHz gain={gain} — {captures_per_config} samples")

np.save('dataset/noise.npy', np.array(all_noise))
print(f"  Total noise: {len(all_noise)} samples\n")

sdr.close()
print(f"Dataset complete: {len(all_fm)} FM + {len(adsb_samples)} ADS-B + {len(all_noise)} noise")