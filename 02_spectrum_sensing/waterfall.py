import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from rtlsdr import RtlSdr

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.center_freq = 100e6  # at 100 MHz
sdr.gain = 'auto'

NFFT = 1024
NUM_ROWS = 100  # number of rows in the waterfall (time history)

# Matrix that accumulates the spectrum over time for the waterfall display
waterfall_data = np.zeros((NUM_ROWS, NFFT))

fig, (ax_spec, ax_wf) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('Spectrum Sensing — 100 MHz ± 1.2 MHz', fontsize=12)

# Top panel: instantaneous spectrum
line, = ax_spec.plot(np.linspace(-1.2, 1.2, NFFT), 
                     np.zeros(NFFT), color='steelblue', linewidth=0.8)
ax_spec.set_xlim(-1.2, 1.2)
ax_spec.set_ylim(-40, 50)
ax_spec.set_xlabel('Relative Frequency (MHz)')
ax_spec.set_ylabel('Power (dB)')
ax_spec.set_title('Instantaneous Spectrum')
ax_spec.grid(True, alpha=0.3)

# Bottom panel: waterfall
img = ax_wf.imshow(waterfall_data, aspect='auto',
                   extent=[-1.2, 1.2, 0, NUM_ROWS],
                   vmin=-30, vmax=40,
                   cmap='inferno', origin='upper')
plt.colorbar(img, ax=ax_wf, label='Power (dB)')
ax_wf.set_xlabel('Relative Frequency (MHz)')
ax_wf.set_ylabel('Time (frames)')
ax_wf.set_title('Waterfall — temporal evolution of the spectrum')

plt.tight_layout()

def update(frame):
    samples = sdr.read_samples(NFFT * 4)
    fft = np.fft.fftshift(np.fft.fft(samples, n=NFFT))
    psd = 10 * np.log10(np.abs(fft) ** 2 + 1e-12)

    # Update spectrum line
    line.set_ydata(psd)

    # Shift waterfall down and add new row at the top
    waterfall_data[1:] = waterfall_data[:-1]
    waterfall_data[0] = psd
    img.set_data(waterfall_data)

    return line, img

ani = animation.FuncAnimation(fig, update, interval=50,
                               blit=False, cache_frame_data=False)

plt.show()
sdr.close()