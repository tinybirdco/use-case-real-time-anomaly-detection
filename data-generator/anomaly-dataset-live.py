import requests
import random
import datetime
import csv
import os
import json
import datetime
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '../config', '.env')
load_dotenv(dotenv_path)

num_sensors = 10
num_iterations = 1000000  # Nearly three hours with a 1-second interval. 
sample_interval = 1 # seconds 

# Set the Tinybird Events API endpoint and load the API token from the local environment (.env). 
# TODO: not batching reports sent to Tinybird. 
tinybird_url = "https://api.tinybird.co/v0/events?name=incoming_data"
tinybird_token = os.environ.get('TINYBIRD_TOKEN')
headers = {"Authorization": f"Bearer {tinybird_token}", "Content-Type": "application/json"}

class Sensor:
    def __init__(self, sensor_id):
        self.id = sensor_id
    
        self.timestamp = generate_timestamp() 
        self.value = random.randint(400, 700)
        self.initial_value = self.value
        self.previous_value = self.value

        self.reports = []
        self.report = {}
        self.report['timestamp'] = self.timestamp
        self.report['value'] = self.value
    
        self.stopped = False
        self.absent = False
        self.trend = None # 'up', 'down'

        # Some persistent stats
        self.window = 3600 # seconds.
        self.average = 0
        self.average_window = 0
        self.max = 0
        self.min = 0

        # Validation metadata
        self.valid_max = 1000
        self.valid_min = 200
   
    def generate_new_value(self):

        value = self.value

        if value < self.valid_min or value > self.valid_max:
            value = self.previous_value

        # For some small percentage, generate a out-of-bounds value
        if random.uniform(0,100) < 0.05:
            if random.uniform(0,100) < 50:
                value = random.uniform(0,self.valid_min-20)
            else:
                value = random.uniform(self.valid_max+20, 1200)
            return value    
        else: #Generate a new value

            # For some small percentage, generate a step change
            step_control = random.uniform(0,100)
            step_amount = random.uniform(50,80)
            if step_control < 0.03 and self.trend == None:
                change = random.choice([-1,1]) * step_amount
            elif step_control < 0.06 and self.trend != None:
                if self.trend == 'up':
                    change = step_amount
                elif self.trend == 'down':
                    change = -step_amount
            else:    
                change = random.uniform(-1,1)
                
            value = value + change

            # If in range, save this as the previous value.
            if value > self.valid_min or value < self.valid_max:
                self.previous_value = value

        return value

    def generate_new_report(self):
        # print(f"Generate new sensor report based on current: {self.report}")

        # Calculate new value
        self.value = self.generate_new_value()
        # Calculate new timestamp
        
        self.timestamp = generate_timestamp()
        # Create new report
        self.report = {}
        
        self.report['timestamp'] = self.timestamp
        self.report['value'] = self.value

        self.report['id'] = self.id # Need to send sensor ID. 
        report_json = json.dumps(self.report)
        response = requests.post(tinybird_url, headers=headers, data=report_json)

def sensor_presets(sensors):
    sensors[2].trend = 'up'
    value = 200
    sensors[2].value = value 
    sensors[2].initial_value = value 
    sensors[2].previous_value = value 
    sensors[2].reports = []
    report = {}
    report['timestamp'] = sensors[2].timestamp
    report['value'] = value
    sensors[2].reports.append(report)
    
    sensors[3].trend = 'down'
    value = 700
    sensors[3].value = value 
    sensors[3].initial_value = value 
    sensors[3].previous_value = value 
    sensors[3].reports = []
    report = {}
    report['timestamp'] = sensors[3].timestamp
    report['value'] = value
    sensors[3].reports.append(report)

    return sensors

def generate_dataset():
  
    # Create sensor objects.
    print(f"Creating {num_sensors} sensors.")
    sensors = []
    # Create an array of Vehicle objects
    sensors = [Sensor(sensor_id) for sensor_id in range(1, num_sensors + 1)]

    sensors = sensor_presets(sensors)

    # Select a random sensor to stop reporting after 50 iterations
    #stopped_sensor_id = random.randint(1, len(sensors) )
    stopped_sensor_id = 5
    stopped_iteration = random.randint(100,200)

    print("Starting to stream data to the Events API...")

    # March through the configured iterations... 
    for i in range(num_iterations):
        for sensor in sensors:    
            # print(f"Generating new sample for sensor {sensor.id}")
            if sensor.stopped:
                # print(f"Sensor {sensor.id} has stopped reporting.")
                # TODO: May want mechanism for a sensor to restart. 
                pass
            else:    
                sensor.generate_new_report()

            # If the sensor is the randomly selected sensor and it has reached 50 iterations, stop it from reporting
            if i == stopped_iteration and sensor.id == stopped_sensor_id:
                sensor.stopped = True
    
def generate_timestamp():
    # Get the current datetime object
    now = datetime.datetime.now()
    # Format the datetime object in the "%Y-%m-%d %H:%M:%S.0" format
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.0')
    return timestamp

if __name__ == '__main__':
  
    generate_dataset()