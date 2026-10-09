import socket
import math
import time
import os

# ─── CONFIGURACIÓN DE LA ESTACIÓN TERRENA (TIJUANA) ─────────────────────────
# Ajusta tus coordenadas exactas si deseas mayor precisión geodésica
STATION_LAT = 32.5149    # Latitud de tu ubicación
STATION_LON = -117.0382  # Longitud de tu ubicación
STATION_ALT_M = 150.0    # Altitud sobre el nivel del mar en metros
FREQ_MHZ = 1090.0        # Frecuencia central ADS-B

# Configuración de red (dump1090 Backend)
HOST = '127.0.0.1'
PORT = 30003

# Archivo de salida KML para Google Earth Pro
KML_FILE = "adsb_live_traffic.kml"

# ─── CÁLCULOS GEODÉSICOS Y MARGEN DE ENLACE RF ──────────────────────────────
class RFLinkBudgetCalculator:
    def __init__(self, rx_lat, rx_lon, rx_alt_m):
        self.rx_lat = rx_lat
        self.rx_lon = rx_lon
        self.rx_alt_m = rx_alt_m

    def calculate_metrics(self, tx_lat, tx_lon, tx_alt_ft):
        """
        Calcula la distancia directa por línea de vista (Slant Range), 
        el ángulo de elevación y las pérdidas por trayectoria en espacio libre (FSPL).
        """
        tx_alt_m = tx_alt_ft * 0.3048  # Conversión de ft a m
        
        # Fórmula de Haversine para distancia sobre el elipsoide terrestre
        R = 6371000.0
        dlat = math.radians(tx_lat - self.rx_lat)
        dlon = math.radians(tx_lon - self.rx_lon)
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(self.rx_lat)) * math.cos(math.radians(tx_lat)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        ground_dist_m = R * c

        # Distancia en 3D (Slant Range)
        alt_diff_m = tx_alt_m - self.rx_alt_m
        slant_range_m = math.sqrt(ground_dist_m**2 + alt_diff_m**2)
        slant_range_km = slant_range_m / 1000.0

        # Ámulo de elevación
        elevation_deg = math.degrees(math.atan2(alt_diff_m, ground_dist_m)) if ground_dist_m > 0 else 90.0

        # Pérdidas en espacio libre (Free Space Path Loss)
        fspl_db = 0.0
        if slant_range_km > 0:
            fspl_db = 20 * math.log10(slant_range_km) + 20 * math.log10(FREQ_MHZ) + 32.44

        return slant_range_km, elevation_deg, fspl_db


# ─── EXPORTADOR DE TRAYECTORIAS KML ──────────────────────────────────────────
class KMLExporter:
    @staticmethod
    def update_kml(aircraft_db):
        """Genera dinámicamente un archivo KML con las trayectorias 3D de los aviones."""
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


# ─── ENGINE PRINCIPAL DE TELEMETRÍA ──────────────────────────────────────────
def main():
    rf_calc = RFLinkBudgetCalculator(STATION_LAT, STATION_LON, STATION_ALT_M)
    
    # Base de datos en memoria para mantener el estado de cada aeronave
    aircraft_db = {}

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("=" * 80)
    print("      ADS-B REAL-TIME TELEMETRY & RF LINK BUDGET ENGINE (TIJUANA)")
    print("=" * 80)
    print(f"Conectando al servidor local dump1090 ({HOST}:{PORT})...")

    try:
        client.connect((HOST, PORT))
        print("Conexión establecida con éxito. Procesando flujo de datos...\n")
        
        # Encabezado de la consola
        print(f"{'ICAO':<8} | {'FLIGHT':<9} | {'ALT(FT)':<8} | {'SPD(KT)':<8} | {'RANGE(KM)':<10} | {'ELEV(°)':<8} | {'FSPL(dB)':<9} | {'POSICIÓN'}")
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
                # Filtrar mensajes de formato SBS-1 (MSG)
                if len(parts) > 10 and parts[0] == 'MSG':
                    icao = parts[4]
                    callsign = parts[10].strip()
                    alt_str = parts[11]
                    speed_str = parts[12]
                    lat_str = parts[14]
                    lon_str = parts[15]

                    # Inicializar registro si es un ICAO nuevo
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
                    
                    # Actualizar telemetría geográfica y cálculos RF
                    if lat_str and lon_str:
                        ac['lat'] = float(lat_str)
                        ac['lon'] = float(lon_str)

                        if ac['alt'] is not None:
                            r_km, elev, fspl = rf_calc.calculate_metrics(ac['lat'], ac['lon'], ac['alt'])
                            ac['range_km'] = r_km
                            ac['elev_deg'] = elev
                            ac['fspl_db'] = fspl

                            # Imprimir evento completo en consola
                            call_disp = ac['callsign'] or 'N/A'
                            spd_disp = ac['speed'] if ac['speed'] is not None else 'N/A'
                            print(f"{icao:<8} | {call_disp:<9} | {ac['alt']:<8} | {spd_disp:<8} | {r_km:<10.2f} | {elev:<8.1f} | {fspl:<9.1f} | {ac['lat']:.5f}, {ac['lon']:.5f}")

            # Actualizar archivo KML cada 2 segundos
            if time.time() - last_kml_update > 2.0:
                KMLExporter.update_kml(aircraft_db)
                last_kml_update = time.time()

    except KeyboardInterrupt:
        print("\nMotor de telemetría detenido por el usuario.")
    except ConnectionRefusedError:
        print(f"\n[ERROR] No se pudo conectar a dump1090 en {HOST}:{PORT}.")
        print("Asegúrate de que 'dump1090.exe --interactive --net' esté ejecutándose en otra terminal.")
    finally:
        client.close()

if __name__ == "__main__":
    main()