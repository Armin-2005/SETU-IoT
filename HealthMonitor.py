import asyncio
import time
import BlynkLib
import csv
from datetime import datetime
from seeed_dht import DHT
from bleak import BleakClient

BLYNK_AUTH = "hQEbOyPFvAXm-uIr9rW5Ay8iB6rKBxfS"
POLAR_ADDRESS = "24:AC:AC:13:EE:AA" 

HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
LOG_FILE = "health_log.csv"

blynk = BlynkLib.Blynk(BLYNK_AUTH)
dht_sensor = DHT("11", 5) 

last_hr_sent = 0
current_heart_rate = 0

# Heart Rate
def handle_hr_data(sender, data):
    global last_hr_sent, current_heart_rate
    current_time = time.time()
    current_heart_rate = data[1]
    
    if current_time - last_hr_sent >= 5:
        print(f"Heart Rate: {current_heart_rate} bpm")
        blynk.virtual_write(2, current_heart_rate)
        
        if current_heart_rate > 100:
            blynk.log_event("high_hr", f"Warning: High HR detected: {current_heart_rate}")
        elif current_heart_rate < 60:
            blynk.log_event("low_hr", f"Warning: Low HR detected: {current_heart_rate}")
            
        last_hr_sent = current_time

async def main():
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Heart Rate (bpm)", "Temperature (C)", "Humidity (%)"])
    
    print("Connecting to Polar H10...")
    async with BleakClient(POLAR_ADDRESS) as client:
        print(f"Connected: {client.is_connected}")
        
        await client.start_notify(HR_UUID, handle_hr_data)
        
        last_env_read = 0
        
        while True:
            blynk.run() 
            
            if time.time() - last_env_read > 30:
                humi, temp = dht_sensor.read()
                if humi is not None and temp is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] Saving Snapshot: HR={current_heart_rate}, T={temp}, H={humi}")

                    blynk.virtual_write(0, temp)
                    blynk.virtual_write(1, humi)

                    with open(LOG_FILE, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, current_heart_rate, temp, humi])

                last_env_read = time.time()
            
            await asyncio.sleep(0.1) 

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Project stopped. Data saved in the file: {LOG_FILE}. Goodbye!")
