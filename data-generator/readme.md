Building a proof-of-concept script for composing the time-series data. The thought is to have one set of tools for creating data sets that can be replayed, and another for generating a live data feed. 

With data set files, we will be able to curate datasets with anomaly artifacts that complements the story that drove the data design.  

Started with a script that generates and writes data set files. Now refactoring to generate a real-time time-series, using the same "data with anomalies" design, but instead posting the data to the Events API. 

## anomaly-dataset-to-file.py

Builds CSV files that look like this: 

```
Timestamp,sensor 1,sensor 2,sensor 3,sensor 4,sensor 5,sensor 6,sensor 7,sensor 8,sensor 9,sensor 10
2023-11-02 16:55:16.0,540,568,200,700,592,684,497,637,471,601
2023-11-02 16:55:17.0,539.98,568.25,199.94,699.64,592.9,684.34,497.98,636.49,470.87,600.71
2023-11-02 16:55:18.0,540.74,567.79,200.87,700.25,592.25,683.35,497.09,635.95,471.71,600.89
2023-11-02 16:55:19.0,540.59,568.05,200.99,700.14,591.71,682.7,497.49,635.01,471.38,600.44
2023-11-02 16:55:20.0,539.8,568.59,200.47,699.15,590.72,683.48,497.1,635.1,470.87,600.43
2023-11-02 16:55:21.0,540.71,569.56,200.18,699.91,590.83,683.9,496.76,635.55,470.6,600.94
2023-11-02 16:55:22.0,541.1,570.26,199.85,700.32,590.47,684.33,496.33,636.14,470.1,600.61
2023-11-02 16:55:23.0,541.52,570.17,200.21,700.87,590.73,683.94,496.4,635.36,470.85,600.13
2023-11-02 16:55:24.0,541.8,569.46,199.55,700.77,590.4,684.48,497.24,634.86,470.6,599.4
2023-11-02 16:55:25.0,541.52,569.08,199.14,699.79,591.34,684.65,496.25,634.55,471.46,598.65
2023-11-02 16:55:26.0,541.8,569.32,199.54,699.53,591.86,685.17,496.55,635.26,470.58,599.07
```

## anomaly-dataset-live.py

Posts each new report to the Events API. No longer using synthetic timestamps and now everything is Now(). 

If this POC evolves, these two script could share common "generate data with anomalies" code. 

### Trend types

Sensors can be seeded with a *trend* setting. 

#### No trend

![No trending](../charts/no-trend.png)

#### Trend up

![Trending up](../charts/trend-up.png)

#### Trend down

![Trending down](../charts/trend-down.png)
