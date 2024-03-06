
# Anomaly detection 

This project is a collection of content in support of demonstrating how Tinybird can be used to detect anomalies and support anomaly-detection systems. With this project, we aim to provide a practical guide for data engineers, analysts, and decision-makers interested in detecting anomalies in data ingested into Tinybird. 


## Introduction

Anomalies, or outliers, in data can often signify critical events, deviations from expected behavior, or potential issues that require immediate attention. Detecting these anomalies in real-time enables you to take proactive measures, mitigate risks, and optimize operations. 

In this project, we present a set of 'recipes' for detecting anomalies in real-time streaming data using SQL-based queries implemented in Tinybird Pipes. By leveraging Tinybird Pipes, we showcase how various types of anomalies can be detected and flagged in streaming data in support of timely decision-making.

The project focuses on five main types of anomalies:

* **Out-of-range**: Identifying data points that fall outside a specified valid range.
* **Rate-of-change**: Detecting abrupt changes or spikes in the rate of change of data.
* **Timeout**: Flagging data points that cease to arrive within a predefined time interval.
* **Interquartile Range (IQR)**: Using statistical methods to identify outliers based on the interquartile range.
* **Z-score**: Applying standard deviation-based analysis to identify anomalies in the data distribution.

Each anomaly detection method is implemented as SQL queries within separate Pipes. The project demonstrates how these SQL-based anomaly detection recipes can be integrated into real-world data pipelines to monitor and analyze streaming data streams continuously.


## Project resources

The main components of this project are:

* A **Tinybird Data Project** in the `tinybird` folder with Pipes that implement different recipes to detect outliers and anomalies. It also provides Data Source definitions, including their data schema and database details. 

* A **data generator** that emits time-series data with outliers and anomalies. With this script you can curate data with prescibed outliers and trends.  See [HERE](./data-generator/readme.md) for more details. 

* A **Grafana dashboard** that displays the time-series data along with anomaly detection summaries. 

![Anomaly detection dashboard](./charts/dashboard-poc.png)

This project includes Tinybird Pipe 'recipes' that implement the following methods for detecting anomalies: 

* **[Out-of-range](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/out-of-range.md)** - Compares data with a set maximum and minimum values. This recipe works with individual data points, and uses the most simple queries.  
* **[Timeout](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/timeout.md)** - Finds the most recent report for each sensor and checks if it is within the 'timeout' window.  
* **[Rate-of-change](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/rate-of-change.md)** - Looks up the two most recent data points and determines the rate of change, or slope, and compares that to a maximax allowable slope.  
* **[Interquartile-range](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/interquartile-range.md)** - Generates a `IQR` range based on first and fourth quartiles and a multipler and used to define an 'acceptable' range. 
* **[Z-score](https://github.com/tinybirdco/use-case-anomaly-detection/blob/main/content/z-score.md)** - Generates a `Z score` based on data averages and standard deviations, with all scores above a threshold identified as anomalies.  

The Interquartile-range and Z-score methods generate time-series statistics to identify *pattern* changes, rather than triggering on a single, isolated data point.


## Getting started

This Tinybird project offers two distinct sets of Pipes for implementing anomaly detection: 

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


## Generating time-series data

For this project, a first step was building tools for generating time-series data with prescribed anomalies and outliers in it. These tools generate a time-series with the following features:
* *Steady-state* values with small random fluctuations.
* *Random and isolated outliers* that are outside of a "valid" range.  
* *Step-functions* where the data jumps upwards and downwards. Here the slope between points is an anomaly.
* Sensors that *stop reporting*.

Kicking off the project with a set of data generator tools. These tools generate single-value time-series data for a set of sensors. See the [the data-generator readme](./data-generator/readme.md) for more details.

