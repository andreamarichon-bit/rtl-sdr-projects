# RTL-SDR Projects

Signal processing projects using a low-cost RTL-SDR dongle and Python.
<<<<<<< HEAD
<<<<<<< HEAD
=======

## Projects
---
### 1. FM Spectrum Scanner
Sweeps the full FM band (88–108 MHz) by capturing IQ samples at 2 MHz steps, computing the power spectral density via FFT, and automatically detecting active stations above a dynamic threshold.
![FM Scanner](images/fm_scan.png)

---

### 2. Real-Time Spectrum Sensing + Waterfall
<<<<<<< HEAD
<<<<<<< HEAD
Continuously captures IQ samples and renders a live dual-panel display: instantaneous spectrum on top, time-frequency waterfall below.
=======
Continuously captures IQ samples and renders a live dual-panel display: instantaneous spectrum on top, time-frequency waterfall below. Each row of the waterfall is one FFT frame — persistent signals appear as vertical bands.
>>>>>>> 37b68f2 (Refactor README by removing key concepts sections)
=======
Continuously captures IQ samples and renders a live dual-panel display: instantaneous spectrum on top, time-frequency waterfall below.
>>>>>>> 94cdb42 (previous adsb modified to adsb visualizer and kml link for google earth)
![Waterfall](images/waterfall.png)

---

<<<<<<< HEAD
<<<<<<< HEAD
### 3. ADS-B visualizer
Receives Mode S ADS-B transmissions at 1090 MHz using dump1090 for processing signals and Google Earth for live visualization using a KML file.
![ADS-B Visualizer](images/adsb_visualizer.png)
=======
### 3. ADS-B Decoder from Scratch
Receives Mode S ADS-B transmissions at 1090 MHz without any external decoding library. The pipeline:
1. Demodulate IQ samples to AM envelope
2. Detect the ADS-B preamble pattern (pulses at 0, 2, 7, 9 µs)
3. Extract 112 bits via Manchester decoding
4. Parse Downlink Format, ICAO address, altitude, and callsign fields

Detected **71 unique aircraft** in a single session over Tijuana/San Diego airspace.
![ADS-B Terminal](images/adsb_terminal.png)
>>>>>>> 37b68f2 (Refactor README by removing key concepts sections)
=======
### 3. ADS-B visualizer
Receives Mode S ADS-B transmissions at 1090 MHz using dump1090 for processing signals and Google Earth for live visualization using a KML file.
![ADS-B Visualizer](images/adsb_visualizer.png)
>>>>>>> 94cdb42 (previous adsb modified to adsb visualizer and kml link for google earth)

---

### 4. Automatic Modulation Classifier (AMC)
<<<<<<< HEAD
<<<<<<< HEAD
Trains a Random Forest classifier to distinguish FM broadcast, ADS-B, and noise from raw IQ samples.
=======
Trains a Random Forest classifier to distinguish FM broadcast, ADS-B, and noise from raw IQ samples. No labels at inference time.
>>>>>>> 37b68f2 (Refactor README by removing key concepts sections)
=======
Trains a Random Forest classifier to distinguish FM broadcast, ADS-B, and noise from raw IQ samples.
>>>>>>> 94cdb42 (previous adsb modified to adsb visualizer and kml link for google earth)
**Feature extraction** (per 1024-sample capture):
- Time domain: mean magnitude, std, kurtosis, skewness
- Phase domain: mean and std of unwrapped phase derivative
- Frequency domain: spectral entropy, spectral std, peak-to-mean ratio
**Results:** 99% accuracy on held-out test set (300 samples, 3 classes)

![Confusion Matrix](images/confusion_matrix.png)
![Feature Importance](images/feature_importance.png)

---

<<<<<<< HEAD
<<<<<<< HEAD
These projects were built to develop hands-on experience with SDR and wireless signal processing.
=======
## Setup

```bash
# Create environment with Python 3.11
uv venv sdr-env --python 3.11
source sdr-env/bin/activate  # or: sdr-env\Scripts\Activate.ps1 on Windows

# Install dependencies
uv pip install pyrtlsdr numpy scipy matplotlib scikit-learn joblib
```

Install WinUSB driver via [Zadig](https://zadig.akeo.ie) (Windows only).

---

## Background

These projects were built to develop hands-on experience with SDR and wireless signal processing, with focus on spectrum sensing and real-time signal classification.
>>>>>>> 37b68f2 (Refactor README by removing key concepts sections)
=======
These projects were built to develop hands-on experience with SDR and wireless signal processing.
>>>>>>> 94cdb42 (previous adsb modified to adsb visualizer and kml link for google earth)
