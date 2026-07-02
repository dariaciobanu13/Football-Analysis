import time
import os
import pandas as pd
from data_ingestion import fetch_match_data, process_and_flatten_data
from reporter import plot_kafka_stream_performance

class KafkaSimulator:
    """
    Simulates an Apache Kafka message broker for real-time football analytics.
    It takes batch data and "emits" events one by one as if they were coming from a 
    live sensor or TV feed.
    """
    def __init__(self, match_id):
        self.match_id = match_id
        print(f"\n[KAFKA BROKER] Initializing Stream for Match ID {match_id}...")
        self.raw_data = fetch_match_data(match_id)
        self.processed_data = process_and_flatten_data(self.raw_data)
        
    def stream_events(self, speed=0.01):
        """
        Generates a stream of events.
        'speed' controls the sleep time between messages.
        """
        print(f"[KAFKA TOPIC] Topic 'match_events_{self.match_id}' is now LIVE.")
        
        # Sort by time to ensure stream is chronological
        stream_ready = self.processed_data.sort_values(by='Time_Minute')
        
        for idx, event in stream_ready.iterrows():
            # In a real Kafka app, this would be a producer.send()
            yield event.to_dict()
            time.sleep(speed)

def consume_stream_simulation(match_id, team_name):
    """
    Demonstrates how a Real-time Consumer would process the Kafka stream.
    """
    broker = KafkaSimulator(match_id)
    print("\n[CONSUMER] Real-time Performance Monitor Starting...")
    print(f"[CONSUMER] Filtering stream for Cluster: {team_name}\n")
    
    count = 0
    start_time = time.time()
    
    # We simulate a "sliding window" logic in a simplified way here
    for event in broker.stream_events(speed=0.005):
        if event['Team_Name'] == team_name:
            count += 1
            if count % 50 == 0:
                print(f"[LIVE MONITOR] Processed {count} packets for {team_name}. Active Time: {event['Time_Minute']}m")
                
                # Logic: If this was a real app, we would update the Rolling Averages here
                # and trigger alerts if the QoS drops in the last 5 minutes.
                
        if count >= 300: # Stop after 300 events for the demo
            break
            
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n[INFO] Real-time Simulation Complete. Processed {count} events in {duration:.2f} seconds.")
    
    # Generate Plot
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    kafka_path = os.path.join(reports_dir, "Kafka_Stream_Throughput.png")
    plot_kafka_stream_performance(count, duration, filename=kafka_path)
    
    print(f"[INFO] Arhitecture is Kafka-Ready. Plot: {os.path.abspath(kafka_path)}")

if __name__ == "__main__":
    consume_stream_simulation(303596, "Barcelona")
