# Rate-of-change anomalies
### Checks incoming data and calculates the rate of change, or slope, based on the previous data point. A simple concept with a more-complicated-than-expected implementation. 

Monitoring the rate of change in sensor readings is crucial for identifying abrupt changes in the system. By setting thresholds on the slope of the data, you can detect instances where the rate of change exceeds an acceptable limit. This is particularly useful for identifying gradual deteriorations or sudden disruptions.

To determine the slope, the previous report is retrieved and compared with the current report. The rate-of-change, or slope, is equal to the change in the y-values over the change in x-values.   

Knowing the current and previous values, slope is calculated as:

 `(value - previous_value) / (timestamp - previous_timestamp) AS slope`


## Selecting previous values

This recipe is based on the use of the ClickHouse `lagInFrame` function to select the timestamp and value of a sensor's previous report. This function allows you to access data from previous rows in your result set based on a specific ordering within partitions defined by the PARTITION BY clause.

Here is how the `previous_timestamp` and `previous_value` values are retrieved:

```sql

lagInFrame(timestamp, 1) OVER 
(PARTITION BY id ORDER BY timestamp ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) AS previous_timestamp, 

lagInFrame(value, 1) 
OVER (PARTITION BY id ORDER BY timestamp ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) AS previous_value

```

These query statements surface the previous `timestamp` and `value` attributes within each partition defined by the `id`. Specifically, it retrieves the `timestamp` and `value` values from the row that precedes the current row by 1 position within each partition. The `ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING` clause specifies the window frame over which the lag function operates. In this case, it is looking at the immediately preceding row. 

## `rate_of_change` Pipe and Endpoint

The `rate_of_change` Pipe consists of two Nodes: `calculating_slope` and `endpoint`.

It is designed to be flexible by supporting the following API Endpoint query parameters:
* **sensor_id** - Used to select a single sensor of interest.
* **detect_window_seconds** - Defines the time window (in seconds) for selecting data points to examine for anomalies. If polling on an interval, this can be set to match that interval to minimize duplicate detections.
* **max_slope** - Sensor reports with an absolute slope more than than this are marked as an anomaly. 

### `calculating_slope` Node


```sql
%
{% set _detect_window_seconds_default = 600 %}
{% set _max_slope = 3 %}

SELECT id, 
  timestamp, 
  previous_timestamp,
  (value - previous_value) / (timestamp - previous_timestamp) as slope,
  value, 
  previous_value,
  (value - previous_value) as value_diff,
  (timestamp - previous_timestamp) as time_diff,
  {{Int16(max_slope, _max_slope, description="Integer. Maximum slope, any higher than this are returned.")}} as max_slope,
  lagInFrame(timestamp, 1) OVER 
    (PARTITION BY id ORDER BY timestamp ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) AS previous_timestamp, 
  lagInFrame(value, 1) OVER
    (PARTITION BY id ORDER BY timestamp ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) AS previous_value
FROM incoming_data
WHERE timestamp > NOW() - INTERVAL {{Int16(detect_window_seconds, _detect_window_seconds_default, description="Search this many most recent minutes of the data history.")}} SECOND
  {% if defined(sensor_id) %}               
    AND id = {{ Int32(sensor_id)}}
  {% end %}    
ORDER BY timestamp DESC

```

### `endpoint` Node

```sql
SELECT id, 
  timestamp, 
  Round(slope,2) as slope, 
  Round(value_diff,2) as value_diff, 
  time_diff, 
  previous_value, 
  value, 
  max_slope 
FROM calculating_slope
WHERE ABS(slope) > max_slope
ORDER BY timestamp DESC
```

