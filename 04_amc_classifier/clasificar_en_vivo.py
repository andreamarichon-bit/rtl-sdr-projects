import numpy as np
from rtlsdr import RtlSdr
import joblib
import time

# Cargar modelo entrenado
clf = joblib.load('modelo_amc.pkl')
labels = ['FM', 'ADS-B', 'Ruido']

def extract_features(s):
    mag   = np.abs(s)
    phase = np.angle(s)
    
    mean_mag   = np.mean(mag)
    std_mag    = np.std(mag)
    kurtosis   = np.mean((mag - mean_mag)**4) / (std_mag**4 + 1e-10)
    skewness   = np.mean((mag - mean_mag)**3) / (std_mag**3 + 1e-10)
    
    phase_diff = np.diff(np.unwrap(phase))
    mean_phase = np.mean(np.abs(phase_diff))
    std_phase  = np.std(phase_diff)
    
    fft      = np.fft.fftshift(np.abs(np.fft.fft(s)))
    psd      = fft ** 2
    psd_norm = psd / (np.sum(psd) + 1e-10)
    
    spectral_mean    = np.mean(psd_norm)
    spectral_std     = np.std(psd_norm)
    spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
    peak_to_mean     = np.max(psd) / (np.mean(psd) + 1e-10)
    
    i_std    = np.std(s.real)
    q_std    = np.std(s.imag)
    iq_ratio = i_std / (q_std + 1e-10)

    return np.array([[mean_mag, std_mag, kurtosis, skewness,
                      mean_phase, std_phase,
                      spectral_mean, spectral_std, spectral_entropy,
                      peak_to_mean, iq_ratio]])

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.gain = 40
time.sleep(0.5)

# Frecuencias a monitorear
frecuencias = {
    'FM 92.7 MHz':  92.7e6,
    'ADS-B 1090 MHz': 1090e6,
    'Desconocida 400 MHz': 400e6,
    'Desconocida 433 MHz': 433e6,  # ISM band, controles remotos
}

print("=== Clasificador AMC en vivo ===\n")
print(f"{'Frecuencia':<25} {'Predicción':<10} {'Confianza'}")
print("-" * 50)

for nombre, freq in frecuencias.items():
    sdr.center_freq = freq
    time.sleep(0.1)
    
    all_preds = []
    all_proba = []
    for _ in range(10):
        samples = sdr.read_samples(1024)
        f = extract_features(samples)
        all_preds.append(clf.predict(f)[0])
        all_proba.append(clf.predict_proba(f)[0])
    
    # Votación por mayoría
    from collections import Counter
    voto = Counter(all_preds).most_common(1)[0][0]
    confianza = np.mean([p[voto] for p in all_proba]) * 100
    
    print(f"{nombre:<25} {labels[voto]:<10} {confianza:.1f}%")

sdr.close()
print("\nHecho.")