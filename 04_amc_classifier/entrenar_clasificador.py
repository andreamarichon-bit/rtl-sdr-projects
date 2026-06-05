import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import joblib

# ─── Cargar dataset ───────────────────────────────────────────────────────────
fm    = np.load('dataset/fm.npy')
adsb  = np.load('dataset/adsb.npy')
noise = np.load('dataset/noise.npy')

# ─── Extraer features de IQ samples ──────────────────────────────────────────
def extract_features(samples):
    """
    Extrae features del dominio del tiempo y frecuencia.
    Cada fila de samples es una captura de 1024 IQ samples.
    """
    features = []
    for s in samples:
        # Magnitud y fase
        mag   = np.abs(s)
        phase = np.angle(s)
        
        # Features del dominio del tiempo
        mean_mag    = np.mean(mag)
        std_mag     = np.std(mag)
        kurtosis    = np.mean((mag - mean_mag)**4) / (std_mag**4 + 1e-10)
        skewness    = np.mean((mag - mean_mag)**3) / (std_mag**3 + 1e-10)
        
        # Variación de fase (clave para distinguir FM)
        phase_diff  = np.diff(np.unwrap(phase))
        mean_phase  = np.mean(np.abs(phase_diff))
        std_phase   = np.std(phase_diff)
        
        # Features espectrales
        fft     = np.fft.fftshift(np.abs(np.fft.fft(s)))
        psd     = fft ** 2
        psd_norm = psd / (np.sum(psd) + 1e-10)
        
        spectral_mean     = np.mean(psd_norm)
        spectral_std      = np.std(psd_norm)
        spectral_entropy  = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
        peak_to_mean      = np.max(psd) / (np.mean(psd) + 1e-10)
        
        # Ratio IQ
        i_std = np.std(s.real)
        q_std = np.std(s.imag)
        iq_ratio = i_std / (q_std + 1e-10)

        features.append([
            mean_mag, std_mag, kurtosis, skewness,
            mean_phase, std_phase,
            spectral_mean, spectral_std, spectral_entropy, peak_to_mean,
            iq_ratio
        ])
    return np.array(features)

print("Extrayendo features...")
X_fm    = extract_features(fm)
X_adsb  = extract_features(adsb)
X_noise = extract_features(noise)

# Labels: 0=FM, 1=ADS-B, 2=Ruido
X = np.vstack([X_fm, X_adsb, X_noise])
y = np.array([0]*500 + [1]*500 + [2]*500)

# ─── Entrenar clasificador ────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

print("Entrenando Random Forest...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# ─── Evaluar ──────────────────────────────────────────────────────────────────
y_pred = clf.predict(X_test)
labels = ['FM', 'ADS-B', 'Ruido']

print("\n=== Reporte de clasificación ===")
print(classification_report(y_test, y_pred, target_names=labels))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, cmap='Blues')
ax.set_xticks(range(3)); ax.set_xticklabels(labels)
ax.set_yticks(range(3)); ax.set_yticklabels(labels)
ax.set_xlabel('Predicción')
ax.set_ylabel('Real')
ax.set_title('Confusion Matrix — AMC Classifier')
plt.colorbar(im)
for i in range(3):
    for j in range(3):
        ax.text(j, i, str(cm[i,j]), ha='center', va='center',
                color='white' if cm[i,j] > cm.max()/2 else 'black',
                fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150)
plt.show()

# Feature importance
fig2, ax2 = plt.subplots(figsize=(8, 4))
feature_names = ['mean_mag','std_mag','kurtosis','skewness',
                 'mean_phase','std_phase','spec_mean','spec_std',
                 'spec_entropy','peak_to_mean','iq_ratio']
importances = clf.feature_importances_
idx = np.argsort(importances)[::-1]
ax2.bar(range(11), importances[idx], color='steelblue')
ax2.set_xticks(range(11))
ax2.set_xticklabels([feature_names[i] for i in idx], rotation=45, ha='right')
ax2.set_title('Feature Importance — Random Forest')
ax2.set_ylabel('Importancia relativa')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150)
plt.show()

# Guardar modelo
joblib.dump(clf, 'modelo_amc.pkl')
print("\nModelo guardado: modelo_amc.pkl")