# Real-time Anomaly detection 

This repository is a collection of content in support of demonstrating how Tinybird can be used to detect anomalies in real-time and support anomaly-detection systems. With this project, we aim to provide a practical guide for data engineers, analysts, and decision-makers interested in detecting anomalies in data ingested into Tinybird. 


## Introduction

Anomalies, or outliers, in data can often signify critical events, deviations from expected behavior, or infrastructure breakdowns. Detecting these anomalies in real-time enables you to take proactive measures, mitigate risks, and optimize operations. In this project we demonstrate how various types of anomalies can be detected and flagged in streaming data.

The project focuses on dectecting five types of anomalies:

* **Out-of-range**: Identifying data points that fall outside a specified valid range.
* **Rate-of-change**: Detecting abrupt changes or spikes in the rate of change of data.
* **Timeout**: Flagging data points that cease to arrive within a predefined time interval.
* **Interquartile Range (IQR)**: Using statistical methods to identify outliers based on the interquartile range.
* **Z-score**: Applying standard deviation-based analysis to identify anomalies in data distribution.

Each anomaly detection method is implemented as SQL queries within separate Tinybird Pipes and published as an API Endpoint. 

## Project resources

The main components of this project are:

* A **Tinybird Data Project** in the `tinybird` folder with Pipes that implement different recipes to detect outliers and anomalies. It also provides Data Source definitions, including their data schema and database details. 

* A **data generator** that emits time-series data with outliers and anomalies. With this script you can curate data with prescibed outliers and trends. The general frequency of anomalies can be *tuned* in a configuration file by setting initial values, expected rates-of-change, thresholds such as maximums and minimums, definitions of 'step' functions, and the precentage of out-of-bounds values. The velocity of data generation is also configurable. While developing these detection methods, a data rate of around ten events per second was used. See [HERE](./data-generator/readme.md) for more details. 

* A **Grafana dashboard** that displays the time-series data along with anomaly detection summaries. Its JSON description is [HERE](./dashboard/anomaly-detection.json).

![Anomaly detection dashboard](./charts/dashboard-poc.png)

## Endpoints for detecting anomalies

At the heart of this project are five Tinybird API Endpoints that individually implement different anomaly detection methods. By supporting a set of query parameters, these endpoints provide flexible ways to detect anomalies. 

* **Out-of-range**: https://api.tinybird.co/v0/pipes/out_of_range.json
* **Timeout**: https://api.tinybird.co/v0/pipes/timeout.json
* **Rate-of-change**: https://api.tinybird.co/v0/pipes/rate_of_change.json
* **Interquartile range**: https://api.tinybird.co/v0/pipes/iqr.json
* **Z-score**: https://api.tinybird.co/v0/pipes/z_score.json

Collectively, these endpoints support the following query parameters:

* **sensor_id** - All endpoints support the ability to select a single sensor of interest. If not used, results for all sensors are returned.

* **detection_window_seconds** - Defines the time window (in seconds) for selecting data points to examine for anomalies. When polling detection endpoints, this parameter can be set the polling interval. For example, if you check on an amomaly type every minute, setting this to 60 seconds will check all data that arrived since the last request.  

* **stats_window_minutes** - The Z-score and interquartile range (IQR) methods depend on the time window (in minutes) for calculating averages and standard deviations for Z-scores, and first and third quartiles used for calculating IQRs.

* **iqr_multiplier** - The multiplier of the IQR to set the range for testing for IQR anomalies.

* **zscore_threshold** - The threshold for determining Z-score outliers, with scores higher than this detected as anomalies. Compared with absolute value of Z-score.

* **max_slope** - Maximum slope, any events with a rate-of-change higher than this is flagged as an anomaly.

* **min_value** - Minimum threshold, readings less than this number will be detected as out-of-range anomalies.

* **max_value** - Maximum threshold, readings greater than this number will be detected as out-of-range anomalies.

* **seconds** - Instead of a detection time window, the timeout endpoint accepts this parameter. If a sensor has not reported in this number of seconds, it is considered 'timedout'. Defaults to 30 seconds.

