# RTL-SDR Projects
    
Built with Python and a low-cost RTL-SDR.


### 1. FM Spectrum Scanner
Sweeps the full FM broadcast band (88–108 MHz) by capturing IQ samples at 2 MHz steps.

<p align="center">
  <img src="images/fm_scan.png" alt="FM Scanner" width="85%"/>
</p>

---

### 2. Real-Time Spectrum Sensing with Waterfall
Continuously streams IQ data to render a live dual-panel display with instantaneous power spectrum on top and a time-frequency waterfall plot below.

<p align="center">
  <img src="images/waterfall.png" alt="Waterfall Display" width="85%"/>
</p>

---

### 3. ADS-B Visualizer
Captures Mode S ADS-B transmissions at 1090 MHz using dump1090 and generates dynamic KML files for real-time flight tracking in Google Earth.

<p align="center">
  <img src="images/adsb_visualizer.png" alt="ADS-B Visualizer" width="85%"/>
</p>

---

### 4. Automatic Modulation Classifier (AMC)
Employs a Random Forest classifier to distinguish between FM broadcasts, ADS-B signals, and noise directly from raw IQ captures.

**Feature Extraction** (per 1024-sample frame):
* **Time domain:** Mean magnitude, standard deviation, kurtosis, skewness.
* **Phase domain:** Mean and standard deviation of unwrapped phase derivative.
* **Frequency domain:** Spectral entropy, spectral standard deviation, peak-to-mean ratio.

**Results:** Achieved **99% accuracy** on test set (300 samples across 3 classes).

<p align="center">
  <img src="images/confusion_matrix.png" alt="Confusion Matrix" width="45%"/>
  <img src="images/feature_importance.png" alt="Feature Importance" width="45%"/>
</p>

---
Developed to build practical experience in Software Defined Radio (SDR), RF spectrum sensing, and machine-learning-based signal classification.


