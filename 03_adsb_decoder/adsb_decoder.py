import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import struct
import time

# SDR configuration 
# Automatic reset
try:
    sdr = RtlSdr()
    sdr.close()
    time.sleep(1)
except:
    pass

time.sleep(1)
sdr = RtlSdr()
sdr.sample_rate = 2.0e6
sdr.center_freq = 1090e6
sdr.gain = 40
time.sleep(0.5)

def demodulate_am(samples):
    """Converts IQ samples to magnitude (AM envelope)."""
    return np.abs(samples)

def detect_preamble(signal, threshold):
    """
    Detects the ADS-B preamble: pulses at positions 0,2,7,9 microseconds.
    At 2 MHz each sample = 0.5 us → positions 0,4,14,18 samples.
    """
    preamble_positions = []
    min_gap = 240  # minimum gap between messages (~120 us)
    last = -min_gap

    for i in range(len(signal) - 240):
        if i - last < min_gap:
            continue
        # Verfy preamble pattern
        p = signal[i:i+20]
        if (p[0] > threshold and p[4] > threshold and
            p[14] > threshold and p[18] > threshold and
            p[2] < threshold and p[6] < threshold and
            p[10] < threshold and p[12] < threshold):
            preamble_positions.append(i)
            last = i

    return preamble_positions

def extract_bits(signal, start):
    """
    Extracts 112 bits using Manchester decoding.
    Each bit occupies 2 samples at 2 MHz (1 us per half-bit).
    """
    bits = []
    # The message starts 16 samples after the preamble
    msg_start = start + 16
    for i in range(112):
        s0 = signal[msg_start + i*2]
        s1 = signal[msg_start + i*2 + 1]
        if s0 > s1:
            bits.append(1)
        elif s1 > s0:
            bits.append(0)
        else:
            bits.append(0)
    return bits

def bits_to_hex(bits):
    """Converts a list of bits to a hexadecimal string."""
    hex_str = ''
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            val = sum(b << (7-j) for j, b in enumerate(byte))
            hex_str += f'{val:02X}'
    return hex_str

def decode_message(bits):
    """Decodes basic fields of an ADS-B message."""
    if len(bits) < 112:
        return None

    df = sum(bits[i] << (4-i) for i in range(5))  # Downlink Format
    
    if df not in [17, 18]:  # Solo ADS-B extended squitter
        return None

    # ICAO address (bits 9-32)
    icao = bits_to_hex(bits[8:32])

    # Type code (bits 33-37)
    tc = sum(bits[32+i] << (4-i) for i in range(5))

    result = {'df': df, 'icao': icao, 'tc': tc}

    # Identification of the flight (TC 1-4)
    if 1 <= tc <= 4:
        charset = '@ABCDEFGHIJKLMNOPQRSTUVWXYZ                 0123456789      '
        callsign = ''
        for i in range(8):
            idx = sum(bits[40 + i*6 + j] << (5-j) for j in range(6))
            callsign += charset[idx] if idx < len(charset) else '?'
        result['callsign'] = callsign.strip()

    # Altitude (TC 9-18)
    elif 9 <= tc <= 18:
        alt_bits = bits[40:52]
        m_bit = alt_bits[6]
        q_bit = alt_bits[8]
        if q_bit == 1:
            n = (sum(alt_bits[i] << (10-i) for i in range(11) if i != 6 and i != 8))
            altitude = n * 25 - 1000
            result['altitude_ft'] = altitude

    return result

# Capture and Processing
print("Capturing ADS-B signal at 1090 MHz...")

all_messages = {}
CAPTURAS = 999999

for cap in range(CAPTURAS):
    samples = sdr.read_samples(256 * 1024)
    signal  = demodulate_am(samples)
    threshold = np.mean(signal) * 1.8

    positions = detect_preamble(signal, threshold)

    for pos in positions:
        if pos + 16 + 224 > len(signal):
            continue
        bits = extract_bits(signal, pos)
        msg  = decode_message(bits)
        if msg:
            icao = msg['icao']
            if icao not in all_messages:
                all_messages[icao] = msg
                print(f"  DF:{msg['df']} | ICAO:{icao} | TC:{msg['tc']}", end='')
                if 'callsign' in msg:
                    print(f" | Flight: {msg['callsign']}", end='')
                if 'altitude_ft' in msg:
                    print(f" | Altitude: {msg['altitude_ft']} ft", end='')
                print()

    if (cap+1) % 5 == 0:
        print(f"  [{cap+1}/{CAPTURAS} blocks processed — {len(all_messages)} unique aircrafts]")

sdr.close()

# Final Report
print(f"\n{'='*50}")
print(f"AIRCRAFT DETECTED: {len(all_messages)}")
print(f"{'='*50}")
for icao, msg in all_messages.items():
    print(f"  ICAO: {icao}  TC:{msg['tc']}", end='')
    if 'callsign' in msg:
        print(f"  Flight: {msg['callsign']}", end='')
    if 'altitude_ft' in msg:
        print(f"  Altitude: {msg['altitude_ft']} ft", end='')
    print()