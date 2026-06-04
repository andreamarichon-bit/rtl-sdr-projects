import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from rtlsdr import RtlSdr

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.center_freq = 100e6  # centro en 100 MHz
sdr.gain = 'auto'

NFFT = 1024
NUM_ROWS = 100  # cuántas filas de tiempo muestra el waterfall

# Matriz que acumula el espectro en el tiempo
waterfall_data = np.zeros((NUM_ROWS, NFFT))

fig, (ax_spec, ax_wf) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('Spectrum Sensing — 100 MHz ± 1.2 MHz', fontsize=12)

# Panel superior: espectro instantáneo
line, = ax_spec.plot(np.linspace(-1.2, 1.2, NFFT), 
                     np.zeros(NFFT), color='steelblue', linewidth=0.8)
ax_spec.set_xlim(-1.2, 1.2)
ax_spec.set_ylim(-40, 50)
ax_spec.set_xlabel('Frecuencia relativa (MHz)')
ax_spec.set_ylabel('Potencia (dB)')
ax_spec.set_title('Espectro instantáneo')
ax_spec.grid(True, alpha=0.3)

# Panel inferior: waterfall
img = ax_wf.imshow(waterfall_data, aspect='auto',
                   extent=[-1.2, 1.2, 0, NUM_ROWS],
                   vmin=-30, vmax=40,
                   cmap='inferno', origin='upper')
plt.colorbar(img, ax=ax_wf, label='Potencia (dB)')
ax_wf.set_xlabel('Frecuencia relativa (MHz)')
ax_wf.set_ylabel('Tiempo (frames)')
ax_wf.set_title('Waterfall — evolución temporal')

plt.tight_layout()

def update(frame):
    samples = sdr.read_samples(NFFT * 4)
    fft = np.fft.fftshift(np.fft.fft(samples, n=NFFT))
    psd = 10 * np.log10(np.abs(fft) ** 2 + 1e-12)

    # Actualizar espectro instantáneo
    line.set_ydata(psd)

    # Desplazar waterfall hacia abajo y agregar nueva fila arriba
    waterfall_data[1:] = waterfall_data[:-1]
    waterfall_data[0] = psd
    img.set_data(waterfall_data)

    return line, img

ani = animation.FuncAnimation(fig, update, interval=50,
                               blit=False, cache_frame_data=False)

plt.show()
sdr.close()