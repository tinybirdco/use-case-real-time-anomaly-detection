
## Anomaly detection 

This project is a collection of things in support of demonstrating how Tinybird can be used to detect anomalies and support anomaly-detection systems. 

The main pieces of this project are:
* A **data generator** that emits time-series data with outliers and anomalies.
* A **Tinybird Data Project** with Pipes that implement different recipes to detect outliers and anomalies.
* A **Grafana dashboard** that displays the time-series data along with anomaly detection summaries. 

![Anomaly detection dashboard](./charts/dashboard-poc.png)


## Anomaly types
This project includes Tinybird Pipe 'recipes' that implement the following methods for detecting anomalies: 

* **Out-of-range**: Data that lies outside of a specified 'valid' range.
* **Rate-of-change**: Data with rates-of-change above a specified rate or slope.
* **Timeout**: Data that stops completely.
* Pattern changing. These methods develop data statistics to detect anomalies:
  * **Interquartile Range (IQR)**: Data outliers due to being outside of IQR lower and upper bounds.
  * **Z-score**: Data outliers due to its Z-Score.  

## Generating time-series data

For this project, a first step was building tools for generating time-series data with prescribed anomalies and outliers in it. These tools generate a time-series with the following features:
* *Steady-state* values with small random fluctuations.
* *Random and isolated outliers* that are outside of a "valid" range.  
* *Step-functions* where the data jumps upwards and downwards. Here the slope between points is an anomaly.
* Sensors that *stop reporting*.

Kicking off the project with a set of data generator tools. These tools generate single-value time-series data for a set of sensors. See the [the data-generator readme](./data-generator/readme.md) for more details.

## Data Project

The `anomaly-detection` Data Project includes two Data Sources and over a dozen Pipes. 

### /datasources
* incoming_data
* copy_log

### /pipes for anomaly detection
Rougly in the order of complexity, starting with the more simple: 
* timeout
* out_of_range
* rate_of_change
* iqr
* z_score

#### Copy Pipes

These Copy Pipes are based on the anomaly detection Pipes. Their Job is to test for anomalies across all sensors and write output to the `copy_log` Data Source. These Copy Pipes do the work of compiling their detections into a single place. 

These Copy Pipes are configured to run every few minutes. In that sense, the compiled log is not up-to-the-second fresh, but does provide a single Endpoint to monitor five types of anomalies across an entire set of sensors. 

These Copy Pipes do not support query parameters so some details are hardcoded in the SQL. For example, the `copy_out_of_range` Pipe hardcodes the minimum and maximum allowable thresholds, along with how far back the detection window should go. Here we are setting the minimum valid value to 200, the maximum to 2000, and the time window to the most recent 30 minutes. 

```sql
SELECT *, 200 AS min_value, 2000 AS max_value 
FROM incoming_data
WHERE (value < 200 OR value > 2000)
AND timestamp > NOW() - INTERVAL 30 MINUTE
```
Here we are adding `min_value` and `max_value` to the SELECT statement to pass them to a subsequent Node that records these values in a `note` column. 

#### Compiling detections into a single source  

The `monitor_logs` API Endpoint pulls from the `copy_log` Data Source that is fed by the Copy Pipes, which get triggered every few minutes. The endpoint returns a list of anomaly detections across the set of sensors for all the anomaly types.  

While this compilation is not based on up-to-the-second fresh data, this endpoint provides a single endpoint that covers the five different anomaly types with a up-to-the-minute results.  

`https://api.tinybird.co/v0/pipes/monitor_logs.json`

