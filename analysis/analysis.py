# analysis.py
# Reads the attack_log.csv and generates analytics.
# Needs: pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt
import os

LOG_FILE = 'attack_log.csv'


def analyze_attacks(df):
    if df.empty:
        print("No attack data found.")
        return

    num_attacks = len(df)
    avg_duration = df['duration_ms'].mean()
    avg_pressure_drop = df['avg_delta_pa'].mean()

    print("--- AIR RAPIER ATTACK ANALYSIS ---")
    print(f"Total Attacks Logged: {num_attacks}")
    print(f"Average Duration: {avg_duration:.2f} ms")
    print(f"Average Pressure Drop: {avg_pressure_drop:.2f} Pa")

    # Activity analysis
    if 'activity' in df.columns:
        activity_counts = df['activity'].value_counts()
        print("\n--- Activity During Attacks ---")
        print(activity_counts)

        most_common_activity = activity_counts.idxmax()
        print(f"\nMost Common Activity During Attack: {most_common_activity}")

        # Plot Activity Pie Chart
        activity_counts.plot(kind='pie',
                             title='Activity During Attacks',
                             autopct='%1.1f%%',
                             startangle=90,
                             figsize=(8, 8))
        plt.ylabel('')  # Hide the 'activity' label
        plt.savefig('attack_activity_pie.png')
        print("Saved 'attack_activity_pie.png'")
        plt.clf()

    # Plot Attack Duration Histogram
    df['duration_ms'].plot(kind='hist',
                           bins=20,
                           title='Attack Duration Distribution',
                           figsize=(10, 6))
    plt.xlabel('Duration (ms)')
    plt.savefig('attack_duration_hist.png')
    print("Saved 'attack_duration_hist.png'")
    plt.clf()

    # Plot Pressure vs. Duration
    df.plot(kind='scatter',
            x='duration_ms',
            y='avg_delta_pa',
            title='Attack Intensity vs. Duration',
            figsize=(10, 6))
    plt.xlabel('Duration (ms)')
    plt.ylabel('Average Pressure Drop (Pa)')
    plt.savefig('attack_pressure_vs_duration.png')
    print("Saved 'attack_pressure_vs_duration.png'")
    plt.clf()


if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Copy it from the SD card.")
    else:
        # Load the CSV
        data = pd.read_csv(LOG_FILE)
        analyze_attacks(data)
