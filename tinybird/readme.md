## Data Project

The `anomaly-detection` data project includes two Data Sources and over a dozen Pipes. 

### /datasources
* incoming_data - where the ingested data is written to. 
* copy_log_duplicates - Where Copy Pipes write new detections every Copy interval. For this project, the interval is every minute. 
* copy_log - stores a deduplicated compilation of anomaly detections. The `dedup_log` Pipe reads from the `copy_log_duplicates` Data Source and writes to the `copy_log` using a Materialized View. 

### /pipes 

There are two Pipes for each of the five anomaly types. One set provides 'recipes' for creating API Endpoints for each detection technique. The other set are `Copy Pipes` that apply the same queries and write output to a shared `copy_log`. 

The `get_anomalies` Pipe provides an API Endpoint for querying the triggered anomalies log. This makes it possible to query a single endpoint and receive results from all five detection methods.  


### Copy Pipes

These Copy Pipes are based on the anomaly detection Pipes. Their Job is to test for anomalies across all sensors and write output to the `copy_log` Data Source. These Copy Pipes do the work of compiling their detections into a single place. 

These Copy Pipes are configured to run every few minutes. In that sense, the compiled log is not up-to-the-second fresh, but does provide a single Endpoint to monitor five types of anomalies across an entire set of sensors. 

These Copy Pipes do not support query parameters so some details are hardcoded in the Nodes. For example, the `copy_out_of_range` Pipe hardcodes the minimum and maximum allowable thresholds, along with how far back the detection window should go. Here we are setting the minimum valid value to 200, the maximum to 2000, and the time window to the most recent 30 minutes. 

```sql
%
{% set _min_value=200 %}
{% set _max_value=2000 %}
{% set _detect_window_seconds=61 %} # This Pipe makes a copy every minute, so selecting events since last copy plus one minute. 

SELECT id, timestamp, value, 
{{_min_value}} AS min_value, 
{{_max_value}} AS max_value
FROM incoming_data
WHERE (value < {{_min_value}} OR value > {{_max_value}}) 
AND timestamp > NOW() - INTERVAL {{_detect_window_seconds}} SECONDS
```
Here we are adding `min_value` and `max_value` to the SELECT statement to pass them to a subsequent Node that records these values in a `note` column. 

### Compiling detections into a single source  

The `monitor_logs` API Endpoint pulls from the `copy_log` Data Source that is fed by the Copy Pipes, which get triggered every minute. The endpoint returns a list of anomaly detections across the set of sensors for all the anomaly types.  

While this compilation is not based on up-to-the-second fresh data, this endpoint provides a single endpoint that covers the five different anomaly types with a up-to-the-minute results.  

`https://api.tinybird.co/v0/pipes/monitor_logs.json`