## Anomaly detection methods

This repository includes a `/content` folder with descriptions of each anomaly detection method. Follow the links below to learn about the detection method, see example queries and Pipe definitions, and see detection examples: 

* **[Out-of-range](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/out-of-range.md)** - Compares data with a set of maximum and minimum values. This recipe works with individual data points, and uses the most simple queries.  
* **[Timeout](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/timeout.md)** - Finds the most recent report for each sensor and checks if it is within the 'timeout' window.  
* **[Rate-of-change](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/rate-of-change.md)** - Looks up the two most recent data points and determines the rate of change, or slope, and compares that to a maximum allowable slope.  
* **[Interquartile-range](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/interquartile-range.md)** - Generates a `IQR` range based on first and third quartiles and a multiplier and used to define an 'acceptable' range. 
* **[Z-score](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/z-score.md)** - Generates a `Z score` based on data averages and standard deviations, with all scores above a threshold identified as anomalies.  

The Interquartile-range and Z-score methods generate time-series statistics to identify *pattern* changes, rather than triggering on a single or pair of isolated data points.


## Getting started

This Tinybird project offers two designs with distinct sets of Pipes for implementing anomaly detection. 

### Individual endpoints or a common log

* **Individual endpoints** where checks for individual anomaly types are made separately with API requests. So, each anomaly type has its own API Endpoint. With these endpoints you can pick and choose the anomaly types you want to detect, and make requests as needed. Every endpoint, except for the `timeout` type, has a `detect_window_seconds` query parameter that enables you to adjust what data interval to check based on when you last made a request. With the `timeout` API Endpoint, you can specify a `seconds` query parameter and it returns any sensor that has not reported within that amount of time.

  Results from these requests are not logged or archived. This design has the advantage of having less latency when checking for real-time anomalies. When making requests,  anomalies are checked for and reported on within milliseconds. This design has the disadvantage of requiring five separate endpoints to be queried to monitor all anomaly types. 

* **Copy Pipes that write anomaly detection results to a common log**. With this model, each anomaly type has its own Copy Pipe which runs type-specific queries and generates detection results that are eventually written to a shared `copy_log` Data Source. Every minute, the Copy Pipes write their results to a `copy_log_duplicate` Data Source, since event duplicates are likely since the copy time intervals are designed to slightly overlap to help ensure no events are missed between copying intervals. To deduplicate the data, a 

  With a shared anomaly log, a single endpoint can provide a compilation of the five anomaly types. Since this design depends on Copy Pipes, which runs on a few-minute interval, it has the disadvantage of increased latency between when an anomaly is first detected and when it arrives in the `copy_log` Data Source. 

Note that detection events are first written to a `copy_log_duplicate` Data Source, then a Materialized View is used to deduplicate events into the `copy_log` Data Source. 

### Applying anomaly detection recipes to an imported Data Source

If you have an active Tinybird project that you would like to build these detection recipes on top of, one option is to create a new Workspace, import the project resources into that, update the reference schema as needed, and share Data Sources of interest with this new Workspace. As noted in the next section, you will likely need to update the field names 


### Setting up anomaly detection Pipes in your Workspace

* Creating Pipes in your Workspace.
  1) First, you need a Tinybird account. 
  2) Create a new Workspace or select an existing one to work with. Look up and copy your personal admin Auth Token associated with your email.  
  3) Clone this repository 
  4) Using the terminal:
      * Navigate to the /tinybird folder
      * Start up the Tinybird CLI and `tb auth` with your personal admin token.
      * Push the contents to Tinybird with `tb push`
* Update Node SQL queries to match your own schema. All of the anomaly detection recipes are based exclusivey on these three schema fields, where `id` is the unique identifier of your sensors, and `value` is the data value being tested for anomalies :

  * `id` Int16
  * `timestamp` DateTime
  * `value` Float32

Assuming your schema uses different names, you can either update the queries accordingly, or build a transformation Pipe to renames these using aliases. 



