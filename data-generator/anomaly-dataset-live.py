import requests
import random
import datetime
import time
import os
import json
import yaml
import datetime
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.', '.env')
load_dotenv(dotenv_path)

with open('./settings.yaml') as file:
    config = yaml.safe_load(file)

num_sensors = config['num_sensors']
sleep_seconds = config['sleep_seconds']
post_batch_size = config['post_batch_size']
num_iterations = config['num_iterations']
id_init_min = config['id_init_min']
id_init_max = config['id_init_max']

valid_max = config['valid_max']
valid_min = config['valid_min']

value_max = config['value_max']
value_min = config['value_min']
value_max_normal_change = config['value_max_normal_change']

step_max = config['step_max']
step_min = config['step_min']
percent_step = config['percent_step']
percent_step_trend = config['percent_step_trend']
percent_out_of_bounds = config['percent_out_of_bounds']
percent_out_of_bounds_high = config['percent_out_of_bounds_high']

# Set the Tinybird Events API endpoint and load the API token from the local environment (.env). 
# TODO: not batching reports sent to Tinybird. 
tinybird_url = "https://api.tinybird.co/v0/events?name=incoming_data"
tinybird_token = os.environ.get('TINYBIRD_TOKEN')
headers = {"Authorization": f"Bearer {tinybird_token}", "Content-Type": "application/json"}


class Sensor:
    def __init__(self, sensor_id):
        self.id = sensor_id
    
        self.timestamp = generate_timestamp() 
        self.value = random.randint(id_init_min, id_init_max)
        self.initial_value = self.value
        self.previous_value = self.value

        self.reports = []
        self.report = {}
        self.report['timestamp'] = self.timestamp
        self.report['value'] = self.value
    
        self.stopped = False
        self.trend = None # 'up', 'down'

        # Validation metadata
        self.outliers = True
        self.valid_min = valid_min
        self.valid_max = valid_max
           
    def generate_new_value(self):

        value = self.value

        if value < self.valid_min or value > self.valid_max:
            value = self.previous_value

        # For some small percentage, generate a out-of-bounds value
        if self.outliers and random.uniform(0,100) < percent_out_of_bounds:
            if random.uniform(0,100) < (100 - percent_out_of_bounds_high):
                value = random.uniform(value_min,self.valid_min-20)
            else:
                value = random.uniform(self.valid_max+20, value_max)
            return value    
        
        else: #Generate a new value

            # For some small percentage, generate a step change
            step_control = random.uniform(0,100)
            step_amount = random.uniform(step_min, step_max)
            if step_control < percent_step and self.trend == None:
                change = random.choice([-1,1]) * step_amount
            elif step_control < percent_step_trend and self.trend != None:
                if self.trend == 'up':
                    change = step_amount
                elif self.trend == 'down':
                    change = -step_amount
            else:    
                change = random.uniform(-value_max_normal_change,value_max_normal_change)
                
            value = value + change

            # If in range, save this as the previous value.
            if value > self.valid_min or value < self.valid_max:
                self.previous_value = value
            else:
                print(f"New value of out range: {value}")    

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
        self.report['id'] = self.id # Need to send sensor ID. 
        self.report['value'] = round(self.value,2)

        self.reports.append(self.report)

        #report_json = json.dumps(self.report)
        #response = requests.post(tinybird_url, headers=headers, data=report_json)

        return self.report

def generate_timestamp():
    # Get the current datetime object
    now = datetime.datetime.utcnow()
    # Format the datetime object in the "%Y-%m-%d %H:%M:%S.000" format
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-2]
    
    return timestamp

def sensor_presets(sensors, config):
    for sensor_data in config['sensor_overrides']:
        id = sensor_data['id'] - 1
        trend = sensor_data['trend']
        initial_value = sensor_data['initial_value']
        outliers = sensor_data['outliers']

        sensors[id].trend = trend
        sensors[id].outliers = outliers
        sensors[id].value = initial_value
        sensors[id].initial_value = initial_value
        sensors[id].previous_value = initial_value
        sensors[id].reports = []
        report = {}
        report['timestamp'] = sensors[id].timestamp
        report['value'] = initial_value
        sensors[id].reports.append(report)

    return sensors

def assemble_payload(reports):
    pass
    payload = ''
    for report in reports:
        json_string = json.dumps(report)
        payload += json_string + '\n'

    return payload

def generate_dataset():
  
    # Create sensor objects.
    print(f"Creating {num_sensors} sensors.")
    sensors = []
    reports = []
    # Create an array of Vehicle objects
    sensors = [Sensor(sensor_id) for sensor_id in range(1, num_sensors + 1)]

    sensors = sensor_presets(sensors, config)

    # Select a random sensor to stop reporting after 50 iterations
    #stopped_sensor_id = random.randint(1, len(sensors) )
    stopped_sensor_id = 5
    stopped_iteration = random.randint(100,150)

    print("Starting to stream data to the Events API...")

    batched_reports = 0
    # March through the configured iterations... 
    for i in range(num_iterations):
        time.sleep(sleep_seconds)
        for sensor in sensors:    
            print(f"Generating new sample for sensor {sensor.id}")
            if sensor.stopped:
                # print(f"Sensor {sensor.id} has stopped reporting.")
                # TODO: May want mechanism for a sensor to restart. 
                pass
            else:    
                report = sensor.generate_new_report()
                reports.append(report)
                batched_reports = batched_reports + 1

            # If the sensor is the randomly selected sensor and it has reached 50 iterations, stop it from reporting
            if i == stopped_iteration and sensor.id == stopped_sensor_id:
                print(f"Sensor {stopped_sensor_id} stopped at {datetime.datetime.utcnow()}")
                sensor.stopped = True

            if batched_reports >= post_batch_size:
                print(f"Sending {len(reports)} to Events API")
                reports_json = assemble_payload(reports)
                #reports_json = json.dumps(sensor.reports)
                response = requests.post(tinybird_url, headers=headers, data=reports_json)
                status_code = response.status_code
                
                if status_code >= 200 and status_code <= 202:
                    reports = []
                    sensor.reports = []
                    batched_reports = 0
                else:
                    print(f"Events request error: {response.status_code} : {response.reason}")    

 
if __name__ == '__main__':
  
    generate_dataset()
