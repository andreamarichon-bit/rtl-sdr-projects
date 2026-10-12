import socket
import math
import time
import os

# Ground station coordinates (Tijuana, Mexico)
STATION_LAT = 32.5149   
STATION_LON = -117.0382  
STATION_ALT_M = 150.0    
FREQ_MHZ = 1090.0        # Central frequency ADS-B

# Network configuration (dump1090 Backend)
HOST = '127.0.0.1'
PORT = 30003

# KML file for Google Earth visualization
KML_FILE = "live.link.kml"

# RF LINK BUDGET CALCULATOR
class RFLinkBudgetCalculator:
    def __init__(self, rx_lat, rx_lon, rx_alt_m):
        self.rx_lat = rx_lat
        self.rx_lon = rx_lon
        self.rx_alt_m = rx_alt_m

    def calculate_metrics(self, tx_lat, tx_lon, tx_alt_ft):
        """Calculates the slant range, elevation angle, and free space path loss (FSPL)."""
        tx_alt_m = tx_alt_ft * 0.3048  # ft a m

        # Harvesine formula for ground distance
        R = 6371000.0
        dlat = math.radians(tx_lat - self.rx_lat)
        dlon = math.radians(tx_lon - self.rx_lon)
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(self.rx_lat)) * math.cos(math.radians(tx_lat)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        ground_dist_m = R * c

        # Slant range
        alt_diff_m = tx_alt_m - self.rx_alt_m
        slant_range_m = math.sqrt(ground_dist_m**2 + alt_diff_m**2)
        slant_range_km = slant_range_m / 1000.0

        # Elevation angle in degrees
        elevation_deg = math.degrees(math.atan2(alt_diff_m, ground_dist_m)) if ground_dist_m > 0 else 90.0

        # FSPL
        fspl_db = 0.0
        if slant_range_km > 0:
            fspl_db = 20 * math.log10(slant_range_km) + 20 * math.log10(FREQ_MHZ) + 32.44

        return slant_range_km, elevation_deg, fspl_db


# KML EXPORTER
class KMLExporter:
    @staticmethod
    def update_kml(aircraft_db):
        """Generates a KML file with the 3D trajectories of the aircraft."""
        kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>ADS-B Real-Time Flight Tracking - Tijuana</name>
    <Style id="planeStyle">
      <IconStyle>
        <scale>1.2</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/airports.png</href></Icon>
      </IconStyle>
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
    </Style>
"""
        kml_footer = """  </Document>
</kml>"""

        placemarks = ""
        for icao, data in aircraft_db.items():
            if data['lat'] is not None and data['lon'] is not None and data['alt'] is not None:
                callsign = data['callsign'] or icao
                alt_m = data['alt'] * 0.3048
                
                placemarks += f"""
    <Placemark>
      <name>{callsign}</name>
      <description>
        ICAO: {icao}
        Altitud: {data['alt']} ft
        Velocidad: {data['speed'] or 'N/A'} kt
        Slant Range: {data['range_km']:.2f} km
        FSPL: {data['fspl_db']:.1f} dB
      </description>
      <styleUrl>#planeStyle</styleUrl>
      <Point>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>{data['lon']},{data['lat']},{alt_m}</coordinates>
      </Point>
    </Placemark>
"""
        try:
            with open(KML_FILE, 'w', encoding='utf-8') as f:
                f.write(kml_header + placemarks + kml_footer)
        except Exception:
            pass


# TELEMETRY ENGINE
def main():
    rf_calc = RFLinkBudgetCalculator(STATION_LAT, STATION_LON, STATION_ALT_M)
    
    # Ditionary for saving aircraft data
    aircraft_db = {}

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("=" * 80)
    print("      ADS-B REAL-TIME TELEMETRY & RF LINK BUDGET ENGINE (TIJUANA)")
    print("=" * 80)
    print(f"Local port dump1090 ({HOST}:{PORT})...")

    try:
        client.connect((HOST, PORT))
        print("Successful connection. Processing data stream...\n")
        
        # print table header
        print(f"{'ICAO':<8} | {'FLIGHT':<9} | {'ALT(FT)':<8} | {'SPD(KT)':<8} | {'RANGE(KM)':<10} | {'ELEV(°)':<8} | {'FSPL(dB)':<9} | {'POS(LAT,LON)'}")
        print("-" * 88)

        buffer = ""
        last_kml_update = time.time()

        while True:
            data = client.recv(2048).decode('utf-8', errors='ignore')
            buffer += data
            lines = buffer.split('\n')
            buffer = lines.pop()

            for line in lines:
                parts = line.split(',')
                # mesagge type MSG, ICAO, callsign, alt, speed, lat, lon
                if len(parts) > 10 and parts[0] == 'MSG':
                    icao = parts[4]
                    callsign = parts[10].strip()
                    alt_str = parts[11]
                    speed_str = parts[12]
                    lat_str = parts[14]
                    lon_str = parts[15]

                    # start tracking new aircraft if not already in the database
                    if icao not in aircraft_db:
                        aircraft_db[icao] = {
                            'callsign': None,
                            'alt': None,
                            'speed': None,
                            'lat': None,
                            'lon': None,
                            'range_km': 0.0,
                            'elev_deg': 0.0,
                            'fspl_db': 0.0,
                            'last_seen': time.time()
                        }

                    ac = aircraft_db[icao]
                    ac['last_seen'] = time.time()

                    if callsign:
                        ac['callsign'] = callsign
                    if alt_str:
                        ac['alt'] = int(alt_str)
                    if speed_str:
                        ac['speed'] = int(float(speed_str))
                    
                    # update position and calculate metrics if lat/lon are available
                    if lat_str and lon_str:
                        ac['lat'] = float(lat_str)
                        ac['lon'] = float(lon_str)

                        if ac['alt'] is not None:
                            r_km, elev, fspl = rf_calc.calculate_metrics(ac['lat'], ac['lon'], ac['alt'])
                            ac['range_km'] = r_km
                            ac['elev_deg'] = elev
                            ac['fspl_db'] = fspl

                            # print aircraft info
                            call_disp = ac['callsign'] or 'N/A'
                            spd_disp = ac['speed'] if ac['speed'] is not None else 'N/A'
                            print(f"{icao:<8} | {call_disp:<9} | {ac['alt']:<8} | {spd_disp:<8} | {r_km:<10.2f} | {elev:<8.1f} | {fspl:<9.1f} | {ac['lat']:.5f}, {ac['lon']:.5f}")

            # update KML file every 2 seconds
            if time.time() - last_kml_update > 2.0:
                KMLExporter.update_kml(aircraft_db)
                last_kml_update = time.time()

    except KeyboardInterrupt:
        print("\nTelemetry engine stopped by user.")
    except ConnectionRefusedError:
        print(f"\n[ERROR] Could not connect to dump1090 at {HOST}:{PORT}.")
        print("Make sure 'dump1090.exe --interactive --net' is running in another terminal.")
    finally:
        client.close()

if __name__ == "__main__":
    main()