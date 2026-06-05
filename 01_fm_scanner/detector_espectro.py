import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.gain = 'auto'

freq_start = 88e6
freq_end   = 108e6
step       = 2e6

freqs_mhz = []
powers_db  = []

print("Escaneando espectro FM...")

freq = freq_start
while freq <= freq_end:
    sdr.center_freq = freq
    samples = sdr.read_samples(128 * 1024)
    fft = np.fft.fftshift(np.fft.fft(samples, n=2048))
    psd = 10 * np.log10(np.abs(fft) ** 2 + 1e-12)
    bin_freqs = freq + np.linspace(-sdr.sample_rate/2,
                                    sdr.sample_rate/2,
                                    len(psd))
    freqs_mhz.extend(bin_freqs / 1e6)
    powers_db.extend(psd)
    print(f"  {freq/1e6:.1f} MHz — pico: {max(psd):.1f} dB")
    freq += step

sdr.close()

freqs_mhz = np.array(freqs_mhz)
powers_db  = np.array(powers_db)
idx = np.argsort(freqs_mhz)
freqs_mhz = freqs_mhz[idx]
powers_db  = powers_db[idx]

# Threshold más alto para filtrar ruido
noise_floor = np.percentile(powers_db, 20)
threshold   = noise_floor + 25  # subimos de 15 a 25 dB

# Detectar picos con separación mínima de 0.15 MHz entre estaciones
peaks = []
i = 1
while i < len(powers_db) - 1:
    if (powers_db[i] > threshold and
        powers_db[i] > powers_db[i-1] and
        powers_db[i] > powers_db[i+1]):
        # Evitar duplicados cercanos
        if not peaks or abs(freqs_mhz[i] - peaks[-1][0]) > 0.15:
            peaks.append((freqs_mhz[i], powers_db[i]))
    i += 1

# Grafica limpia
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(freqs_mhz, powers_db, linewidth=0.4, color='steelblue')
ax.axhline(threshold, color='red', linestyle='--',
           linewidth=1, label=f'Threshold ({threshold:.1f} dB)')

for f, p in peaks:
    ax.annotate(f'{f:.1f}', xy=(f, p),
                xytext=(0, 6), textcoords='offset points',
                fontsize=8, ha='center', color='darkred',
                arrowprops=dict(arrowstyle='-', color='red', lw=0.5))

ax.set_xlabel('Frecuencia (MHz)')
ax.set_ylabel('Potencia (dB)')
ax.set_title('Scanner FM — 88 a 108 MHz')
ax.legend(loc='upper right')
ax.set_xlim(88, 108)
plt.tight_layout()
plt.savefig('fm_scan.png', dpi=150)
plt.show()

print(f"\nEstaciones detectadas: {len(peaks)}")
for f, p in sorted(peaks):
    print(f"  {f:.2f} MHz  —  {p:.1f} dB")