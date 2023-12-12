## Anomaly Detection Pipes

* iqr - 
* out_of_range - 
* rate_of_change - 
* simple_z_score - 
* timeout - 

All support the `id` query parameter. 

## get_anomalies Pipe

Pulls from copy_log and supports these query parameters:

+ anomaly_type - String. Options: z-source, interquartile range, out-of-range, rate-of-change, timeout.
+ max_results - Integer. Defaults to 10. The maximum number of most recent anomalies to return per response.
+ sensor_id	- Integer. Single sensor of interest.
