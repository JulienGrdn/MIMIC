import time
import yaml
import random
import paho.mqtt.client as mqtt
import os

# Configuration
YAML_FILE = 'example/devices_configuration.yaml'
PUBLISH_INTERVAL = .5  # Seconds between updates

def load_config(path):
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        exit(1)
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def generate_value(data_type, format = None):
    """Generates a random value based on the YAML type definition."""
    generated_value = 0
    if data_type == 'float':
        generated_value =  round(random.uniform(0.0, 24.0), 2)
    elif data_type == 'integer':
        generated_value = random.randint(0, 100)
    elif data_type == 'boolean':
        # specific string format for booleans can be adjusted here (e.g., "true", "ON", "1")
        generated_value = str(random.choice([True, False])).lower()
    if format is not None:
        payload_type, payload_value_location = eval(format)
        if payload_type == 'list':
            payload_iterable = []
            for _ in range(payload_value_location):
                payload_iterable.append(None)
            payload_iterable.append(generated_value)
        elif payload_type == 'dict':
            payload_iterable = {payload_value_location:generated_value}
        return str(payload_iterable)
    else:
        return generated_value

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def main():
    config = load_config(YAML_FILE)
    broker_address = config.get('broker', 'localhost')
    
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        print(f"Connecting to broker at {broker_address}...")
        client.connect(broker_address, 1883, 60)
        client.loop_start()

        print("Starting publication loop (Press CTRL+C to stop)...")
        
        while True:
            for device in config.get('devices', []):
                base_topic = device.get('mqtt_base_topic')
                
                if not base_topic:
                    continue

                for channel in device.get('channels', []):
                    # We only publish if a status_suffix is defined
                    if 'status_suffix' in channel:
                        suffix = channel['status_suffix']
                        topic = f"{base_topic}/{suffix}"
                        
                        # Generate dummy data based on type
                        val = generate_value(channel.get('type'), channel.get('mqtt_payload_format'))
                        
                        # Publish
                        client.publish(topic, val)
                        print(f"[{device['nickname']}] Published {val} to {topic}")

            print("-" * 30)
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
