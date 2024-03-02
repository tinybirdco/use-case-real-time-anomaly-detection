# Z-Score anomalies
### Using averages and standard deviations to identify anomalies. 

#### Another method of generating data statistics to identify pattern changes, rather than triggering on single or pairs of isolated data points.

This recipe was inspired by [this previous Tinybird blog post about detecting anomalies with Z-scores](https://www.tinybird.co/blog-posts/anomaly-detection). 

Z-scores are a valuable tool for identifying anomalies in real-time data by providing a standardized way to compare individual data points to the overall trend of the data. When a sensor reading exceeds a certain Z-Score threshold, it indicates a deviation from the expected behavior. This method is effective for identifying outliers and anomalies in sensor data.

Z-scores are based on data averages and standard deviations. These statistics are based on a moving time window of the recent data. 

For each new incoming data point, the Z-score is calculated using the formula:
Z-score = (value - average) / stddev
where:

* `value` is the data point being evaluated. 
* `average` is the average of the data within the chosen time window.
* `stddev` is the standard deviation of the data within the same window.

Currently, this Pipe is based on two time windows:
1) First, the statistics are calculated across the `_stats_time_window_minutes` interval.
2) Second, anomalies are scanned for using the `_detect_window_seconds` interval.

Below the `zscore_multiplier defaults to 3, and this parameter is one to experiment with. 

Note:

* Choosing an appropriate statistics window size is crucial. A small window may be too sensitive to fluctuations, while a large window might miss recent changes.
* Z-scores are less effective for highly seasonal or non-stationary time series data, where the mean and standard deviation might exhibit significant trends over time.


## `z_score` Pipe and Endpoint

The `z_score` Pipe consiste of two Nodes: `calculate_z_score` and `endpoint`.

The `z_score` Pipe is designed to be flexible by supporting the following API Endpoint query parameters:
* **sensor_id** - Used to select a single sensor of interest.
* **zscore_threshold** - The threshold for determining Z-score outliers. Compared with absolute value of Z-score.
* **stats_window_minutes** - Defines the time window (in minutes) for calculating data averages and standard deviations used to calculate Z-score.
* **detect_window_seconds** - Defines the time window (in seconds) for selecting data points to examine for anomalies. If polling on an interval, this can be set to match that interval to minimize duplicate detections.

### `calculate_z_score` Node

In this Node we set up a Common Table Expression (CTE) that calculates the average and standard deviation for each sensor (id) within the specified `stats_window_minutes`.
* It filters incoming data based on the specified time window `(NOW() - INTERVAL stats_window_minutes MINUTE)` and optionally filters by sensor_id if provided.
* avg(value) calculates the average value for each id within the window.
* stddevPop(value) calculates the population standard deviation for each id within the window.
* The results are grouped by id and stored in the stats table.

The main query:
*  calculates z-scores for incoming data and identifies potential anomalies.
* It joins the incoming_data table (i) with the stats table (s) on the id column.
* It filters the incoming data based on the specified detect_window_seconds `(NOW() - interval detect_window_seconds) SECOND`.
* For each data point, it calculates the Z-score using the formula: (i.value - stats.average) / stats.stddev.
* It selects various columns, including the timestamp, sensor ID, value, calculated z-score, average, standard deviation, and the defined z-score multiplier.
* Finally, it orders the results by timestamp in descending order, displaying the most recent data points first.


```sql
%
{% set _zscore_multiplier_default = 3 %}  # A multipler used to determine Z-score outliers. 
{% set _stats_window_minutes_default = 10 %}  # Statistical quartiles are based on this most recent window.
{% set _detect_window_seconds_default = 60 %} # This Pipe makes a copy every minute, so selecting events since last copy. 

WITH stats AS (
    SELECT id,
        avg(value) AS average,
        stddevPop(value) AS stddev
    FROM incoming_data
    WHERE timestamp BETWEEN NOW() - INTERVAL {{Int16(stats_window_minutes, _stats_window_minutes_default)}} MINUTE AND NOW()
       {% if defined(sensor_id) %}               
          AND id = {{ Int32(sensor_id)}}
       {% end %}  
    GROUP BY id  
)
SELECT i.timestamp, 
     i.id, 
     i.value, 
     (i.value - stats.average)/stats.stddev AS zscore,
     stats.average,
     stats.stddev,
     {{Float32(zscore_multiplier, _zscore_multiplier_default, description="Z-Score multipler to identify anomalies.")}} AS zscore_multiplier
FROM incoming_data i
JOIN stats s ON s.id = i.id
WHERE timestamp BETWEEN NOW() - interval {{Int16(detect_window_seconds, _detect_window_seconds_default)}} SECOND AND NOW()
ORDER BY timestamp DESC
```

* This query calculates real-time z-scores by using a sliding window approach for both statistical calculations and data selection.
* The zscore_multiplier provides a threshold for identifying potential anomalies. If the absolute value of the z-score is greater than or equal to the multiplier, the data point might be considered an anomaly.
* The query can be customized by adjusting the default values for windows, the z-score multiplier, and potential filtering based on sensor_id.


### `endpoint` Node

This query builds upon the previous calculate_z_score query, selecting and processing specific data points based on their z-scores. This query demonstrates applying 'high', 'low' or 'OK' labels depending on the Z-scores. 

This query:
* Takes the pre-calculated z-scores from the calculate_z_score table.
* Rounds the z-score, average, and standard deviation for better presentation.
* Uses the multiIf function to categorize data points as 'low', 'high', or 'ok' based on their z-score deviation from the average.
* Filters the results to only include data points with significant deviations (either positive or negative) exceeding the defined zscore_multiplier threshold.
* Orders the results by timestamp, highlighting the most recent potential anomalies.

```sql
%
SELECT timestamp,
   id,
   value,
   Round(zscore,2) AS zscore,
   multiIf(zscore < (-1 * zscore_multiplier), 'low', zscore > zscore_multiplier, 'high','ok') AS test,
   ROUND(average,2) AS average,
   ROUND(stddev,2) AS stddev,
   zscore_multiplier
FROM calculate_z_score
WHERE test = 'low' OR test = 'high' 
 AND zscore < -1 * zscore_multiplier OR zscore > zscore_multiplier 
ORDER by timestamp DESC
```
