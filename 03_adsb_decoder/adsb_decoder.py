import numpy as np
from rtlsdr import RtlSdr
import time

# Set up the SDR
try:
    sdr_temp = RtlSdr()
    sdr_temp.close()
    time.sleep(0.5)
except Exception:
    pass

sdr = RtlSdr()
time.sleep(0.3)

# Configure the SDR for ADS-B reception
sdr.direct_sampling = 0
time.sleep(0.2)

sdr.sample_rate = 2.0e6
sdr.center_freq = 1090e6
sdr.gain = 28.0  # Gain adjusted to avoid saturation, can be tuned based on environment
time.sleep(0.5)

# CRC 24 generator polynomial for ADS-B messages
CRC24_GENERATOR = 0xFFFA04

def crc24(bits):
    msg_bytes = []
    for i in range(0, len(bits) - 24, 8):
        byte = sum(bits[i+j] << (7-j) for j in range(8))
        msg_bytes.append(byte)
    
    crc = 0
    for byte in msg_bytes:
        crc ^= (byte << 16)
        for _ in range(8):
            if crc & 0x800000:
                crc = (crc << 1) ^ CRC24_GENERATOR
            else:
                crc <<= 1
            crc &= 0xFFFFFF
    return crc

def validate_crc(bits):
    if len(bits) < 112:
        return False
    computed = crc24(bits)
    transmitted = 0
    for i in range(88, 112):
        transmitted = (transmitted << 1) | bits[i]
    return computed == transmitted

def demodulate_am(samples):
    return np.abs(samples)

def detect_preamble(signal, threshold):
    preamble_positions = []
    min_gap = 240
    last = -min_gap
    for i in range(len(signal) - 240):
        if i - last < min_gap:
            continue
        p = signal[i:i+20]
        if (p[0] > threshold and p[4] > threshold and
            p[14] > threshold and p[18] > threshold and
            p[2] < threshold and p[6] < threshold and
            p[10] < threshold and p[12] < threshold):
            preamble_positions.append(i)
            last = i
    return preamble_positions

def extract_bits(signal, start):
    bits = []
    msg_start = start + 16
    for i in range(112):
        s0 = signal[msg_start + i*2]
        s1 = signal[msg_start + i*2 + 1]
        bits.append(1 if s0 > s1 else 0)
    return bits

def bits_to_hex(bits):
    hex_str = ''
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            val = sum(b << (7-j) for j, b in enumerate(byte))
            hex_str += f'{val:02X}'
    return hex_str

def decode_message(bits):
    if len(bits) < 112:
        return None

    if not validate_crc(bits):
        return None

    df = sum(bits[i] << (4-i) for i in range(5))
    if df not in [17, 18]:
        return None

    icao = bits_to_hex(bits[8:32])
    tc = sum(bits[32+i] << (4-i) for i in range(5))
    result = {'df': df, 'icao': icao, 'tc': tc}

    if 1 <= tc <= 4:
        charset = '@ABCDEFGHIJKLMNOPQRSTUVWXYZ                     0123456789      '
        callsign = ''
        for i in range(8):
            idx = sum(bits[40 + i*6 + j] << (5-j) for j in range(6))
            callsign += charset[idx] if idx < len(charset) else '?'
        result['callsign'] = callsign.strip()

    elif 9 <= tc <= 18:
        alt_bits = bits[40:52]
        q_bit = alt_bits[8]
        if q_bit == 1:
            n = sum(alt_bits[i] << (10-i) for i in range(11) if i != 6 and i != 8)
            result['altitude_ft'] = n * 25 - 1000

    return result

# Capture and decode ADS-B messages
print("Capturing ADS-B signals at 1090 MHz...")
print("CRC validation active (0xFFFA04)\n")

all_messages = {}
CAPTURES = 999999

try:
    for cap in range(CAPTURES):
        try:
            # Buffer 32k samples to ensure we capture complete messages
            samples = sdr.read_samples(32 * 1024)
        except Exception:
            time.sleep(0.05)
            continue

        signal = demodulate_am(samples)
        threshold = np.mean(signal) * 2.2

        for pos in detect_preamble(signal, threshold):
            if pos + 16 + 224 > len(signal):
                continue
            bits = extract_bits(signal, pos)
            msg = decode_message(bits)
            if msg:
                icao = msg['icao']
                if icao not in all_messages:
                    all_messages[icao] = msg
                    print(f"DF:{msg['df']} | ICAO:{icao} | TC:{msg['tc']}", end='')
                    if 'callsign' in msg:
                        print(f" | Flight: {msg['callsign']}", end='')
                    if 'altitude_ft' in msg:
                        print(f" | Altitude: {msg['altitude_ft']} ft", end='')
                    print()

        if (cap+1) % 25 == 0:
            print(f"  [{cap+1}/{CAPTURES} processed blocks — {len(all_messages)} unique aircraft detected]")

except KeyboardInterrupt:
    print("\nCapture interrupted by user.")
finally:
    sdr.close()
    print("SDR released correctly.")