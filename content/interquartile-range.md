# Interquartile Range (IQR) anomalies
#### Using quartiles to identify anomalies. 

##### Another method of generating data statistics to identify pattern changes, rather than triggering on single or pairs of isolated data points.

The Interquartile Range (IQR) method is a valuable tool for identifying anomalies in real-time data by providing a standardized way to compare individual data points to the overall trend of the data. This method is effective for identifying outliers and anomalies in sensor data. When a sensor reading is outside of an IQR-based range, it indicates a deviation from the expected behavior. 

The first step of the Interquartile Range (IQR) method is calculating the first and third quartiles (Q1 and Q3). These quartiles are based on a moving time window of the recent data. 

The difference between these two quartiles is referred to as the IQR, as in:

IQR = Q3 - Q1

Data points that are below or above some level based on a multiplier of this IQR are considered outliers. Commonly, this multiple is set to `1.5`, so we are looking for cases where:

* values < Q1 - (IQR * 1.5) 
* values > Q3 + (IQR * 1.5) 

## `iqr` Pipe and Endpoint

The `iqr` Pipe is designed to be flexible by supporting the following API Endpoint query parameters:
* **sensor_id** - Used to select a single sensor of interest.
* **iqr_multiplier** - The threshold for determining Z-score outliers. Compared with absolute value of Z-score.
* **stats_window_minutes** - Defines the time window (in minutes) for calculating data averages and standard deviations used to calculate Z-score.
* **detect_window_seconds** - Defines the time window (in seconds) for selecting data points to examine for anomalies. If polling on an interval, this can be set to match that interval to minimize duplicate detections.
* **max_per_sensor** - Used to limit the number of IQR anomalies to return by sensor.

### `endpoint` Node

The `endpoint` Node uses a Common Table Expression (CTE) to determine Q1 and Q3 for a time window of recent data based on the `_stats_window_minutes` parameter. This Node also implements the query parameter for selecting a sensor id of interest. 

The main query JOINs with the `stats` CTE and tests each event within the `_detect_window_seconds` against the lower and upper bounds based on the IQR and the multiplier. 

There is also a `_max_per_sensor` parameter to limit the number anomaly events to return per sensor. When data is arriving many times a second, the anomaly events can get noisy when they start occurring. 


```sql
%
{% set _iqr_multipler=1.5 %}  # A multipler used to determine the IQR value. 
{% set _stats_window_minutes=10 %}  # Statistical quartiles are based on this most recent window.
{% set _detect_window_seconds=600 %} # For each request, we look back 10 minutes. 

WITH stats AS (SELECT id,
   quantileExact(0.25) (value) AS lower_quartile,
   quantileExact(0.75) (value) AS upper_quartile,
   (upper_quartile - lower_quartile) * {{_iqr_multipler}} AS IQR
FROM incoming_data
WHERE timestamp >= toDate(NOW()) - INTERVAL {{Int16(_stats_window_minutes)}} MINUTES
  {% if defined(sensor_id) %}               
    AND id = {{ Int32(sensor_id)}}
  {% end %}    
GROUP BY id
)
 SELECT DISTINCT timestamp, 
    id, 
    value, 
    ROUND((stats.lower_quartile - stats.IQR),2) AS lower_bound, 
    ROUND((stats.upper_quartile + stats.IQR),2) AS upper_bound 
 FROM incoming_data
 JOIN stats ON incoming_data.id = stats.id
 WHERE timestamp >= toDate(NOW()) - INTERVAL {{Int16(_detect_window_seconds)}} SECONDS
 AND (value > (stats.upper_quartile + stats.IQR)
 OR value < (stats.lower_quartile - stats.IQR))
 ORDER BY timestamp DESC

```
