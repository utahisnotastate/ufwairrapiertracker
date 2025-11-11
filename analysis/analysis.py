# analysis.py
# ufwairrapiertracker V2.0 - ML Anomaly Detection
# Uses Isolation Forest to find "attack" signatures in sensor data.
# Inspired by:

import pandas as pd
import matplotlib.pyplot as plt
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

LOG_FILE = 'sensor_log.csv'
# Define the features to analyze for anomalies
FEATURES = ['pressure_delta', 'vibration_mag', 'audio_level']


def analyze_log(df):
    if df.empty:
        print("Log is empty.")
        return

    print("--- Sensor Log Analysis (V2.0) ---")

    # 1. Prepare data
    # We can't feed raw data to the model. We must scale it.
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[FEATURES])

    # 2. Train Anomaly Detection Model
    # IsolationForest is fast and effective.
    # 'contamination' is the expected % of anomalies. Let's start low.
    model = IsolationForest(contamination=0.001, random_state=42)
    print("Training ML model...")
    model.fit(df_scaled)

    # 3. Predict Anomalies
    print("Predicting anomalies...")
    df['anomaly_score'] = model.decision_function(df_scaled)
    df['is_anomaly'] = model.predict(df_scaled)  # -1 for anomaly, 1 for normal

    # Get all "attack" events
    attacks = df[df['is_anomaly'] == -1]

    if attacks.empty:
        print("\n--- RESULT ---")
        print("No significant anomalies (attacks) detected in the log.")
    else:
        print(f"\n--- {len(attacks)} ANOMALOUS EVENTS DETECTED ---")
        print("These are the moments that match the 3-sensor attack signature:")
        print(attacks[['pressure_delta', 'vibration_mag', 'audio_level', 'anomaly_score']])

        # Plot the main graph
        print("Generating anomaly plot...")
        fig, ax = plt.subplots(figsize=(20, 8))

        # Plot the anomaly score
        ax.plot(df.index, df['anomaly_score'], label='Anomaly Score', color='blue', alpha=0.5)
        ax.set_ylabel('Anomaly Score', color='blue')

        # Highlight attacks
        ax.scatter(attacks.index, attacks['anomaly_score'], color='red', label='Detected Attack', s=50, zorder=10)

        # Plot pressure delta on a second y-axis to correlate
        ax2 = ax.twinx()
        ax2.plot(df.index, df['pressure_delta'], label='Pressure Delta (Pa)', color='green', alpha=0.3)
        ax2.set_ylabel('Pressure Delta (Pa)', color='green')

        plt.title('V2.0 Attack Analysis: Anomaly Score vs. Pressure')
        fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.9))
        plt.grid(True)
        plt.savefig('attack_analysis_V2.png')
        print("Saved 'attack_analysis_V2.png'")
        plt.clf()


if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Copy it from the SD card.")
    else:
        print(f"Loading log file: {LOG_FILE}...")
        data = pd.read_csv(LOG_FILE)
        # Convert ms timestamp to a simple index for plotting
        data = data.reset_index()

        analyze_log(data)
