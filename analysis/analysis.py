# analysis.py
# ufwairrapiertracker V4.0 - Forensic Analysis
# 1. Verifies log integrity via hash chain
# 2. Runs 4-sensor ML anomaly detection
# 3. Maps verified attacks

import pandas as pd
import matplotlib.pyplot as plt
import os
import hashlib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

LOG_FILE = 'forensic_log_v4.csv'
# NEW Features to analyze
FEATURES = ['pressure_delta', 'vibration_mag', 'audio_level', 'dust_voltage']


def verify_hash_chain(df):
    """Verifies the SHA-256 hash chain. Returns True if valid."""
    print("\n--- FORENSIC VERIFICATION ---")
    is_valid = True

    # Check genesis block
    if df.iloc[0]['prev_hash'] != "0" * 64:
        print("!! TAMPERING DETECTED: Genesis hash (line 1) is incorrect. !!")
        return False

    for i in range(1, len(df)):
        # Get the previous line (as a string, exactly as logged)
        prev_line_data = df.iloc[i - 1]
        prev_line_string = f"{prev_line_data['timestamp']},{prev_line_data['pressure_delta']:.2f},{prev_line_data['vibration_mag']:.2f}," \
                           f"{prev_line_data['audio_level']},{prev_line_data['dust_voltage']:.3f},{prev_line_data['lat']:.6f}," \
                           f"{prev_line_data['lon']:.6f},{prev_line_data['alt']:.1f},{prev_line_data['prev_hash']}"

        # Calculate its hash
        expected_hash = hashlib.sha256(prev_line_string.encode('utf-8')).hexdigest()

        # Compare to the hash stored in the current line
        stored_hash = df.iloc[i]['prev_hash']

        if expected_hash != stored_hash:
            print(f"!! TAMPERING DETECTED at line {i + 1} !!")
            print(f"  Stored Hash:   {stored_hash}")
            print(f"  Expected Hash: {expected_hash}")
            is_valid = False
            break

    if is_valid:
        print("VERIFIED: Log file integrity is 100%. No tampering detected.")
    else:
        print("CRITICAL: Log file has been tampered with. Analysis is unreliable.")

    return is_valid


def analyze_log(df):
    print("\n--- SENSOR LOG ANALYSIS (V4.0) ---")

    # 1. Prepare data for ML
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[FEATURES])

    # 2. Train Anomaly Detection Model
    model = IsolationForest(contamination=0.001, random_state=42)
    print("Training ML model on 4-sensor data...")
    model.fit(df_scaled)

    # 3. Predict Anomalies
    print("Predicting anomalies...")
    df['is_anomaly'] = model.predict(df_scaled)  # -1 for anomaly

    attacks = df[df['is_anomaly'] == -1]

    if attacks.empty:
        print("\n--- RESULT ---")
        print("No significant anomalies (attacks) detected in the log.")
    else:
        print(f"\n--- {len(attacks)} ANOMALOUS EVENTS DETECTED ---")
        attacks_with_gps = attacks[(attacks['lat'] != 0.0) & (attacks['lon'] != 0.0)]

        if attacks_with_gps.empty:
            print("Found attacks, but none had a GPS lock.")
            print(attacks[FEATURES])
        else:
            print("Attacks with valid GPS data:")
            print(attacks_with_gps[['lat', 'lon'] + FEATURES])

            # 4. Generate Attack Map
            print("Generating attack map...")
            plt.figure(figsize=(12, 8))

            df_gps_normal = df[(df['lat'] != 0.0) & (df['lon'] != 0.0) & (df['is_anomaly'] == 1)]
            plt.scatter(df_gps_normal['lon'], df_gps_normal['lat'], c='grey', alpha=0.1, s=1, label='Normal Path')

            plt.scatter(attacks_with_gps['lon'], attacks_with_gps['lat'], c=attacks_with_gps['dust_voltage'],
                        cmap='Reds', s=50, label='Attack (Color=Dust)', edgecolors='black')

            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title('V4.0 Forensic Map: Attack Location (Color by Dust Level)')
            plt.colorbar(label='Dust Sensor Voltage')
            plt.legend()
            plt.grid(True)
            plt.axis('equal')
            plt.savefig('attack_map_V4_forensic.png')
            print("Saved 'attack_map_V4_forensic.png'")
            plt.clf()


if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Copy it from the SD card.")
    else:
        print(f"Loading log file: {LOG_FILE}...")
        data = pd.read_csv(LOG_FILE)

        # Verify the hash chain *first*
        if verify_hash_chain(data):
            # If valid, proceed with analysis
            analyze_log(data)
        else:
            print("Analysis aborted due to log integrity failure.")
